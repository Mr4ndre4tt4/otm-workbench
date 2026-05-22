import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import {
  archiveAsset,
  createAsset,
  createAssetLink,
  downloadCurrentAssetVersion,
  uploadAssetVersion,
  useAssetClassifications,
  useAssetDetail,
  useAssetLinks,
  useAssets,
  useAssetVersions
} from '../../platform/hooks';
import type { AssetClassification, AssetFilters, AssetItem } from '../../platform/types';
import { PageHeader } from '../../app/shell';
import {
  Button,
  DetailList,
  FeedbackMessage,
  MetricGrid,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  OperationalPanel,
  SelectedObjectPanel,
  StatePanel
} from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function assetMeta(asset: AssetItem) {
  const scope = asset.module_id ? `${asset.scope_type} / ${asset.module_id}` : asset.scope_type;
  return [asset.asset_type, asset.category, scope];
}

const assetWorkflowStages = [
  { id: "library", title: "Library", status: "1" },
  { id: "create", title: "Create", status: "2" },
  { id: "version", title: "Version", status: "3" },
  { id: "link", title: "Link", status: "4" },
  { id: "lifecycle", title: "Lifecycle", status: "5" }
] as const;

type AssetWorkflowStage = (typeof assetWorkflowStages)[number]["id"];

const emptyAssetFilters: AssetFilters = {
  asset_type: "",
  category: "",
  status: "",
  tag: ""
};

function classificationItems(classifications: AssetClassification[] | undefined, fallback: string[]) {
  if (classifications?.length) {
    return classifications;
  }
  return fallback.map((code, index) => ({
    code,
    description: code,
    id: `${code}-${index}`,
    is_active: true,
    name: code,
    sort_order: index,
    system_protected: true,
    classification_type: "fallback"
  }));
}

