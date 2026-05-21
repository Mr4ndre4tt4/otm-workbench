import { useState } from 'react';

import { useEvidenceDetail, useEvidenceHub } from '../../platform/hooks';
import type { EvidenceItem } from '../../platform/types';
import { PageHeader } from '../../app/shell';
import { DetailList, MetricGrid, ModuleObjectList, SelectedObjectPanel, StatePanel, StatusChip } from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function evidenceMeta(evidence: EvidenceItem) {
  return [
    evidence.source_module,
    evidence.artifact ? evidence.artifact.file_name : "No artifact",
    evidence.client_safe ? "Client safe" : "Internal"
  ];
}

export function EvidenceHubView({ token }: { token: string }) {
  const evidence = useEvidenceHub(token);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const evidenceItems = evidence.data?.items ?? [];
  const effectiveEvidenceId = selectedEvidenceId ?? evidenceItems[0]?.id ?? null;
  const evidenceDetail = useEvidenceDetail(token, effectiveEvidenceId);
  const selectedEvidence = evidenceDetail.data;
  const artifactCount = evidenceItems.filter((item) => item.artifact).length;
  const manifestCount = evidenceItems.filter((item) => item.manifest).length;

  if (evidence.isLoading) {
    return <StatePanel>Loading Evidence Hub...</StatePanel>;
  }

  if (evidence.isError || !evidence.data) {
    return <StatePanel tone="error">Evidence Hub is unavailable.</StatePanel>;
  }

  return (
    <>
      <PageHeader
        description="Client-safe evidence, manifests, artifacts, and implementation audit trail across modules."
        label="Module workspace"
        title="Evidence Hub"
      />

      <MetricGrid
        ariaLabel="Evidence Hub metrics"
        items={[
          { key: "total", label: "Evidence", status: booleanStatus(evidence.data.total), value: evidence.data.total },
          { key: "artifacts", label: "Artifacts", status: booleanStatus(artifactCount), value: artifactCount },
          { key: "manifests", label: "Manifests", status: booleanStatus(manifestCount), value: manifestCount },
          { key: "client_safe", label: "Client safe", status: booleanStatus(evidenceItems.length), value: evidenceItems.length }
        ]}
      />

      <section className="module-template" aria-label="Evidence Hub workspace">
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Evidence</h2>
            <StatusChip status={evidenceItems.length ? "ACTIVE" : "EMPTY"} />
          </div>
          <ModuleObjectList
            emptyText="No client-safe evidence available for the current context."
            items={evidenceItems.map((item) => ({
              id: item.id,
              meta: evidenceMeta(item),
              status: item.status,
              subtitle: item.source_module,
              title: item.evidence_type
            }))}
            onSelect={setSelectedEvidenceId}
            selectedId={effectiveEvidenceId}
          />
        </div>

        <SelectedObjectPanel
          emptyText="Select evidence to inspect backend-owned metadata."
          fields={
            selectedEvidence
              ? [
                  { label: "Source module", value: selectedEvidence.source_module },
                  { label: "Sensitivity", value: selectedEvidence.sensitivity_level },
                  { label: "Artifact", value: selectedEvidence.artifact?.file_name ?? "None" },
                  { label: "Manifest", value: selectedEvidence.manifest?.manifest_type ?? "None" }
                ]
              : []
          }
          isLoading={evidenceDetail.isLoading && Boolean(effectiveEvidenceId)}
          loadingText="Loading selected evidence..."
          status={selectedEvidence?.status ?? "PENDING"}
          subtitle={selectedEvidence?.source_module}
          title={selectedEvidence?.evidence_type}
        >
          <DetailList
            ariaLabel="Selected evidence references"
            emptyText="No artifact or manifest references for this evidence."
            items={[
              ...(selectedEvidence?.artifact
                ? [
                    {
                      id: selectedEvidence.artifact.id,
                      meta: [
                        selectedEvidence.artifact.artifact_type,
                        selectedEvidence.artifact.content_type,
                        `${selectedEvidence.artifact.size_bytes} bytes`
                      ],
                      status: selectedEvidence.artifact.sensitivity_level,
                      title: selectedEvidence.artifact.file_name
                    }
                  ]
                : []),
              ...(selectedEvidence?.manifest
                ? [
                    {
                      id: selectedEvidence.manifest.id,
                      meta: [
                        selectedEvidence.manifest.source_module,
                        selectedEvidence.manifest.schema_version ?? "No schema version"
                      ],
                      status: selectedEvidence.manifest.status,
                      title: selectedEvidence.manifest.manifest_type ?? "Manifest"
                    }
                  ]
                : [])
            ]}
          />
        </SelectedObjectPanel>
      </section>
    </>
  );
}
