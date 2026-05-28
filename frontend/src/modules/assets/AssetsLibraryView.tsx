import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

import {
  archiveAsset,
  createAsset,
  createAssetClassification,
  createAssetLink,
  downloadCurrentAssetVersion,
  updateAsset,
  updateAssetClassification,
  uploadAssetVersion,
  useAssetClassifications,
  useAssetDetail,
  useAssetLinks,
  useAssets,
  useCatalogMacroObjects,
  useCatalogTables,
  useEvidenceHub,
  useNavigation,
  useAssetVersions
} from '../../platform/hooks';
import type { AssetClassification, AssetFilters, AssetItem, EvidenceHubFilters } from '../../platform/types';
import { ApiError } from '../../platform/api';
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
  asset_id: "",
  asset_type: "",
  category: "",
  description: "",
  linked_target_type: "",
  macro_object_code: "",
  module_id: "",
  name: "",
  otm_table_name: "",
  scope_type: "",
  status: "",
  tag: ""
};

const defaultAssetSearchDraft: AssetFilters = {
  ...emptyAssetFilters,
  asset_id_operator: "contains",
  description_operator: "contains",
  linked_target_type_operator: "one_of",
  macro_object_code_operator: "contains",
  module_id_operator: "contains",
  name_operator: "contains",
  otm_table_name_operator: "contains",
  page_size: "50"
};

const textSearchOperators = [
  { label: "Contains", value: "contains" },
  { label: "Begins with", value: "begins_with" },
  { label: "One of", value: "one_of" },
  { label: "Not one of", value: "not_one_of" }
] as const;

const defaultAssetDraft = {
  asset_type: "SPEC",
  category: "INTEGRATION",
  description: "Client-safe synthetic support asset.",
  macro_object_code: "ORDER_RELEASE",
  module_id: "integration_mapping",
  name: "Synthetic Mapping Spec",
  otm_table_name: "ORDER_RELEASE",
  scope_type: "MODULE",
  sensitivity: "INTERNAL",
  tags: "SYNTHETIC,MVP0",
  visibility: "PROJECT"
};

const classificationTypeOptions = [
  { code: "asset_type", name: "Asset type", targetField: "asset_type" },
  { code: "asset_category", name: "Asset category", targetField: "category" },
  { code: "asset_visibility", name: "Asset visibility", targetField: "visibility" },
  { code: "asset_scope", name: "Asset scope", targetField: "scope_type" },
  { code: "asset_sensitivity", name: "Asset sensitivity", targetField: "sensitivity" },
  { code: "asset_link_type", name: "Asset link type", targetField: null }
] as const;

const defaultClassificationDraft = {
  classification_type: "asset_category",
  code: "PLAYBOOK",
  description: "Client-safe reusable implementation playbook.",
  name: "Playbook",
  sort_order: "90"
};

