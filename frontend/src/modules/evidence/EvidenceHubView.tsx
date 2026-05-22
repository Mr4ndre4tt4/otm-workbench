import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { PageHeader } from "../../app/shell";
import {
  createEvidenceArchivePackage,
  downloadEvidenceArtifact,
  useEvidenceDetail,
  useEvidenceHub
} from "../../platform/hooks";
import type { EvidenceArchivePackageResponse, EvidenceHubFilters, EvidenceItem } from "../../platform/types";
import {
  Button,
  DetailList,
  FeedbackMessage,
  MetricGrid,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  SelectedObjectPanel,
  StatePanel
} from "../../ui/components";
import { booleanStatus } from "../moduleStatus";

function evidenceMeta(evidence: EvidenceItem) {
  return [
    evidence.source_module,
    evidence.artifact ? evidence.artifact.file_name : "No artifact",
    evidence.client_safe ? "Client safe" : "Internal"
  ];
}

const workflowSteps = [
  { id: "find", title: "Find" },
  { id: "inspect", title: "Inspect" },
  { id: "download", title: "Download" },
  { id: "archive", title: "Archive" }
];

const emptyFilters = {
  artifact_id: "",
  evidence_type: "",
  manifest_id: "",
  project_id: "",
  sensitivity_level: "",
  source_module: "",
  status: ""
};

function normalizeFilters(filters: typeof emptyFilters): EvidenceHubFilters {
  return Object.fromEntries(Object.entries(filters).filter(([, value]) => value.trim() !== ""));
}