export function AssetsLibraryView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const [assetFilters, setAssetFilters] = useState<AssetFilters>(emptyAssetFilters);
  const [draftAssetFilters, setDraftAssetFilters] = useState<AssetFilters>(emptyAssetFilters);
  const assets = useAssets(token, assetFilters);
  const classifications = useAssetClassifications(token);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<AssetWorkflowStage>("library");
  const [operationAsset, setOperationAsset] = useState<AssetItem | null>(null);
  const [selectedVersionFile, setSelectedVersionFile] = useState<File | null>(null);
  const [linkType, setLinkType] = useState("MODULE");
  const [linkTargetId, setLinkTargetId] = useState("integration_mapping");
  const [linkTargetLabel, setLinkTargetLabel] = useState("Integration Mapping Studio");
  const [operationMessage, setOperationMessage] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const assetItems = assets.data?.items ?? [];
  const effectiveAssetId = selectedAssetId ?? operationAsset?.id ?? assetItems[0]?.id ?? null;
  const assetDetail = useAssetDetail(token, effectiveAssetId);
  const assetVersions = useAssetVersions(token, effectiveAssetId);
  const assetLinks = useAssetLinks(token, effectiveAssetId);
  const selectedAsset = operationAsset?.id === effectiveAssetId ? operationAsset : assetDetail.data;
  const versionedCount = assetItems.filter((asset) => asset.current_version_id).length;
  const internalCount = assetItems.filter((asset) => asset.sensitivity === "INTERNAL").length;
  const isArchived = selectedAsset?.status === "ARCHIVED";
  const classificationGroups = classifications.data?.items ?? [];
  const assetTypeOptions = classificationItems(
    classificationGroups.find((group) => group.classification_type === "asset_type")?.items,
    ["SPEC", "TEMPLATE", "SAMPLE_PAYLOAD"]
  );
  const assetCategoryOptions = classificationItems(
    classificationGroups.find((group) => group.classification_type === "asset_category")?.items,
    ["INTEGRATION", "OTM_SETUP", "TESTING"]
  );
  const assetStatusOptions = classificationItems(
    classificationGroups.find((group) => group.classification_type === "asset_status")?.items,
    ["DRAFT", "ACTIVE", "ARCHIVED"]
  );
  const assetLinkTypeOptions = classificationItems(
    classificationGroups.find((group) => group.classification_type === "asset_link_type")?.items,
    ["MODULE", "MACRO_OBJECT", "OTM_TABLE", "ARTIFACT", "EVIDENCE"]
  );

  const refreshAssetState = async (assetId: string) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["modules", "assets", "assets"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "assets", "assets", assetId] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "assets", "assets", assetId, "versions"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "assets", "assets", assetId, "links"] })
    ]);
  };

  const runAction = async <T,>(action: () => Promise<T>, onSuccess: (result: T) => string) => {
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await action();
      setOperationMessage(onSuccess(result));
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Assets Library action failed.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateAsset = () => {
    void runAction(
      async () => {
        const created = await createAsset(token, {
          name: "Synthetic Mapping Spec",
          description: "Client-safe synthetic support asset.",
          asset_type: "SPEC",
          category: "INTEGRATION",
          visibility: "PROJECT",
          scope_type: "MODULE",
          sensitivity: "INTERNAL",
          module_id: "integration_mapping",
          macro_object_code: "ORDER_RELEASE",
          otm_table_name: "ORDER_RELEASE",
          tags: ["SYNTHETIC", "MVP0"]
        });
        setSelectedAssetId(created.id);
        setOperationAsset(created);
        await refreshAssetState(created.id);
        setActiveStage("version");
        return created;
      },
      (result) => `Asset ${result.name} created.`
    );
  };

  const handleUploadVersion = () => {
    if (!effectiveAssetId || !selectedVersionFile) return;
    void runAction(
      async () => {
        const version = await uploadAssetVersion(token, effectiveAssetId, selectedVersionFile);
        setOperationAsset((current) =>
          current?.id === effectiveAssetId ? { ...current, current_version_id: version.id } : current
        );
        setSelectedVersionFile(null);
        await refreshAssetState(effectiveAssetId);
        setActiveStage("link");
        return version;
      },
      (result) => `Asset version ${result.file_name} uploaded.`
    );
  };

  const handleCreateLink = () => {
    if (!effectiveAssetId) return;
    void runAction(
      async () => {
        const link = await createAssetLink(token, effectiveAssetId, {
          link_type: linkType,
          target_id: linkTargetId.trim(),
          target_label: linkTargetLabel.trim()
        });
        await refreshAssetState(effectiveAssetId);
        setActiveStage("lifecycle");
        return link;
      },
      (result) => `Asset link ${result.target_id} created.`
    );
  };

  const handleDownloadCurrentVersion = () => {
    if (!effectiveAssetId) return;
    void runAction(
      () => downloadCurrentAssetVersion(token, effectiveAssetId),
      (result) => `Download started: ${result.filename ?? "asset file"}.`
    );
  };

  const handleArchiveAsset = () => {
    if (!effectiveAssetId) return;
    void runAction(
      async () => {
        const archived = await archiveAsset(token, effectiveAssetId);
        setOperationAsset(archived);
        setSelectedVersionFile(null);
        await refreshAssetState(effectiveAssetId);
        return archived;
      },
      (result) => `Asset ${result.name} archived.`
    );
  };

  if (assets.isLoading) {
    return <StatePanel>Loading Assets Library...</StatePanel>;
  }

  if (assets.isError || !assets.data) {
    return <StatePanel tone="error">Assets Library is unavailable.</StatePanel>;
  }

  return (
    <>
      <PageHeader
        description="Shared library for templates, payloads, generated files, specs, and reusable implementation assets."
        label="Module workspace"
        title="Assets Library"
      />

      <MetricGrid
        ariaLabel="Assets Library metrics"
        items={[
          { key: "total", label: "Assets", status: booleanStatus(assets.data.total), value: assets.data.total },
          { key: "versioned", label: "Versioned", status: booleanStatus(versionedCount), value: versionedCount },
          { key: "internal", label: "Internal", status: booleanStatus(internalCount), value: internalCount },
          { key: "visible", label: "Visible rows", status: booleanStatus(assetItems.length), value: assetItems.length }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Assets Library workspace"
        side={
          <SelectedObjectPanel
            ariaLabel="Selected asset"
            emptyText="Select an asset to inspect backend-owned metadata."
            fields={
              selectedAsset
                ? [
                    { label: "Category", value: selectedAsset.category },
                    { label: "Sensitivity", value: selectedAsset.sensitivity },
                    { label: "Macro object", value: selectedAsset.macro_object_code ?? "None" },
                    { label: "OTM table", value: selectedAsset.otm_table_name ?? "None" }
                  ]
                : []
            }
            isLoading={assetDetail.isLoading && Boolean(effectiveAssetId)}
            loadingText="Loading selected asset..."
            status={selectedAsset?.status ?? "PENDING"}
            subtitle={selectedAsset?.asset_type}
            title={selectedAsset?.name}
          >
            {selectedAsset?.description ? <p className="empty-text">{selectedAsset.description}</p> : null}
            <DetailList
              ariaLabel="Selected asset versions"
              emptyText="No versions uploaded for this asset."
              items={(assetVersions.data?.items ?? []).map((version) => ({
                id: version.id,
                meta: [`v${version.version_number}`, version.content_type, `${version.size_bytes} bytes`],
                status: version.status,
                title: version.file_name
              }))}
            />
            <DetailList
              ariaLabel="Selected asset links"
              emptyText="No links created for this asset."
              items={(assetLinks.data?.items ?? []).map((link) => ({
                id: link.id,
                meta: [link.link_type, link.target_id],
                status: link.link_type,
                title: link.target_label || link.target_id
              }))}
            />
          </SelectedObjectPanel>
        }
        status={assetItems.length ? "ACTIVE" : "EMPTY"}
        title="Assets"
      >
        <div className="load-plan-workflow" aria-label="Assets Library workflow">
          {assetWorkflowStages.map((stage) => (
            <button
              aria-pressed={activeStage === stage.id}
              className={
                activeStage === stage.id
                  ? "load-plan-workflow-step load-plan-workflow-step-active"
                  : "load-plan-workflow-step"
              }
              key={stage.id}
              onClick={() => setActiveStage(stage.id)}
              type="button"
            >
              <span>{stage.status}</span>
              <strong>{stage.title}</strong>
            </button>
          ))}
        </div>

        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        {activeStage === "library" ? (
          <OperationalPanel
            ariaLabel="Assets list workflow"
            emptyText="No assets available for the current context."
            hasItems
            status={assetItems.length ? "ACTIVE" : "EMPTY"}
            title="Library"
          >
            <div className="master-data-action-bar">
              <label>
                Asset type filter
                <select
                  aria-label="Asset type filter"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, asset_type: event.target.value }))}
                  value={draftAssetFilters.asset_type ?? ""}
                >
                  <option value="">Any type</option>
                  {assetTypeOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset category filter
                <select
                  aria-label="Asset category filter"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, category: event.target.value }))}
                  value={draftAssetFilters.category ?? ""}
                >
                  <option value="">Any category</option>
                  {assetCategoryOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset status filter
                <select
                  aria-label="Asset status filter"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, status: event.target.value }))}
                  value={draftAssetFilters.status ?? ""}
                >
                  <option value="">Any status</option>
                  {assetStatusOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset tag filter
                <input
                  aria-label="Asset tag filter"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, tag: event.target.value }))}
                  value={draftAssetFilters.tag ?? ""}
                />
              </label>
              <Button
                disabled={isMutating}
                onClick={() => {
                  setAssetFilters(draftAssetFilters);
                  setSelectedAssetId(null);
                  setOperationAsset(null);
                }}
                variant="secondary"
              >
                Apply asset filters
              </Button>
            </div>
            <ModuleObjectList
              ariaLabel="Assets"
              emptyText="No assets available for the current context."
              items={assetItems.map((asset) => ({
                id: asset.id,
                meta: assetMeta(asset),
                status: asset.status,
                subtitle: asset.macro_object_code ?? asset.module_id ?? asset.scope_type,
                title: asset.name
              }))}
              onSelect={(assetId) => {
                setSelectedAssetId(assetId);
                setOperationAsset(null);
              }}
              selectedId={effectiveAssetId}
            />
          </OperationalPanel>
        ) : null}

        {activeStage === "create" ? (
          <OperationalPanel
            ariaLabel="Assets create workflow"
            emptyText="Create a governed support asset before adding file versions or links."
            hasItems
            status="READY"
            title="Create asset"
          >
            <div className="master-data-action-bar">
              <Button disabled={isMutating} onClick={handleCreateAsset} variant="primary">
                Create asset
              </Button>
            </div>
          </OperationalPanel>
        ) : null}

        {activeStage === "version" ? (
          <OperationalPanel
            ariaLabel="Assets version workflow"
            emptyText="Select an asset before uploading a version."
            hasItems
            status={isArchived ? "ARCHIVED" : selectedAsset?.current_version_id ? "VERSIONED" : "PENDING"}
            title="Version"
          >
            <div className="master-data-action-bar">
              <label>
                Asset version file
                <input
                  aria-label="Asset version file"
                  disabled={isArchived}
                  onChange={(event) => setSelectedVersionFile(event.target.files?.[0] ?? null)}
                  type="file"
                />
              </label>
              <Button
                disabled={isMutating || !effectiveAssetId || !selectedVersionFile || isArchived}
                onClick={handleUploadVersion}
                variant="primary"
              >
                Upload version
              </Button>
            </div>
          </OperationalPanel>
        ) : null}

        {activeStage === "link" ? (
          <OperationalPanel
            ariaLabel="Assets link workflow"
            emptyText="Select an active asset before linking it to another workbench object."
            hasItems
            status={isArchived ? "ARCHIVED" : "READY"}
            title="Link"
          >
            <div className="master-data-action-bar">
              <label>
                Asset link type
                <select aria-label="Asset link type" onChange={(event) => setLinkType(event.target.value)} value={linkType}>
                  {assetLinkTypeOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset link target id
                <input
                  aria-label="Asset link target id"
                  onChange={(event) => setLinkTargetId(event.target.value)}
                  value={linkTargetId}
                />
              </label>
              <label>
                Asset link target label
                <input
                  aria-label="Asset link target label"
                  onChange={(event) => setLinkTargetLabel(event.target.value)}
                  value={linkTargetLabel}
                />
              </label>
              <Button
                disabled={isMutating || !effectiveAssetId || isArchived || !linkTargetId.trim()}
                onClick={handleCreateLink}
                variant="primary"
              >
                Create link
              </Button>
            </div>
          </OperationalPanel>
        ) : null}

        {activeStage === "lifecycle" ? (
          <OperationalPanel
            ariaLabel="Assets lifecycle workflow"
            emptyText="Select an asset before downloading or archiving it."
            hasItems
            status={selectedAsset?.status ?? "PENDING"}
            title="Lifecycle"
          >
            <div className="master-data-action-bar">
              <Button
                disabled={isMutating || !effectiveAssetId || !selectedAsset?.current_version_id}
                onClick={handleDownloadCurrentVersion}
                variant="secondary"
              >
                Download current version
              </Button>
              <Button
                disabled={isMutating || !effectiveAssetId || isArchived}
                onClick={handleArchiveAsset}
                variant="primary"
              >
                Archive asset
              </Button>
            </div>
          </OperationalPanel>
        ) : null}
      </ModuleWorkspaceLayout>
    </>
  );
}