const emptyEvidenceTargetFilters: EvidenceHubFilters = {
  artifact_id: "",
  client_safe: true,
  evidence_type: "",
  source_module: "",
  status: ""
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

function assetDraftPayload(assetDraft: typeof defaultAssetDraft) {
  return {
    name: assetDraft.name.trim(),
    description: assetDraft.description.trim(),
    asset_type: assetDraft.asset_type,
    category: assetDraft.category,
    visibility: assetDraft.visibility,
    scope_type: assetDraft.scope_type,
    sensitivity: assetDraft.sensitivity,
    module_id: assetDraft.module_id.trim() || null,
    macro_object_code: assetDraft.macro_object_code.trim() || null,
    otm_table_name: assetDraft.otm_table_name.trim() || null,
    tags: assetDraft.tags
      .split(",")
      .map((tag) => tag.trim().toUpperCase())
      .filter(Boolean)
  };
}

function assetDraftFromAsset(asset: AssetItem) {
  return {
    asset_type: asset.asset_type,
    category: asset.category,
    description: asset.description,
    macro_object_code: asset.macro_object_code ?? "",
    module_id: asset.module_id ?? "",
    name: asset.name,
    otm_table_name: asset.otm_table_name ?? "",
    scope_type: asset.scope_type,
    sensitivity: asset.sensitivity,
    tags: asset.tags.join(","),
    visibility: asset.visibility
  };
}

function formatAssetsError(error: unknown) {
  if (error instanceof ApiError) {
    const allowedCodes = Array.isArray(error.details.allowed_codes)
      ? error.details.allowed_codes.filter((item): item is string => typeof item === "string")
      : [];
    const fieldName = typeof error.details.field_name === "string" ? error.details.field_name : "";
    const detailSuffix = allowedCodes.length
      ? ` Allowed ${fieldName || "values"}: ${allowedCodes.join(", ")}.`
      : "";
    return `${error.code}: ${error.message}${detailSuffix}`;
  }
  return error instanceof Error ? error.message : "Assets Library action failed.";
}

function cleanAssetSearchFilters(draft: AssetFilters, page = "1") {
  const filters: AssetFilters = {};
  const copyTrimmed = (key: keyof AssetFilters) => {
    const value = draft[key]?.trim();
    if (value) {
      filters[key] = value;
    }
  };
  const copyTextFilter = (valueKey: keyof AssetFilters, operatorKey: keyof AssetFilters) => {
    const value = draft[valueKey]?.trim();
    if (!value) return;
    filters[valueKey] = value;
    const operator = draft[operatorKey]?.trim();
    if (operator) {
      filters[operatorKey] = operator;
    }
  };

  copyTextFilter("asset_id", "asset_id_operator");
  copyTextFilter("name", "name_operator");
  copyTextFilter("description", "description_operator");
  copyTrimmed("asset_type");
  copyTrimmed("category");
  copyTrimmed("status");
  copyTrimmed("scope_type");
  copyTrimmed("tag");
  copyTextFilter("module_id", "module_id_operator");
  copyTextFilter("macro_object_code", "macro_object_code_operator");
  copyTextFilter("otm_table_name", "otm_table_name_operator");
  copyTextFilter("linked_target_type", "linked_target_type_operator");
  const pageSize = draft.page_size?.trim();
  if (pageSize && pageSize !== "50") {
    filters.page = page;
    filters.page_size = pageSize;
  }
  return filters;
}

type GuidedLinkTarget = {
  description: string;
  label: string;
  targetId: string;
  targetLabel: string;
};

function actionDisabled(asset: AssetItem | undefined, actionKey: string, fallbackDisabled: boolean) {
  const action = asset?.available_actions?.find((item) => item.key === actionKey);
  return action ? action.disabled : fallbackDisabled;
}

function assetLibraryRowActions(asset: AssetItem, onSelect: (assetId: string) => void) {
  const rowUploadDisabled = actionDisabled(asset, "asset.upload_version", asset.status === "ARCHIVED");
  const rowArchiveDisabled = actionDisabled(asset, "asset.archive", asset.status === "ARCHIVED");
  return (
    <div className="master-data-action-bar">
      <Button aria-label={`Select ${asset.name}`} onClick={() => onSelect(asset.id)} variant="secondary">
        Select
      </Button>
      <Link aria-label={`Open ${asset.name}`} className="button button-secondary" to={`/assets/${asset.id}`}>
        Open
      </Link>
      {rowUploadDisabled ? null : (
        <Link
          aria-label={`Upload version for ${asset.name}`}
          className="button button-secondary"
          to={`/assets/${asset.id}/versions/new`}
        >
          Upload version
        </Link>
      )}
      {rowArchiveDisabled ? null : (
        <Link aria-label={`Archive ${asset.name}`} className="button button-primary" to={`/assets/${asset.id}/archive`}>
          Archive
        </Link>
      )}
    </div>
  );
}

export function AssetsLibraryView({ token }: { token: string }) {
  const location = useLocation();
  const queryClient = useQueryClient();
  const directAssetEditMatch = /^\/assets\/([^/]+)\/edit$/.exec(location.pathname);
  const directAssetVersionsNewMatch = /^\/assets\/([^/]+)\/versions\/new$/.exec(location.pathname);
  const directAssetVersionsMatch = /^\/assets\/([^/]+)\/versions$/.exec(location.pathname);
  const directAssetLinksMatch = /^\/assets\/([^/]+)\/links$/.exec(location.pathname);
  const directAssetArchiveMatch = /^\/assets\/([^/]+)\/archive$/.exec(location.pathname);
  const directAssetNew = location.pathname === "/assets/new";
  const directClassificationsNew = location.pathname === "/assets/classifications/new";
  const directClassificationsEditMatch = /^\/assets\/classifications\/([^/]+)\/edit$/.exec(location.pathname);
  const directClassificationEditId = directClassificationsEditMatch?.[1] ?? null;
  const directAssetDetailMatch = /^\/assets\/([^/]+)$/.exec(location.pathname);
  const directAssetEditId = directAssetEditMatch?.[1] ?? null;
  const directAssetVersionsNewId = directAssetVersionsNewMatch?.[1] ?? null;
  const directAssetVersionsId = directAssetVersionsMatch?.[1] ?? null;
  const directAssetLinksId = directAssetLinksMatch?.[1] ?? null;
  const directAssetArchiveId = directAssetArchiveMatch?.[1] ?? null;
  const directAssetId =
    directAssetDetailMatch && !["library", "new", "classifications"].includes(directAssetDetailMatch[1])
      ? directAssetDetailMatch[1]
      : null;
  const directAssetRouteId =
    directAssetArchiveId ??
    directAssetLinksId ??
    directAssetVersionsNewId ??
    directAssetVersionsId ??
    directAssetEditId ??
    directAssetId;
  const [assetFilters, setAssetFilters] = useState<AssetFilters>(emptyAssetFilters);
  const [draftAssetFilters, setDraftAssetFilters] = useState<AssetFilters>(defaultAssetSearchDraft);
  const assets = useAssets(token, assetFilters);
  const classifications = useAssetClassifications(token);
  const navigation = useNavigation(token);
  const catalogMacroObjects = useCatalogMacroObjects(token);
  const [evidenceTargetFilters, setEvidenceTargetFilters] = useState<EvidenceHubFilters>(emptyEvidenceTargetFilters);
  const [draftEvidenceTargetFilters, setDraftEvidenceTargetFilters] =
    useState<EvidenceHubFilters>(emptyEvidenceTargetFilters);
  const evidenceHub = useEvidenceHub(token, evidenceTargetFilters);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<AssetWorkflowStage>("library");
  const [operationAsset, setOperationAsset] = useState<AssetItem | null>(null);
  const [selectedVersionFile, setSelectedVersionFile] = useState<File | null>(null);
  const [assetDraft, setAssetDraft] = useState(defaultAssetDraft);
  const [classificationDraft, setClassificationDraft] = useState(defaultClassificationDraft);
  const [classificationEditDraft, setClassificationEditDraft] = useState(defaultClassificationDraft);
  const [linkType, setLinkType] = useState("MODULE");
  const [linkTargetId, setLinkTargetId] = useState("integration_mapping");
  const [linkTargetLabel, setLinkTargetLabel] = useState("Integration Mapping Studio");
  const catalogTables = useCatalogTables(token, linkType === "OTM_TABLE" ? linkTargetId : "", 25);
  const [operationMessage, setOperationMessage] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const assetItems = assets.data?.items ?? [];
  const assetTotal = assets.data?.total ?? assetItems.length;
  const assetPage = (assets.data?.page ?? Number(assetFilters.page ?? "1")) || 1;
  const assetPageSize = (assets.data?.page_size ?? Number(assetFilters.page_size ?? "50")) || 50;
  const canGoPreviousAssetPage = assetPage > 1;
  const canGoNextAssetPage = assetPage * assetPageSize < assetTotal;
  const assetSelectionDisabled =
    directAssetNew || location.pathname === "/assets/classifications" || directClassificationsNew || Boolean(directClassificationEditId);
  const effectiveAssetId = assetSelectionDisabled
    ? null
    : selectedAssetId ?? directAssetRouteId ?? operationAsset?.id ?? assetItems[0]?.id ?? null;
  const assetDetail = useAssetDetail(token, effectiveAssetId);
  const assetVersions = useAssetVersions(token, effectiveAssetId);
  const assetLinks = useAssetLinks(token, effectiveAssetId);
  const selectedAsset = operationAsset?.id === effectiveAssetId ? operationAsset : assetDetail.data;
  const versionedCount = assetItems.filter((asset) => asset.current_version_id).length;
  const internalCount = assetItems.filter((asset) => asset.sensitivity === "INTERNAL").length;
  const isArchived = selectedAsset?.status === "ARCHIVED";
  const updateDisabled = actionDisabled(selectedAsset, "asset.update", isArchived);
  const uploadDisabled = actionDisabled(selectedAsset, "asset.upload_version", isArchived);
  const linkDisabled = actionDisabled(selectedAsset, "asset.create_link", isArchived);
  const downloadDisabled = actionDisabled(selectedAsset, "asset.download_current", !selectedAsset?.current_version_id);
  const archiveDisabled = actionDisabled(selectedAsset, "asset.archive", isArchived);
  const classificationGroups = classifications.data?.items ?? [];
  const flatClassifications = classificationGroups.flatMap((group) =>
    group.items.map((item) => ({ ...item, classification_type: item.classification_type ?? group.classification_type }))
  );
  const selectedClassification = flatClassifications.find((item) => item.id === directClassificationEditId);
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
  const assetVisibilityOptions = classificationItems(
    classificationGroups.find((group) => group.classification_type === "asset_visibility")?.items,
    ["PROJECT", "PROFILE", "MODULE"]
  );
  const assetScopeOptions = classificationItems(
    classificationGroups.find((group) => group.classification_type === "asset_scope")?.items,
    ["GLOBAL", "PROJECT", "MODULE"]
  );
  const assetSensitivityOptions = classificationItems(
    classificationGroups.find((group) => group.classification_type === "asset_sensitivity")?.items,
    ["PUBLIC", "INTERNAL", "SECRET"]
  );
  const guidedLinkTargets: GuidedLinkTarget[] =
    linkType === "MODULE"
      ? (navigation.data?.items ?? []).map((item) => ({
          description: item.description ?? item.path,
          label: item.label,
          targetId: item.id,
          targetLabel: item.label
        }))
      : linkType === "MACRO_OBJECT"
        ? (catalogMacroObjects.data?.items ?? []).map((item) => ({
            description: item.description,
            label: item.name,
            targetId: item.code,
            targetLabel: `${item.name} macro object`
          }))
        : linkType === "OTM_TABLE"
          ? (catalogTables.data?.items ?? []).map((item) => ({
              description: item.description,
              label: item.table_name,
              targetId: item.table_name,
              targetLabel: `${item.table_name} table`
            }))
          : linkType === "ARTIFACT"
            ? Array.from(
                new Map(
                  (evidenceHub.data?.items ?? [])
                    .filter((item) => item.artifact)
                    .map((item) => [
                      item.artifact!.id,
                      {
                        description: `${item.artifact!.source_module} / ${item.artifact!.artifact_type}`,
                        label: item.artifact!.file_name,
                        targetId: item.artifact!.id,
                        targetLabel: item.artifact!.file_name
                      }
                    ])
                ).values()
              )
            : linkType === "EVIDENCE"
              ? (evidenceHub.data?.items ?? []).map((item) => ({
                  description: `${item.source_module} / ${item.status}`,
                  label: item.evidence_type,
                  targetId: item.id,
                  targetLabel: `${item.evidence_type} evidence`
                }))
        : [];

  const handleGuidedLinkTargetChange = (targetId: string) => {
    const target = guidedLinkTargets.find((item) => item.targetId === targetId);
    if (!target) return;
    setLinkTargetId(target.targetId);
    setLinkTargetLabel(target.targetLabel);
  };

  const applyEvidenceTargetFilters = () => {
    setEvidenceTargetFilters({
      artifact_id: draftEvidenceTargetFilters.artifact_id?.trim() ?? "",
      client_safe: true,
      evidence_type: draftEvidenceTargetFilters.evidence_type?.trim() ?? "",
      source_module: draftEvidenceTargetFilters.source_module?.trim() ?? "",
      status: draftEvidenceTargetFilters.status?.trim() ?? ""
    });
    setLinkTargetId("");
    setLinkTargetLabel("");
  };

  const resetEvidenceTargetFilters = () => {
    setDraftEvidenceTargetFilters(emptyEvidenceTargetFilters);
    setEvidenceTargetFilters(emptyEvidenceTargetFilters);
    setLinkTargetId("");
    setLinkTargetLabel("");
  };

  const clearAssetWorkspaceState = () => {
    setOperationAsset(null);
    setSelectedVersionFile(null);
    setOperationMessage(null);
    setOperationError(null);
    setDraftEvidenceTargetFilters(emptyEvidenceTargetFilters);
    setEvidenceTargetFilters(emptyEvidenceTargetFilters);
    setLinkType("MODULE");
    setLinkTargetId("integration_mapping");
    setLinkTargetLabel("Integration Mapping Studio");
  };

  const handleSelectAsset = (assetId: string) => {
    if (assetId === effectiveAssetId) return;
    clearAssetWorkspaceState();
    setSelectedAssetId(assetId);
  };

  const resetAssetFilters = () => {
    setDraftAssetFilters(defaultAssetSearchDraft);
    setAssetFilters(emptyAssetFilters);
    setSelectedAssetId(null);
    clearAssetWorkspaceState();
  };

  const applyAssetSearch = () => {
    setAssetFilters(cleanAssetSearchFilters(draftAssetFilters));
    setSelectedAssetId(null);
    clearAssetWorkspaceState();
  };

  const moveAssetSearchPage = (nextPage: number) => {
    setAssetFilters((current) => ({
      ...current,
      page: String(Math.max(nextPage, 1)),
      page_size: draftAssetFilters.page_size?.trim() || current.page_size || "50"
    }));
    setSelectedAssetId(null);
    clearAssetWorkspaceState();
  };

  useEffect(() => {
    if (selectedAsset) {
      // Draft mirrors the backend-selected asset so updates never use stale row metadata.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setAssetDraft(assetDraftFromAsset(selectedAsset));
    }
  }, [selectedAsset]);

  useEffect(() => {
    if (selectedClassification) {
      setClassificationEditDraft({
        classification_type: selectedClassification.classification_type,
        code: selectedClassification.code,
        description: selectedClassification.description,
        name: selectedClassification.name,
        sort_order: String(selectedClassification.sort_order)
      });
    }
  }, [
    selectedClassification?.classification_type,
    selectedClassification?.code,
    selectedClassification?.description,
    selectedClassification?.id,
    selectedClassification?.name,
    selectedClassification?.sort_order
  ]);

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
      setOperationError(formatAssetsError(error));
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateAsset = () => {
    void runAction(
      async () => {
        const created = await createAsset(token, assetDraftPayload(assetDraft));
        setSelectedAssetId(created.id);
        setOperationAsset(created);
        await refreshAssetState(created.id);
        setActiveStage("version");
        return created;
      },
      (result) => `Asset ${result.name} created.`
    );
  };

  const handleCreateClassification = () => {
    void runAction(
      async () => {
        const created = await createAssetClassification(token, {
          classification_type: classificationDraft.classification_type,
          code: classificationDraft.code.trim(),
          name: classificationDraft.name.trim(),
          description: classificationDraft.description.trim(),
          sort_order: Number(classificationDraft.sort_order) || 0
        });
        await queryClient.invalidateQueries({ queryKey: ["modules", "assets", "classifications"] });
        const option = classificationTypeOptions.find((item) => item.code === created.classification_type);
        if (option?.targetField) {
          setAssetDraft((current) => ({ ...current, [option.targetField]: created.code }));
        }
        if (created.classification_type === "asset_link_type") {
          setLinkType(created.code);
        }
        return created;
      },
      (result) => `Classification ${result.code} created.`
    );
  };

  const handleUpdateClassification = () => {
    if (!directClassificationEditId || !selectedClassification || selectedClassification.system_protected) return;
    void runAction(
      async () => {
        const updated = await updateAssetClassification(token, directClassificationEditId, {
          name: classificationEditDraft.name.trim(),
          description: classificationEditDraft.description.trim(),
          sort_order: Number(classificationEditDraft.sort_order) || 0,
          is_active: selectedClassification.is_active
        });
        await queryClient.invalidateQueries({ queryKey: ["modules", "assets", "classifications"] });
        return updated;
      },
      (result) => `Classification ${result.code} saved.`
    );
  };

  const handleUpdateAsset = () => {
    if (!effectiveAssetId || updateDisabled) return;
    void runAction(
      async () => {
        const updated = await updateAsset(token, effectiveAssetId, assetDraftPayload(assetDraft));
        setSelectedAssetId(updated.id);
        setOperationAsset(updated);
        await refreshAssetState(updated.id);
        return updated;
      },
      (result) => `Asset ${result.name} updated.`
    );
  };

  const handleUploadVersion = () => {
    if (!effectiveAssetId || !selectedVersionFile) return;
    void runAction(
      async () => {
        const version = await uploadAssetVersion(token, effectiveAssetId, selectedVersionFile);
        setOperationAsset((current) => {
          if (current?.id !== effectiveAssetId) return current;
          const rest = { ...current };
          delete rest.available_actions;
          return { ...rest, current_version_id: version.id };
        });
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

  if (directAssetNew) {
    return (
      <>
        <PageHeader
          description="Create a governed reusable asset from backend-owned metadata classifications."
          label="Assets"
          title="Create asset"
        />

        <div className="master-data-action-bar">
          <Link className="button button-secondary" to="/assets/library">
            Back to Library
          </Link>
          <Link className="button button-secondary" to="/assets/library">
            Cancel
          </Link>
          <Link className="button button-secondary" to="/assets/classifications">
            Manage classifications
          </Link>
        </div>

        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        <ModuleWorkspaceLayout
          ariaLabel="Asset create workspace"
          side={
            <SelectedObjectPanel
              ariaLabel="Asset create guidance"
              emptyText="No create guidance is available."
              fields={[
                { label: "Type source", value: "Classification contract" },
                { label: "Category source", value: "Classification contract" },
                { label: "Validation", value: "Backend owned" },
                { label: "Next step", value: "Upload version" }
              ]}
              status="READY"
              subtitle="Route-level task"
              title="Asset metadata"
            >
              <p className="empty-text">
                Classification authoring is managed separately so asset creation stays focused on reusable file metadata.
              </p>
            </SelectedObjectPanel>
          }
          status="READY"
          title="Asset metadata"
        >
          <OperationalPanel
            ariaLabel="Asset create form"
            emptyText="Asset creation is unavailable."
            hasItems
            status="READY"
            title="Asset metadata"
          >
            <div className="module-form-grid">
              <label>
                Asset name
                <input
                  aria-label="Asset name"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, name: event.target.value }))}
                  value={assetDraft.name}
                />
              </label>
              <label>
                Asset description
                <input
                  aria-label="Asset description"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, description: event.target.value }))}
                  value={assetDraft.description}
                />
              </label>
              <label>
                Asset type
                <select
                  aria-label="Asset type"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, asset_type: event.target.value }))}
                  value={assetDraft.asset_type}
                >
                  {assetTypeOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset category
                <select
                  aria-label="Asset category"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, category: event.target.value }))}
                  value={assetDraft.category}
                >
                  {assetCategoryOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset visibility
                <select
                  aria-label="Asset visibility"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, visibility: event.target.value }))}
                  value={assetDraft.visibility}
                >
                  {assetVisibilityOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset scope
                <select
                  aria-label="Asset scope"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, scope_type: event.target.value }))}
                  value={assetDraft.scope_type}
                >
                  {assetScopeOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset sensitivity
                <select
                  aria-label="Asset sensitivity"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, sensitivity: event.target.value }))}
                  value={assetDraft.sensitivity}
                >
                  {assetSensitivityOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset module id
                <input
                  aria-label="Asset module id"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, module_id: event.target.value }))}
                  value={assetDraft.module_id}
                />
              </label>
              <label>
                Asset macro object
                <input
                  aria-label="Asset macro object"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, macro_object_code: event.target.value }))}
                  value={assetDraft.macro_object_code}
                />
              </label>
              <label>
                Asset OTM table
                <input
                  aria-label="Asset OTM table"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, otm_table_name: event.target.value }))}
                  value={assetDraft.otm_table_name}
                />
              </label>
              <label>
                Asset tags
                <input
                  aria-label="Asset tags"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, tags: event.target.value }))}
                  value={assetDraft.tags}
                />
              </label>
            </div>
            <div className="master-data-action-bar">
              <Button disabled={isMutating || !assetDraft.name.trim()} onClick={handleCreateAsset} variant="primary">
                Create asset
              </Button>
            </div>
          </OperationalPanel>
        </ModuleWorkspaceLayout>
      </>
    );
  }

  if (location.pathname === "/assets/classifications") {
    return (
      <>
        <PageHeader
          description="Backend-owned classification values for asset metadata and link targets."
          label="Assets"
          title="Asset classifications"
        />

        <div className="master-data-action-bar">
          <Link className="button button-secondary" to="/assets">
            Back to Assets
          </Link>
          <Link className="button button-primary" to="/assets/classifications/new">
            Create classification
          </Link>
          <Link className="button button-secondary" to="/assets/library">
            Open library
          </Link>
        </div>

        <ModuleWorkspaceLayout
          ariaLabel="Asset classifications workspace"
          side={
            <SelectedObjectPanel
              ariaLabel="Asset classifications summary"
              emptyText="No classification groups are available."
              fields={[
                { label: "Groups", value: String(classificationGroups.length) },
                { label: "Rows", value: String(flatClassifications.length) },
                {
                  label: "Editable",
                  value: String(flatClassifications.filter((classification) => !classification.system_protected).length)
                }
              ]}
              status={classificationGroups.length ? "READY" : "EMPTY"}
              subtitle="Backend contract"
              title="Classification registry"
            />
          }
          status={classificationGroups.length ? "READY" : "EMPTY"}
          title="Classification groups"
        >
          {classificationGroups.map((group) => (
            <OperationalPanel
              ariaLabel={`Asset classification group ${group.classification_type}`}
              emptyText="No classifications are registered for this group."
              hasItems={group.items.length > 0}
              key={group.classification_type}
              status={group.items.length ? "READY" : "EMPTY"}
              title={group.classification_type}
            >
              <DetailList
                ariaLabel={`Asset classification rows ${group.classification_type}`}
                emptyText="No classifications are registered for this group."
                items={group.items.map((classification) => ({
                  id: classification.id,
                  action: classification.system_protected ? (
                    <span className="status-chip">SYSTEM</span>
                  ) : (
                    <Link className="button button-secondary" to={`/assets/classifications/${classification.id}/edit`}>
                      Edit
                    </Link>
                  ),
                  meta: [classification.code, classification.description],
                  status: classification.is_active ? "ACTIVE" : "INACTIVE",
                  title: classification.name
                }))}
              />
            </OperationalPanel>
          ))}
        </ModuleWorkspaceLayout>
      </>
    );
  }

  if (directClassificationsNew) {
    return (
      <>
        <PageHeader
          description="Create reusable metadata values without mixing classification authoring into asset creation."
          label="Asset classifications"
          title="Create asset classification"
        />

        <div className="master-data-action-bar">
          <Link className="button button-secondary" to="/assets/classifications">
            Back to Classifications
          </Link>
          <Link className="button button-secondary" to="/assets/classifications">
            Cancel
          </Link>
        </div>

        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        <OperationalPanel
          ariaLabel="Asset classification create form"
          emptyText="Classification creation is unavailable."
          hasItems
          status="READY"
          title="Classification metadata"
        >
          <div className="assets-classification-authoring" aria-label="Asset classification authoring">
            <div className="module-form-grid">
              <label>
                Type
                <select
                  aria-label="Asset classification type"
                  onChange={(event) =>
                    setClassificationDraft((current) => ({ ...current, classification_type: event.target.value }))
                  }
                  value={classificationDraft.classification_type}
                >
                  {classificationTypeOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Code
                <input
                  aria-label="Asset classification code"
                  onChange={(event) =>
                    setClassificationDraft((current) => ({ ...current, code: event.target.value.toUpperCase() }))
                  }
                  value={classificationDraft.code}
                />
              </label>
              <label>
                Name
                <input
                  aria-label="Asset classification name"
                  onChange={(event) => setClassificationDraft((current) => ({ ...current, name: event.target.value }))}
                  value={classificationDraft.name}
                />
              </label>
              <label>
                Description
                <input
                  aria-label="Asset classification description"
                  onChange={(event) =>
                    setClassificationDraft((current) => ({ ...current, description: event.target.value }))
                  }
                  value={classificationDraft.description}
                />
              </label>
              <label>
                Sort order
                <input
                  aria-label="Asset classification sort order"
                  onChange={(event) =>
                    setClassificationDraft((current) => ({ ...current, sort_order: event.target.value }))
                  }
                  type="number"
                  value={classificationDraft.sort_order}
                />
              </label>
            </div>
            <Button
              disabled={isMutating || !classificationDraft.code.trim() || !classificationDraft.name.trim()}
              onClick={handleCreateClassification}
              variant="primary"
            >
              Create classification
            </Button>
          </div>
        </OperationalPanel>
      </>
    );
  }

  if (directClassificationEditId) {
    if (classifications.isLoading) {
      return <StatePanel>Loading asset classification...</StatePanel>;
    }

    if (!selectedClassification) {
      return (
        <>
          <PageHeader
            description="The requested classification is not available in the current backend contract."
            label="Asset classifications"
            title="Classification unavailable"
          />
          <StatePanel tone="error">
            Classification detail is unavailable. <Link to="/assets/classifications">Back to Classifications</Link>
          </StatePanel>
        </>
      );
    }

    return (
      <>
        <PageHeader
          description="Update editable classification labels while keeping classification type and code backend-owned."
          label="Asset classifications"
          title={`Edit ${selectedClassification.name}`}
        />

        <div className="master-data-action-bar">
          <Link className="button button-secondary" to="/assets/classifications">
            Back to Classifications
          </Link>
          <Link className="button button-secondary" to="/assets/classifications">
            Cancel
          </Link>
        </div>

        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        <ModuleWorkspaceLayout
          ariaLabel="Asset classification edit workspace"
          side={
            <SelectedObjectPanel
              ariaLabel="Asset classification edit reference"
              emptyText="No classification metadata is available."
              fields={[
                { label: "Type", value: selectedClassification.classification_type },
                { label: "Code", value: selectedClassification.code },
                { label: "System protected", value: selectedClassification.system_protected ? "Yes" : "No" },
                { label: "Status", value: selectedClassification.is_active ? "Active" : "Inactive" }
              ]}
              status={selectedClassification.system_protected ? "BLOCKED" : "READY"}
              subtitle={selectedClassification.classification_type}
              title={selectedClassification.code}
            />
          }
          status={selectedClassification.system_protected ? "BLOCKED" : "READY"}
          title="Classification metadata"
        >
          <OperationalPanel
            ariaLabel="Asset classification edit form"
            emptyText="Classification editing is unavailable."
            hasItems
            status={selectedClassification.system_protected ? "BLOCKED" : "READY"}
            title="Editable fields"
          >
            <div className="assets-classification-authoring" aria-label="Asset classification authoring">
              <div className="module-form-grid">
                <label>
                  Type
                  <input
                    aria-label="Asset classification type"
                    disabled
                    value={classificationEditDraft.classification_type}
                  />
                </label>
                <label>
                  Code
                  <input aria-label="Asset classification code" disabled value={classificationEditDraft.code} />
                </label>
                <label>
                  Name
                  <input
                    aria-label="Asset classification name"
                    disabled={selectedClassification.system_protected}
                    onChange={(event) =>
                      setClassificationEditDraft((current) => ({ ...current, name: event.target.value }))
                    }
                    value={classificationEditDraft.name}
                  />
                </label>
                <label>
                  Description
                  <input
                    aria-label="Asset classification description"
                    disabled={selectedClassification.system_protected}
                    onChange={(event) =>
                      setClassificationEditDraft((current) => ({ ...current, description: event.target.value }))
                    }
                    value={classificationEditDraft.description}
                  />
                </label>
                <label>
                  Sort order
                  <input
                    aria-label="Asset classification sort order"
                    disabled={selectedClassification.system_protected}
                    onChange={(event) =>
                      setClassificationEditDraft((current) => ({ ...current, sort_order: event.target.value }))
                    }
                    type="number"
                    value={classificationEditDraft.sort_order}
                  />
                </label>
              </div>
              <Button
                disabled={
                  isMutating ||
                  selectedClassification.system_protected ||
                  !classificationEditDraft.name.trim()
                }
                onClick={handleUpdateClassification}
                variant="primary"
              >
                Save classification
              </Button>
            </div>
          </OperationalPanel>
        </ModuleWorkspaceLayout>
      </>
    );
  }

  if (location.pathname === "/assets") {
    const missingVersionCount = assetItems.filter((asset) => !asset.current_version_id).length;
    const archivedCount = assetItems.filter((asset) => asset.status === "ARCHIVED").length;
    const recentAssets = assetItems.slice(0, 5);
    const assetsNeedingAttention = assetItems.filter((asset) => !asset.current_version_id || asset.status === "ARCHIVED").slice(0, 5);

    return (
      <>
        <PageHeader
          description="Governed reusable implementation files for templates, payload samples, specifications, diagrams, XML files, schema packs, and project playbooks."
          label="Module hub"
          title="Assets Library"
        />

        <MetricGrid
          ariaLabel="Assets Library hub metrics"
          items={[
            { key: "total", label: "Assets", status: booleanStatus(assets.data.total), value: assets.data.total },
            { key: "versioned", label: "Versioned", status: booleanStatus(versionedCount), value: versionedCount },
            {
              key: "missing-version",
              label: "Missing version",
              status: missingVersionCount ? "PENDING" : "READY",
              value: missingVersionCount
            },
            { key: "archived", label: "Archived", status: archivedCount ? "BLOCKED" : "READY", value: archivedCount },
            { key: "visible", label: "Visible rows", status: booleanStatus(assetItems.length), value: assetItems.length }
          ]}
        />

        <ModuleWorkspaceLayout
          ariaLabel="Assets Library hub"
          side={
            <OperationalPanel
              ariaLabel="Recommended next actions"
              emptyText="Use route-level entry points before changing asset lifecycle data."
              hasItems
              status="READY"
              title="Recommended next actions"
            >
              <div className="master-data-action-bar">
                <Link className="button button-primary" to="/assets/library">
                  Open library
                </Link>
                <Link className="button button-secondary" to="/assets/new">
                  Create asset
                </Link>
                <Link className="button button-secondary" to="/assets/classifications">
                  Manage classifications
                </Link>
              </div>
            </OperationalPanel>
          }
          status="READY"
          title="Library health"
        >
          <OperationalPanel
            ariaLabel="Recent assets"
            emptyText="No assets are available for the current context."
            hasItems={recentAssets.length > 0}
            status={recentAssets.length ? "READY" : "EMPTY"}
            title="Recent assets"
          >
            {recentAssets.length ? (
              <DetailList
                ariaLabel="Recent asset rows"
                emptyText="No assets are available for the current context."
                items={recentAssets.map((asset) => ({
                  id: asset.id,
                  action: (
                    <Link className="button button-secondary" to={`/assets/${asset.id}`}>
                      Open detail
                    </Link>
                  ),
                  meta: [asset.asset_type, asset.category, asset.scope_type],
                  status: asset.status,
                  title: asset.name
                }))}
              />
            ) : null}
          </OperationalPanel>

          <OperationalPanel
            ariaLabel="Assets needing attention"
            emptyText="No visible assets need version or lifecycle attention."
            hasItems={assetsNeedingAttention.length > 0}
            status={assetsNeedingAttention.length ? "PENDING" : "READY"}
            title="Assets needing attention"
          >
            {assetsNeedingAttention.length ? (
              <DetailList
                ariaLabel="Asset attention rows"
                emptyText="No visible assets need version or lifecycle attention."
                items={assetsNeedingAttention.map((asset) => ({
                  id: asset.id,
                  action: (
                    <Link className="button button-secondary" to={`/assets/${asset.id}`}>
                      Open detail
                    </Link>
                  ),
                  meta: [
                    asset.asset_type,
                    asset.category,
                    asset.current_version_id ? "Archived" : "Missing version"
                  ],
                  status: asset.status,
                  title: asset.name
                }))}
              />
            ) : null}
          </OperationalPanel>
        </ModuleWorkspaceLayout>
      </>
    );
  }

  if (directAssetRouteId) {
    if (assetDetail.isLoading && !selectedAsset) {
      return <StatePanel>Loading asset detail...</StatePanel>;
    }

    if (assetDetail.isError || !selectedAsset) {
      return (
        <>
          <PageHeader
            description="The requested asset is not available in the current project, environment, and domain scope."
            label="Asset detail"
            title="Asset unavailable"
          />
          <StatePanel tone="error">
            Asset detail is unavailable. <Link to="/assets/library">Back to Library</Link>
          </StatePanel>
        </>
      );
    }

    if (directAssetVersionsNewId) {
      return (
        <>
          <PageHeader
            description="Upload a new governed file version for this asset without mixing link management or lifecycle actions."
            label="Asset versions"
            title={`Upload version for ${selectedAsset.name}`}
          />

          <div className="master-data-action-bar">
            <Link className="button button-secondary" to={`/assets/${selectedAsset.id}`}>
              Back to Asset
            </Link>
            <Link className="button button-secondary" to={`/assets/${selectedAsset.id}/versions`}>
              Version history
            </Link>
            <Link className="button button-secondary" to="/assets/library">
              Back to Library
            </Link>
          </div>

          {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
          {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

          <ModuleWorkspaceLayout
            ariaLabel="Asset version upload workspace"
            side={
              <SelectedObjectPanel
                ariaLabel="Asset version upload reference"
                emptyText="No asset metadata is available."
                fields={[
                  { label: "Status", value: selectedAsset.status },
                  { label: "Current version", value: selectedAsset.current_version_id ?? "Missing" },
                  { label: "Type", value: selectedAsset.asset_type },
                  { label: "Sensitivity", value: selectedAsset.sensitivity }
                ]}
                status={uploadDisabled ? "BLOCKED" : selectedAsset.current_version_id ? "VERSIONED" : "PENDING"}
                subtitle={selectedAsset.category}
                title={selectedAsset.name}
              >
                <p className="empty-text">
                  Upload eligibility stays backend-owned. Archived or blocked assets cannot receive new versions.
                </p>
              </SelectedObjectPanel>
            }
            status={uploadDisabled ? "BLOCKED" : "READY"}
            title="Upload new version"
          >
            <OperationalPanel
              ariaLabel="Asset version upload form"
              emptyText="Version upload is unavailable."
              hasItems
              status={uploadDisabled ? "BLOCKED" : "READY"}
              title="File upload"
            >
              <div className="master-data-action-bar">
                <label>
                  Asset version file
                  <input
                    aria-label="Asset version file"
                    disabled={uploadDisabled}
                    onChange={(event) => setSelectedVersionFile(event.target.files?.[0] ?? null)}
                    type="file"
                  />
                </label>
                <Button
                  disabled={isMutating || !effectiveAssetId || !selectedVersionFile || uploadDisabled}
                  onClick={handleUploadVersion}
                  variant="primary"
                >
                  Upload version
                </Button>
              </div>
            </OperationalPanel>
          </ModuleWorkspaceLayout>
        </>
      );
    }

    if (directAssetVersionsId) {
      const versionItems = assetVersions.data?.items ?? [];
      return (
        <>
          <PageHeader
            description="Review governed asset version history and guarded current-version download state."
            label="Asset versions"
            title={`Versions for ${selectedAsset.name}`}
          />

          <div className="master-data-action-bar">
            <Link className="button button-secondary" to={`/assets/${selectedAsset.id}`}>
              Back to Asset
            </Link>
            <Link className="button button-secondary" to="/assets/library">
              Back to Library
            </Link>
            <Link className="button button-primary" to={`/assets/${selectedAsset.id}/versions/new`}>
              Upload new version
            </Link>
            <Button disabled={isMutating || !effectiveAssetId || downloadDisabled} onClick={handleDownloadCurrentVersion}>
              Download current version
            </Button>
          </div>

          {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
          {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

          <ModuleWorkspaceLayout
            ariaLabel="Asset versions workspace"
            side={
              <SelectedObjectPanel
                ariaLabel="Asset versions reference"
                emptyText="No asset metadata is available."
                fields={[
                  { label: "Status", value: selectedAsset.status },
                  { label: "Current version", value: selectedAsset.current_version_id ?? "Missing" },
                  { label: "Versions", value: String(versionItems.length) },
                  { label: "Download", value: downloadDisabled ? "Blocked" : "Ready" }
                ]}
                status={selectedAsset.current_version_id ? "ACTIVE" : "PENDING"}
                subtitle={selectedAsset.asset_type}
                title={selectedAsset.name}
              />
            }
            status={selectedAsset.current_version_id ? "ACTIVE" : "PENDING"}
            title="Version history"
          >
            <OperationalPanel
              ariaLabel="Asset versions history"
              emptyText="No versions uploaded for this asset."
              hasItems={versionItems.length > 0}
              status={selectedAsset.current_version_id ? "ACTIVE" : "PENDING"}
              title="Versions"
            >
              <DetailList
                ariaLabel="Asset versions rows"
                emptyText="No versions uploaded for this asset."
                items={versionItems.map((version) => ({
                  id: version.id,
                  meta: [
                    `v${version.version_number}`,
                    version.content_type,
                    `${version.size_bytes} bytes`,
                    version.uploaded_by ?? "Unknown uploader"
                  ],
                  status: version.status,
                  title: version.file_name
                }))}
              />
            </OperationalPanel>
          </ModuleWorkspaceLayout>
        </>
      );
    }

    if (directAssetLinksId) {
      const linkItems = assetLinks.data?.items ?? [];
      return (
        <>
          <PageHeader
            description="Create and review governed relationships from this asset to backend-owned workbench targets."
            label="Asset links"
            title={`Links for ${selectedAsset.name}`}
          />

          <div className="master-data-action-bar">
            <Link className="button button-secondary" to={`/assets/${selectedAsset.id}`}>
              Back to Asset
            </Link>
            <Link className="button button-secondary" to="/assets/library">
              Back to Library
            </Link>
          </div>

          {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
          {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

          <ModuleWorkspaceLayout
            ariaLabel="Asset links workspace"
            side={
              <SelectedObjectPanel
                ariaLabel="Asset links reference"
                emptyText="No asset metadata is available."
                fields={[
                  { label: "Status", value: selectedAsset.status },
                  { label: "Links", value: String(linkItems.length) },
                  { label: "Module", value: selectedAsset.module_id ?? "None" },
                  { label: "Sensitivity", value: selectedAsset.sensitivity }
                ]}
                status={linkDisabled ? "BLOCKED" : "READY"}
                subtitle={selectedAsset.asset_type}
                title={selectedAsset.name}
              >
                <p className="empty-text">
                  Artifact and evidence relationships stay client-safe through backend validation.
                </p>
              </SelectedObjectPanel>
            }
            status={linkDisabled ? "BLOCKED" : "READY"}
            title="Relationship editor"
          >
            <OperationalPanel
              ariaLabel="Asset link creation form"
              emptyText="Link creation is unavailable."
              hasItems
              status={linkDisabled ? "BLOCKED" : "READY"}
              title="Create link"
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
                {linkType === "ARTIFACT" || linkType === "EVIDENCE" ? (
                  <>
                    <label>
                      Evidence target source module filter
                      <input
                        aria-label="Evidence target source module filter"
                        onChange={(event) =>
                          setDraftEvidenceTargetFilters((current) => ({ ...current, source_module: event.target.value }))
                        }
                        value={draftEvidenceTargetFilters.source_module ?? ""}
                      />
                    </label>
                    <label>
                      Evidence target type filter
                      <input
                        aria-label="Evidence target type filter"
                        onChange={(event) =>
                          setDraftEvidenceTargetFilters((current) => ({ ...current, evidence_type: event.target.value }))
                        }
                        value={draftEvidenceTargetFilters.evidence_type ?? ""}
                      />
                    </label>
                    <label>
                      Evidence target status filter
                      <input
                        aria-label="Evidence target status filter"
                        onChange={(event) =>
                          setDraftEvidenceTargetFilters((current) => ({ ...current, status: event.target.value }))
                        }
                        value={draftEvidenceTargetFilters.status ?? ""}
                      />
                    </label>
                    <label>
                      Evidence target artifact id filter
                      <input
                        aria-label="Evidence target artifact id filter"
                        onChange={(event) =>
                          setDraftEvidenceTargetFilters((current) => ({ ...current, artifact_id: event.target.value }))
                        }
                        value={draftEvidenceTargetFilters.artifact_id ?? ""}
                      />
                    </label>
                    <Button disabled={isMutating} onClick={applyEvidenceTargetFilters} variant="secondary">
                      Apply evidence target filters
                    </Button>
                    <Button disabled={isMutating} onClick={resetEvidenceTargetFilters} variant="secondary">
                      Reset evidence target filters
                    </Button>
                  </>
                ) : null}
                {guidedLinkTargets.length ? (
                  <label>
                    Asset guided link target
                    <select
                      aria-label="Asset guided link target"
                      onChange={(event) => handleGuidedLinkTargetChange(event.target.value)}
                      value={guidedLinkTargets.some((item) => item.targetId === linkTargetId) ? linkTargetId : ""}
                    >
                      <option value="">Select backend-owned target</option>
                      {guidedLinkTargets.map((item) => (
                        <option key={item.targetId} value={item.targetId}>
                          {item.label}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}
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
                  disabled={isMutating || !effectiveAssetId || linkDisabled || !linkTargetId.trim()}
                  onClick={handleCreateLink}
                  variant="primary"
                >
                  Create link
                </Button>
              </div>
            </OperationalPanel>

            <OperationalPanel
              ariaLabel="Asset links"
              emptyText="No links created for this asset."
              hasItems={linkItems.length > 0}
              status={linkItems.length ? "ACTIVE" : "PENDING"}
              title="Linked targets"
            >
              <DetailList
                ariaLabel="Asset links rows"
                emptyText="No links created for this asset."
                items={linkItems.map((link) => ({
                  id: link.id,
                  meta: [link.link_type, link.target_id, link.created_by ?? "Unknown creator"],
                  status: "ACTIVE",
                  title: link.target_label
                }))}
              />
            </OperationalPanel>
          </ModuleWorkspaceLayout>
        </>
      );
    }

    if (directAssetArchiveId) {
      const versionItems = assetVersions.data?.items ?? [];
      const linkItems = assetLinks.data?.items ?? [];
      const linkedTargetSummary = `${linkItems.length} linked target${linkItems.length === 1 ? "" : "s"}`;
      const currentVersion = versionItems.find((version) => version.id === selectedAsset.current_version_id) ?? versionItems[0];
      return (
        <>
          <PageHeader
            description="Review lifecycle impact before archiving this governed reusable asset."
            label="Asset lifecycle"
            title={`Archive ${selectedAsset.name}`}
          />

          <div className="master-data-action-bar">
            <Link className="button button-secondary" to={`/assets/${selectedAsset.id}`}>
              Back to Asset
            </Link>
            <Link className="button button-secondary" to="/assets/library">
              Back to Library
            </Link>
            <Link className="button button-secondary" to={`/assets/${selectedAsset.id}`}>
              Cancel
            </Link>
          </div>

          {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
          {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

          <ModuleWorkspaceLayout
            ariaLabel="Asset archive workspace"
            side={
              <SelectedObjectPanel
                ariaLabel="Asset archive reference"
                emptyText="No asset metadata is available."
                fields={[
                  { label: "Status", value: selectedAsset.status },
                  { label: "Current version", value: selectedAsset.current_version_id ?? "Missing" },
                  { label: "Versions", value: String(versionItems.length) },
                  { label: "Links", value: linkedTargetSummary }
                ]}
                status={archiveDisabled ? "BLOCKED" : "READY"}
                subtitle={selectedAsset.asset_type}
                title={selectedAsset.name}
              >
                <p className="empty-text">
                  Archive eligibility is backend-owned. Archived assets block metadata updates, version uploads, and new links.
                </p>
              </SelectedObjectPanel>
            }
            status={archiveDisabled ? "BLOCKED" : "READY"}
            title="Archive review"
          >
            <OperationalPanel
              ariaLabel="Asset archive impact"
              emptyText="Archive impact is unavailable."
              hasItems
              status={archiveDisabled ? "BLOCKED" : "READY"}
              title="Impact summary"
            >
              <DetailList
                ariaLabel="Asset archive impact rows"
                items={[
                  {
                    id: "status",
                    meta: [selectedAsset.visibility, selectedAsset.sensitivity],
                    status: selectedAsset.status,
                    title: selectedAsset.status
                  },
                  {
                    id: "version",
                    meta: [
                      selectedAsset.current_version_id ?? "Missing current version id",
                      versionItems.length ? `${versionItems.length} version rows` : "No uploaded versions"
                    ],
                    status: selectedAsset.current_version_id ? "ACTIVE" : "PENDING",
                    title: currentVersion?.file_name ?? selectedAsset.current_version_id ?? "Missing current version"
                  },
                  {
                    id: "links",
                    meta: [linkItems.map((link) => link.target_label).join(", ") || "No linked targets"],
                    status: linkItems.length ? "ACTIVE" : "PENDING",
                    title: linkedTargetSummary
                  }
                ]}
              />
              <div className="master-data-action-bar">
                <Button
                  disabled={isMutating || !effectiveAssetId || archiveDisabled}
                  onClick={handleArchiveAsset}
                  variant="primary"
                >
                  Archive asset
                </Button>
              </div>
            </OperationalPanel>
          </ModuleWorkspaceLayout>
        </>
      );
    }

    if (directAssetEditId) {
      return (
        <>
          <PageHeader
            description="Edit governed asset metadata without mixing version upload, link management, or lifecycle actions."
            label="Asset metadata"
            title={`Edit ${selectedAsset.name}`}
          />

          <div className="master-data-action-bar">
            <Link className="button button-secondary" to={`/assets/${selectedAsset.id}`}>
              Back to Asset
            </Link>
            <Link className="button button-secondary" to="/assets/library">
              Back to Library
            </Link>
          </div>

          {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
          {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

          <ModuleWorkspaceLayout
            ariaLabel="Asset metadata edit workspace"
            side={
              <SelectedObjectPanel
                ariaLabel="Asset edit reference"
                emptyText="No asset metadata is available."
                fields={[
                  { label: "Status", value: selectedAsset.status },
                  { label: "Current version", value: selectedAsset.current_version_id ?? "Missing" },
                  { label: "Created by", value: selectedAsset.created_by ?? "Unknown" },
                  { label: "Updated", value: selectedAsset.updated_at ?? "Not updated" }
                ]}
                status={updateDisabled ? "BLOCKED" : selectedAsset.status}
                subtitle={selectedAsset.asset_type}
                title={selectedAsset.name}
              >
                <p className="empty-text">
                  Metadata changes are validated by backend classifications, Catalog Core, and the Data Dictionary.
                </p>
              </SelectedObjectPanel>
            }
            status={updateDisabled ? "BLOCKED" : "READY"}
            title="Edit metadata"
          >
            <OperationalPanel
              ariaLabel="Asset metadata edit form"
              emptyText="Asset metadata is unavailable."
              hasItems
              status={updateDisabled ? "BLOCKED" : "READY"}
              title="Metadata"
            >
              <div className="master-data-action-bar">
                <label>
                  Asset name
                  <input
                    aria-label="Asset name"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, name: event.target.value }))}
                    value={assetDraft.name}
                  />
                </label>
                <label>
                  Asset description
                  <input
                    aria-label="Asset description"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, description: event.target.value }))}
                    value={assetDraft.description}
                  />
                </label>
                <label>
                  Asset type
                  <select
                    aria-label="Asset type"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, asset_type: event.target.value }))}
                    value={assetDraft.asset_type}
                  >
                    {assetTypeOptions.map((item) => (
                      <option key={item.code} value={item.code}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Asset category
                  <select
                    aria-label="Asset category"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, category: event.target.value }))}
                    value={assetDraft.category}
                  >
                    {assetCategoryOptions.map((item) => (
                      <option key={item.code} value={item.code}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Asset visibility
                  <select
                    aria-label="Asset visibility"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, visibility: event.target.value }))}
                    value={assetDraft.visibility}
                  >
                    {assetVisibilityOptions.map((item) => (
                      <option key={item.code} value={item.code}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Asset scope
                  <select
                    aria-label="Asset scope"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, scope_type: event.target.value }))}
                    value={assetDraft.scope_type}
                  >
                    {assetScopeOptions.map((item) => (
                      <option key={item.code} value={item.code}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Asset sensitivity
                  <select
                    aria-label="Asset sensitivity"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, sensitivity: event.target.value }))}
                    value={assetDraft.sensitivity}
                  >
                    {assetSensitivityOptions.map((item) => (
                      <option key={item.code} value={item.code}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Asset module id
                  <input
                    aria-label="Asset module id"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, module_id: event.target.value }))}
                    value={assetDraft.module_id}
                  />
                </label>
                <label>
                  Asset macro object
                  <input
                    aria-label="Asset macro object"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, macro_object_code: event.target.value }))}
                    value={assetDraft.macro_object_code}
                  />
                </label>
                <label>
                  Asset OTM table
                  <input
                    aria-label="Asset OTM table"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, otm_table_name: event.target.value }))}
                    value={assetDraft.otm_table_name}
                  />
                </label>
                <label>
                  Asset tags
                  <input
                    aria-label="Asset tags"
                    disabled={updateDisabled}
                    onChange={(event) => setAssetDraft((current) => ({ ...current, tags: event.target.value }))}
                    value={assetDraft.tags}
                  />
                </label>
                <Button
                  disabled={isMutating || !effectiveAssetId || updateDisabled || !assetDraft.name.trim()}
                  onClick={handleUpdateAsset}
                  variant="primary"
                >
                  Save metadata
                </Button>
              </div>
            </OperationalPanel>
          </ModuleWorkspaceLayout>
        </>
      );
    }

    const detailFields = [
      { label: "Type", value: selectedAsset.asset_type },
      { label: "Category", value: selectedAsset.category },
      { label: "Visibility", value: selectedAsset.visibility },
      { label: "Scope", value: selectedAsset.scope_type },
      { label: "Sensitivity", value: selectedAsset.sensitivity },
      { label: "Module", value: selectedAsset.module_id ?? "None" },
      { label: "Macro object", value: selectedAsset.macro_object_code ?? "None" },
      { label: "OTM table", value: selectedAsset.otm_table_name ?? "None" },
      { label: "Current version", value: selectedAsset.current_version_id ?? "Missing" }
    ];

    return (
      <>
        <PageHeader
          description="Inspect governed reusable asset metadata, version history, links, and lifecycle state for the active scope."
          label="Asset detail"
          title={selectedAsset.name}
        />

        <div className="master-data-action-bar">
          <Link className="button button-secondary" to="/assets">
            Back to Assets
          </Link>
          <Link className="button button-secondary" to="/assets/library">
            Back to Library
          </Link>
          <Link className="button button-secondary" to={`/assets/${selectedAsset.id}/edit`}>
            Edit metadata
          </Link>
          <Link className="button button-secondary" to={`/assets/${selectedAsset.id}/versions/new`}>
            Upload version
          </Link>
          <Link className="button button-secondary" to={`/assets/${selectedAsset.id}/versions`}>
            View versions
          </Link>
          <Link className="button button-secondary" to={`/assets/${selectedAsset.id}/links`}>
            Manage links
          </Link>
          <Button disabled={isMutating || !effectiveAssetId || downloadDisabled} onClick={handleDownloadCurrentVersion}>
            Download current version
          </Button>
          <Link className="button button-secondary" to={`/assets/${selectedAsset.id}/archive`}>
            Archive asset
          </Link>
        </div>

        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        <ModuleWorkspaceLayout
          ariaLabel="Asset detail workspace"
          side={
            <SelectedObjectPanel
              ariaLabel="Asset detail metadata"
              emptyText="No asset metadata is available."
              fields={detailFields}
              status={selectedAsset.status}
              subtitle={selectedAsset.asset_type}
              title={selectedAsset.name}
            >
              <p className="empty-text">{selectedAsset.description}</p>
              {selectedAsset.tags.length ? (
                <p className="empty-text">Tags: {selectedAsset.tags.join(", ")}</p>
              ) : null}
            </SelectedObjectPanel>
          }
          status={selectedAsset.status}
          title="Asset detail"
        >
          <OperationalPanel
            ariaLabel="Asset detail versions"
            emptyText="No versions uploaded for this asset."
            hasItems={(assetVersions.data?.items ?? []).length > 0}
            status={selectedAsset.current_version_id ? "ACTIVE" : "PENDING"}
            title="Version history"
          >
            <DetailList
              ariaLabel="Asset detail version rows"
              emptyText="No versions uploaded for this asset."
              items={(assetVersions.data?.items ?? []).map((version) => ({
                id: version.id,
                meta: [`v${version.version_number}`, version.content_type, `${version.size_bytes} bytes`],
                status: version.status,
                title: version.file_name
              }))}
            />
          </OperationalPanel>

          <OperationalPanel
            ariaLabel="Asset detail links"
            emptyText="No links created for this asset."
            hasItems={(assetLinks.data?.items ?? []).length > 0}
            status={(assetLinks.data?.items ?? []).length ? "ACTIVE" : "PENDING"}
            title="Linked workbench objects"
          >
            <DetailList
              ariaLabel="Asset detail link rows"
              emptyText="No links created for this asset."
              items={(assetLinks.data?.items ?? []).map((link) => ({
                id: link.id,
                meta: [link.link_type, link.target_id],
                status: link.link_type,
                title: link.target_label || link.target_id
              }))}
            />
          </OperationalPanel>

          <OperationalPanel
            ariaLabel="Asset detail lifecycle"
            emptyText="Lifecycle state is owned by the backend asset contract."
            hasItems
            status={selectedAsset.status}
            title="Lifecycle"
          >
            <DetailList
              ariaLabel="Asset lifecycle actions"
              items={[
                {
                  id: "status",
                  meta: [selectedAsset.visibility, selectedAsset.sensitivity],
                  status: selectedAsset.status,
                  title: "Current lifecycle state"
                },
                {
                  id: "download",
                  meta: [selectedAsset.current_version_id ? "Version available" : "No current version"],
                  status: downloadDisabled ? "BLOCKED" : "READY",
                  title: "Current-version download"
                },
                {
                  id: "archive",
                  meta: [archiveDisabled ? "Action blocked" : "Action available"],
                  status: archiveDisabled ? "BLOCKED" : "READY",
                  title: "Archive review"
                }
              ]}
            />
          </OperationalPanel>
        </ModuleWorkspaceLayout>
      </>
    );
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
                Asset name search
                <input
                  aria-label="Asset name search"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, name: event.target.value }))}
                  value={draftAssetFilters.name ?? ""}
                />
              </label>
              <label>
                Asset name operator
                <select
                  aria-label="Asset name operator"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, name_operator: event.target.value }))}
                  value={draftAssetFilters.name_operator ?? "contains"}
                >
                  {textSearchOperators.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset description search
                <input
                  aria-label="Asset description search"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, description: event.target.value }))}
                  value={draftAssetFilters.description ?? ""}
                />
              </label>
              <label>
                Asset description operator
                <select
                  aria-label="Asset description operator"
                  onChange={(event) =>
                    setDraftAssetFilters((current) => ({ ...current, description_operator: event.target.value }))
                  }
                  value={draftAssetFilters.description_operator ?? "contains"}
                >
                  {textSearchOperators.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
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
              <label>
                Asset scope filter
                <select
                  aria-label="Asset scope filter"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, scope_type: event.target.value }))}
                  value={draftAssetFilters.scope_type ?? ""}
                >
                  <option value="">Any scope</option>
                  {assetScopeOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset module filter
                <input
                  aria-label="Asset module filter"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, module_id: event.target.value }))}
                  value={draftAssetFilters.module_id ?? ""}
                />
              </label>
              <label>
                Asset module operator
                <select
                  aria-label="Asset module operator"
                  onChange={(event) =>
                    setDraftAssetFilters((current) => ({ ...current, module_id_operator: event.target.value }))
                  }
                  value={draftAssetFilters.module_id_operator ?? "contains"}
                >
                  {textSearchOperators.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset macro object filter
                <input
                  aria-label="Asset macro object filter"
                  onChange={(event) =>
                    setDraftAssetFilters((current) => ({ ...current, macro_object_code: event.target.value }))
                  }
                  value={draftAssetFilters.macro_object_code ?? ""}
                />
              </label>
              <label>
                Asset macro object operator
                <select
                  aria-label="Asset macro object operator"
                  onChange={(event) =>
                    setDraftAssetFilters((current) => ({ ...current, macro_object_code_operator: event.target.value }))
                  }
                  value={draftAssetFilters.macro_object_code_operator ?? "contains"}
                >
                  {textSearchOperators.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset OTM table filter
                <input
                  aria-label="Asset OTM table filter"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, otm_table_name: event.target.value }))}
                  value={draftAssetFilters.otm_table_name ?? ""}
                />
              </label>
              <label>
                Asset OTM table operator
                <select
                  aria-label="Asset OTM table operator"
                  onChange={(event) =>
                    setDraftAssetFilters((current) => ({ ...current, otm_table_name_operator: event.target.value }))
                  }
                  value={draftAssetFilters.otm_table_name_operator ?? "contains"}
                >
                  {textSearchOperators.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset linked target type filter
                <select
                  aria-label="Asset linked target type filter"
                  onChange={(event) =>
                    setDraftAssetFilters((current) => ({ ...current, linked_target_type: event.target.value }))
                  }
                  value={draftAssetFilters.linked_target_type ?? ""}
                >
                  <option value="">Any linked target</option>
                  {assetLinkTypeOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset linked target type operator
                <select
                  aria-label="Asset linked target type operator"
                  onChange={(event) =>
                    setDraftAssetFilters((current) => ({ ...current, linked_target_type_operator: event.target.value }))
                  }
                  value={draftAssetFilters.linked_target_type_operator ?? "one_of"}
                >
                  <option value="one_of">One of</option>
                  <option value="not_one_of">Not one of</option>
                </select>
              </label>
              <label>
                Asset page size
                <select
                  aria-label="Asset page size"
                  onChange={(event) => setDraftAssetFilters((current) => ({ ...current, page_size: event.target.value }))}
                  value={draftAssetFilters.page_size ?? "50"}
                >
                  <option value="12">12</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                </select>
              </label>
              <Button
                disabled={isMutating}
                onClick={applyAssetSearch}
                variant="secondary"
              >
                Apply search
              </Button>
              <Button disabled={isMutating} onClick={resetAssetFilters} variant="secondary">
                Reset search
              </Button>
            </div>
            <div className="master-data-action-bar" aria-label="Asset search pagination">
              <span>{`Showing ${assetItems.length} of ${assetTotal} assets`}</span>
              <Button
                disabled={isMutating || !canGoPreviousAssetPage}
                onClick={() => moveAssetSearchPage(assetPage - 1)}
                variant="secondary"
              >
                Previous assets page
              </Button>
              <span>{`Page ${assetPage}`}</span>
              <Button
                disabled={isMutating || !canGoNextAssetPage}
                onClick={() => moveAssetSearchPage(assetPage + 1)}
                variant="secondary"
              >
                Next assets page
              </Button>
            </div>
            <DetailList
              ariaLabel="Assets"
              emptyText="No assets available for the current context."
              items={assetItems.map((asset) => ({
                action: assetLibraryRowActions(asset, handleSelectAsset),
                id: asset.id,
                meta: assetMeta(asset),
                status: asset.status,
                title: asset.name
              }))}
              maxVisibleItems={12}
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
              <label>
                Asset name
                <input
                  aria-label="Asset name"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, name: event.target.value }))}
                  value={assetDraft.name}
                />
              </label>
              <label>
                Asset description
                <input
                  aria-label="Asset description"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, description: event.target.value }))}
                  value={assetDraft.description}
                />
              </label>
              <label>
                Asset type
                <select
                  aria-label="Asset type"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, asset_type: event.target.value }))}
                  value={assetDraft.asset_type}
                >
                  {assetTypeOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset category
                <select
                  aria-label="Asset category"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, category: event.target.value }))}
                  value={assetDraft.category}
                >
                  {assetCategoryOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset visibility
                <select
                  aria-label="Asset visibility"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, visibility: event.target.value }))}
                  value={assetDraft.visibility}
                >
                  {assetVisibilityOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset scope
                <select
                  aria-label="Asset scope"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, scope_type: event.target.value }))}
                  value={assetDraft.scope_type}
                >
                  {assetScopeOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset sensitivity
                <select
                  aria-label="Asset sensitivity"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, sensitivity: event.target.value }))}
                  value={assetDraft.sensitivity}
                >
                  {assetSensitivityOptions.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Asset module id
                <input
                  aria-label="Asset module id"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, module_id: event.target.value }))}
                  value={assetDraft.module_id}
                />
              </label>
              <label>
                Asset macro object
                <input
                  aria-label="Asset macro object"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, macro_object_code: event.target.value }))}
                  value={assetDraft.macro_object_code}
                />
              </label>
              <label>
                Asset OTM table
                <input
                  aria-label="Asset OTM table"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, otm_table_name: event.target.value }))}
                  value={assetDraft.otm_table_name}
                />
              </label>
              <label>
                Asset tags
                <input
                  aria-label="Asset tags"
                  onChange={(event) => setAssetDraft((current) => ({ ...current, tags: event.target.value }))}
                  value={assetDraft.tags}
                />
              </label>
              <Button disabled={isMutating || !assetDraft.name.trim()} onClick={handleCreateAsset} variant="primary">
                Create asset
              </Button>
              <Button
                disabled={isMutating || !effectiveAssetId || updateDisabled || !assetDraft.name.trim()}
                onClick={handleUpdateAsset}
                variant="secondary"
              >
                Update asset
              </Button>
            </div>
          </OperationalPanel>
        ) : null}

        {activeStage === "version" ? (
          <OperationalPanel
            ariaLabel="Assets version workflow"
            emptyText="Select an asset before uploading a version."
            hasItems
            status={uploadDisabled ? "BLOCKED" : selectedAsset?.current_version_id ? "VERSIONED" : "PENDING"}
            title="Version"
          >
            <div className="master-data-action-bar">
              <label>
                Asset version file
                <input
                  aria-label="Asset version file"
                  disabled={uploadDisabled}
                  onChange={(event) => setSelectedVersionFile(event.target.files?.[0] ?? null)}
                  type="file"
                />
              </label>
              <Button
                disabled={isMutating || !effectiveAssetId || !selectedVersionFile || uploadDisabled}
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
            status={linkDisabled ? "BLOCKED" : "READY"}
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
              {linkType === "ARTIFACT" || linkType === "EVIDENCE" ? (
                <>
                  <label>
                    Evidence target source module filter
                    <input
                      aria-label="Evidence target source module filter"
                      onChange={(event) =>
                        setDraftEvidenceTargetFilters((current) => ({ ...current, source_module: event.target.value }))
                      }
                      value={draftEvidenceTargetFilters.source_module ?? ""}
                    />
                  </label>
                  <label>
                    Evidence target type filter
                    <input
                      aria-label="Evidence target type filter"
                      onChange={(event) =>
                        setDraftEvidenceTargetFilters((current) => ({ ...current, evidence_type: event.target.value }))
                      }
                      value={draftEvidenceTargetFilters.evidence_type ?? ""}
                    />
                  </label>
                  <label>
                    Evidence target status filter
                    <input
                      aria-label="Evidence target status filter"
                      onChange={(event) =>
                        setDraftEvidenceTargetFilters((current) => ({ ...current, status: event.target.value }))
                      }
                      value={draftEvidenceTargetFilters.status ?? ""}
                    />
                  </label>
                  <label>
                    Evidence target artifact id filter
                    <input
                      aria-label="Evidence target artifact id filter"
                      onChange={(event) =>
                        setDraftEvidenceTargetFilters((current) => ({ ...current, artifact_id: event.target.value }))
                      }
                      value={draftEvidenceTargetFilters.artifact_id ?? ""}
                    />
                  </label>
                  <Button disabled={isMutating} onClick={applyEvidenceTargetFilters} variant="secondary">
                    Apply evidence target filters
                  </Button>
                  <Button disabled={isMutating} onClick={resetEvidenceTargetFilters} variant="secondary">
                    Reset evidence target filters
                  </Button>
                </>
              ) : null}
              {guidedLinkTargets.length ? (
                <label>
                  Asset guided link target
                  <select
                    aria-label="Asset guided link target"
                    onChange={(event) => handleGuidedLinkTargetChange(event.target.value)}
                    value={guidedLinkTargets.some((item) => item.targetId === linkTargetId) ? linkTargetId : ""}
                  >
                    <option value="">Select backend-owned target</option>
                    {guidedLinkTargets.map((item) => (
                      <option key={item.targetId} value={item.targetId}>
                        {item.label}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
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
                disabled={isMutating || !effectiveAssetId || linkDisabled || !linkTargetId.trim()}
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
                disabled={isMutating || !effectiveAssetId || downloadDisabled}
                onClick={handleDownloadCurrentVersion}
                variant="secondary"
              >
                Download current version
              </Button>
              <Button
                disabled={isMutating || !effectiveAssetId || archiveDisabled}
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