export function EvidenceHubView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const [draftFilters, setDraftFilters] = useState(emptyFilters);
  const [appliedFilters, setAppliedFilters] = useState<EvidenceHubFilters>({});
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [operationMessage, setOperationMessage] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const [archivePackage, setArchivePackage] = useState<EvidenceArchivePackageResponse | null>(null);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const evidence = useEvidenceHub(token, appliedFilters);
  const evidenceItems = evidence.data?.items ?? [];
  const effectiveEvidenceId = selectedEvidenceId ?? evidenceItems[0]?.id ?? null;
  const evidenceDetail = useEvidenceDetail(token, effectiveEvidenceId);
  const selectedEvidence = evidenceDetail.data;
  const artifactCount = evidenceItems.filter((item) => item.artifact).length;
  const manifestCount = evidenceItems.filter((item) => item.manifest).length;
  const activeStep = selectedEvidence?.artifact ? "download" : selectedEvidence ? "inspect" : "find";

  const updateDraftFilter = (key: keyof typeof emptyFilters, value: string) => {
    setDraftFilters((current) => ({ ...current, [key]: value }));
  };

  const handleApplyFilters = () => {
    setAppliedFilters(normalizeFilters(draftFilters));
    setSelectedEvidenceId(null);
    setArchivePackage(null);
    setOperationError(null);
    setOperationMessage("Evidence filters applied.");
  };

  const handleClearFilters = () => {
    setDraftFilters(emptyFilters);
    setAppliedFilters({});
    setSelectedEvidenceId(null);
    setArchivePackage(null);
    setOperationError(null);
    setOperationMessage("Evidence filters cleared.");
  };

  const handleDownloadArtifact = async () => {
    if (!selectedEvidence?.artifact) {
      setOperationError("Select evidence with a linked artifact before downloading.");
      return;
    }
    setOperationError(null);
    setOperationMessage(null);
    setDownloadingArtifactId(selectedEvidence.artifact.id);
    try {
      const result = await downloadEvidenceArtifact(token, selectedEvidence.artifact.id);
      const objectUrl = URL.createObjectURL(result.blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = result.filename ?? selectedEvidence.artifact.file_name;
      anchor.click();
      URL.revokeObjectURL(objectUrl);
      setOperationMessage(`Artifact ${anchor.download} downloaded through Evidence Hub.`);
    } catch {
      setOperationError("Could not download the selected artifact.");
    } finally {
      setDownloadingArtifactId(null);
    }
  };

  const handleCreateArchive = async () => {
    setOperationError(null);
    setOperationMessage(null);
    setIsMutating(true);
    try {
      const archive = await createEvidenceArchivePackage(token, normalizeFilters(draftFilters));
      setArchivePackage(archive);
      setSelectedEvidenceId(archive.evidence_id);
      await queryClient.invalidateQueries({ queryKey: ["evidence-hub", "evidence"] });
      setOperationMessage(`Archive package ${archive.file_name} created.`);
    } catch {
      setOperationError("Could not create an archive package for the current filters.");
    } finally {
      setIsMutating(false);
    }
  };

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

      <ModuleWorkspaceLayout
        ariaLabel="Evidence Hub workspace"
        side={
          <SelectedObjectPanel
            actions={
              selectedEvidence ? (
                <div className="action-bar">
                  <Button
                    disabled={!selectedEvidence.artifact || downloadingArtifactId === selectedEvidence.artifact?.id}
                    onClick={() => void handleDownloadArtifact()}
                    variant="primary"
                  >
                    {downloadingArtifactId === selectedEvidence.artifact?.id ? "Downloading..." : "Download artifact"}
                  </Button>
                  <Button disabled={isMutating} onClick={() => void handleCreateArchive()}>
                    {isMutating ? "Creating archive..." : "Create archive"}
                  </Button>
                </div>
              ) : null
            }
            ariaLabel="Selected evidence"
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
            {archivePackage ? (
              <DetailList
                ariaLabel="Latest archive package"
                items={[
                  {
                    id: archivePackage.archive_id,
                    meta: [
                      archivePackage.artifact_id,
                      `${archivePackage.summary.evidence_count} evidence`,
                      `${archivePackage.size_bytes} bytes`
                    ],
                    status: "CREATED",
                    title: archivePackage.file_name
                  }
                ]}
              />
            ) : null}
          </SelectedObjectPanel>
        }
        status={evidenceItems.length ? "ACTIVE" : "EMPTY"}
        title="Evidence workspace"
      >
        <div className="evidence-workflow" aria-label="Evidence Hub workflow">
          {workflowSteps.map((step, index) => (
            <div
              className={
                step.id === activeStep ? "evidence-workflow-step evidence-workflow-step-active" : "evidence-workflow-step"
              }
              key={step.id}
            >
              <span>{index + 1}</span>
              <strong>{step.title}</strong>
            </div>
          ))}
        </div>

        <div className="evidence-filter-bar" aria-label="Evidence filters">
          <label>
            Source module
            <input
              onChange={(event) => updateDraftFilter("source_module", event.target.value)}
              value={draftFilters.source_module}
            />
          </label>
          <label>
            Evidence type
            <input
              onChange={(event) => updateDraftFilter("evidence_type", event.target.value)}
              value={draftFilters.evidence_type}
            />
          </label>
          <label>
            Status
            <input onChange={(event) => updateDraftFilter("status", event.target.value)} value={draftFilters.status} />
          </label>
          <label>
            Project
            <input
              onChange={(event) => updateDraftFilter("project_id", event.target.value)}
              value={draftFilters.project_id}
            />
          </label>
          <label>
            Sensitivity
            <input
              onChange={(event) => updateDraftFilter("sensitivity_level", event.target.value)}
              value={draftFilters.sensitivity_level}
            />
          </label>
          <label>
            Artifact
            <input
              onChange={(event) => updateDraftFilter("artifact_id", event.target.value)}
              value={draftFilters.artifact_id}
            />
          </label>
          <label>
            Manifest
            <input
              onChange={(event) => updateDraftFilter("manifest_id", event.target.value)}
              value={draftFilters.manifest_id}
            />
          </label>
          <div className="evidence-filter-actions">
            <Button onClick={handleApplyFilters} variant="primary">
              Apply filters
            </Button>
            <Button onClick={handleClearFilters}>Clear</Button>
          </div>
        </div>

        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        <ModuleObjectList
          ariaLabel="Evidence entries"
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
      </ModuleWorkspaceLayout>
    </>
  );
}
