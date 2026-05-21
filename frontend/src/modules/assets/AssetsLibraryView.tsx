import { AlertCircle } from 'lucide-react';
import { useState } from 'react';

import { useAssetDetail, useAssets, useAssetVersions } from '../../platform/hooks';
import type { AssetItem } from '../../platform/types';
import { PageHeader } from '../../app/shell';
import { DetailList, MetricGrid, ModuleObjectList, SelectedObjectPanel, StatusChip } from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function assetMeta(asset: AssetItem) {
  const scope = asset.module_id ? `${asset.scope_type} / ${asset.module_id}` : asset.scope_type;
  return [asset.asset_type, asset.category, scope];
}

export function AssetsLibraryView({ token }: { token: string }) {
  const assets = useAssets(token);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const assetItems = assets.data?.items ?? [];
  const effectiveAssetId = selectedAssetId ?? assetItems[0]?.id ?? null;
  const assetDetail = useAssetDetail(token, effectiveAssetId);
  const assetVersions = useAssetVersions(token, effectiveAssetId);
  const selectedAsset = assetDetail.data;
  const versionedCount = assetItems.filter((asset) => asset.current_version_id).length;
  const internalCount = assetItems.filter((asset) => asset.sensitivity === "INTERNAL").length;

  if (assets.isLoading) {
    return <section className="state-panel">Loading Assets Library...</section>;
  }

  if (assets.isError || !assets.data) {
    return (
      <section className="state-panel state-panel-error">
        <AlertCircle aria-hidden="true" />
        <span>Assets Library is unavailable.</span>
      </section>
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

      <section className="module-template" aria-label="Assets Library workspace">
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Assets</h2>
            <StatusChip status={assetItems.length ? "ACTIVE" : "EMPTY"} />
          </div>
          <ModuleObjectList
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
        </div>

        <SelectedObjectPanel
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
        </SelectedObjectPanel>
      </section>
    </>
  );
}
