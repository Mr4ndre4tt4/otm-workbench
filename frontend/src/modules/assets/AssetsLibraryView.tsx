import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import {
  archiveAsset,
  createAsset,
  createAssetLink,
  downloadCurrentAssetVersion,
  uploadAssetVersion,
  useAssetDetail,
  useAssetLinks,
  useAssets,
  useAssetVersions
} from '../../platform/hooks';
import type { AssetItem } from '../../platform/types';
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

export function AssetsLibraryView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const assets = useAssets(token);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [operationAsset, setOperationAsset] = useState<AssetItem | null>(null);
  const [selectedVersionFile, setSelectedVersionFile] = useState<File | null>(null);
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
        await refreshAssetState(effectiveAssetId);
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
          link_type: "MODULE",
          target_id: "integration_mapping",
          target_label: "Integration Mapping Studio"
        });
        await refreshAssetState(effectiveAssetId);
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
            <div className="master-data-action-bar">
              <Button disabled={isMutating || !effectiveAssetId || !selectedAsset?.current_version_id} onClick={handleDownloadCurrentVersion} variant="secondary">
                Download current version
              </Button>
              <Button disabled={isMutating || !effectiveAssetId || selectedAsset?.status === "ARCHIVED"} onClick={handleArchiveAsset} variant="secondary">
                Archive asset
              </Button>
            </div>
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
        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        <OperationalPanel
          ariaLabel="Assets authoring workflow"
          emptyText="Create an asset before uploading versions or links."
          hasItems
          status={selectedAsset?.status ?? "READY"}
          title="Asset workflow"
        >
          <div className="master-data-action-bar">
            <Button disabled={isMutating} onClick={handleCreateAsset} variant="primary">
              Create asset
            </Button>
            <label>
              Asset version file
              <input
                aria-label="Asset version file"
                onChange={(event) => setSelectedVersionFile(event.target.files?.[0] ?? null)}
                type="file"
              />
            </label>
            <Button disabled={isMutating || !effectiveAssetId || !selectedVersionFile} onClick={handleUploadVersion} variant="secondary">
              Upload version
            </Button>
            <Button disabled={isMutating || !effectiveAssetId} onClick={handleCreateLink} variant="secondary">
              Create link
            </Button>
          </div>
        </OperationalPanel>

        <OperationalPanel
          ariaLabel="Assets list workflow"
          emptyText="No assets available for the current context."
          hasItems={Boolean(assetItems.length)}
          status={assetItems.length ? "ACTIVE" : "EMPTY"}
          title="Assets"
        >
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
            onSelect={setSelectedAssetId}
            selectedId={effectiveAssetId}
          />
        </OperationalPanel>
      </ModuleWorkspaceLayout>
    </>
  );
}
