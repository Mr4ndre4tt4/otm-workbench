import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../../platform/api";
import {
  downloadBackendArtifact,
  executeBackendAction,
  useRateBatchArtifacts,
  useRateBatchDetail,
  useRateBatchEvidence,
  useRatesSummary
} from "../../platform/hooks";
import type { AvailableAction, RatesSummaryItem } from "../../platform/types";
import { ActionBar, PageHeader } from "../../app/shell";
import {
  ArtifactList,
  BlockerPanel,
  Button,
  DetailList,
  FeedbackMessage,
  MetricGrid,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  OperationalPanel,
  SelectedObjectPanel,
  StatePanel
} from "../../ui/components";

function severityStatus(severity: string) {
  if (severity === "success") return "READY";
  if (severity === "warning") return "BLOCKED";
  if (severity === "danger") return "ERROR";
  return "INFO";
}

function rateBatchMeta(batch: RatesSummaryItem) {
  const issueCount = Object.values(batch.summary.issue_summary).reduce((total, value) => total + value, 0);
  return [`${batch.summary.table_count} table(s)`, `${batch.summary.row_count} row(s)`, `${issueCount} issue(s)`];
}

export function RatesSummaryView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const rates = useRatesSummary(token);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [runningActionKey, setRunningActionKey] = useState<string | null>(null);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const recentObjects = rates.data?.recent_objects ?? [];
  const effectiveBatchId = selectedBatchId ?? recentObjects[0]?.id ?? null;
  const batchDetail = useRateBatchDetail(token, effectiveBatchId);
  const batchArtifacts = useRateBatchArtifacts(token, effectiveBatchId);
  const batchEvidence = useRateBatchEvidence(token, effectiveBatchId);

  if (rates.isLoading) {
    return <StatePanel>Loading Rates Studio...</StatePanel>;
  }

  if (rates.isError || !rates.data) {
    return <StatePanel tone="error">Rates Studio summary is unavailable.</StatePanel>;
  }

  const data = rates.data;

  async function runBatchAction(action: AvailableAction) {
    if (action.method !== "POST" || action.disabled) return;
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey(action.key);
    try {
      await executeBackendAction(token, action.href);
      setActionMessage(`${action.label} completed.`);
      if (action.result_hint === "refresh_object" || action.result_hint === "refresh_list") {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
          queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId] })
        ]);
      }
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError(`${action.label} failed.`);
      }
    } finally {
      setRunningActionKey(null);
    }
  }

  async function downloadArtifact(artifactId: string, href: string, fallbackName: string) {
    setActionMessage(null);
    setActionError(null);
    setDownloadingArtifactId(artifactId);
    try {
      const result = await downloadBackendArtifact(token, href);
      const objectUrl = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = result.filename ?? fallbackName;
      link.click();
      URL.revokeObjectURL(objectUrl);
      setActionMessage(`Download started: ${result.filename ?? fallbackName}.`);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError("Download failed.");
      }
    } finally {
      setDownloadingArtifactId(null);
    }
  }

  return (
    <>
      <PageHeader
        actions={data.available_actions}
        description={data.description}
        label="Module workspace"
        title={data.title}
      />

      <MetricGrid
        ariaLabel="Rates summary metrics"
        items={data.counts.map((count) => ({
          key: count.key,
          label: count.label,
          status: severityStatus(count.severity),
          value: count.value
        }))}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Rates Studio workspace"
        side={
          <SelectedObjectPanel
            ariaLabel="Selected rate batch"
            actions={
              batchDetail.data ? (
                <ActionBar
                  actions={batchDetail.data.available_actions}
                  onAction={(action) => void runBatchAction(action)}
                  runningActionKey={runningActionKey}
                />
              ) : null
            }
            emptyText="Select a rate batch to inspect backend-owned details."
            fields={
              batchDetail.data
                ? [
                    { label: "Domain", value: batchDetail.data.domain_name },
                    { label: "Macro object", value: batchDetail.data.catalog_macro_object_code },
                    { label: "Tables", value: batchDetail.data.tables.length }
                  ]
                : []
            }
            isLoading={batchDetail.isLoading && Boolean(effectiveBatchId)}
            loadingText="Loading selected batch..."
            status={batchDetail.data?.status ?? "PENDING"}
            subtitle={batchDetail.data?.scenario_code}
            title={batchDetail.data?.name}
          >
            {actionMessage ? <FeedbackMessage tone="success">{actionMessage}</FeedbackMessage> : null}
            {actionError ? <FeedbackMessage tone="error">{actionError}</FeedbackMessage> : null}
            <DetailList
              ariaLabel="Selected batch tables"
              emptyText="No tables have been staged for this batch."
              items={(batchDetail.data?.tables ?? []).map((table) => ({
                id: table.id,
                meta: [`${table.row_count} row(s)`],
                status: table.status,
                title: table.table_name
              }))}
            />
          </SelectedObjectPanel>
        }
        status={data.recent_objects.length ? "ACTIVE" : "EMPTY"}
        title="Recent rate batches"
      >
        <ModuleObjectList
          ariaLabel="Rate batches"
          emptyText="No rate batches available for the current context."
          items={data.recent_objects.map((batch) => ({
            id: batch.id,
            meta: rateBatchMeta(batch),
            status: batch.status,
            subtitle: batch.code,
            title: batch.display_name
          }))}
          onSelect={setSelectedBatchId}
          selectedId={effectiveBatchId}
        />
      </ModuleWorkspaceLayout>

      <BlockerPanel
        emptyText="No open blockers in the current rates summary."
        items={data.open_blockers.map((blocker) => ({
          codes: blocker.codes,
          id: `${blocker.object_type}-${blocker.object_id}`,
          message: blocker.message
        }))}
        title="Open blockers"
      />

      <section className="activity-layout">
        <OperationalPanel
          ariaLabel="Rate batch export artifacts"
          emptyText="No export artifacts registered for this batch."
          hasItems={(batchArtifacts.data?.items.length ?? 0) > 0}
          isLoading={batchArtifacts.isLoading && Boolean(effectiveBatchId)}
          loadingText="Loading artifacts..."
          status={batchArtifacts.data?.total ? "ACTIVE" : "EMPTY"}
          title="Batch artifacts"
        >
          <ArtifactList
            items={(batchArtifacts.data?.items ?? []).map((artifact) => ({
              action: artifact.download_url ? (
                  <Button
                    disabled={downloadingArtifactId === artifact.id}
                    onClick={() => void downloadArtifact(artifact.id, artifact.download_url!, artifact.file_name)}
                  >
                    {downloadingArtifactId === artifact.id ? "Downloading..." : "Download"}
                  </Button>
                ) : undefined,
              id: artifact.id,
              meta: [artifact.content_type, `${artifact.size_bytes} bytes`],
              status: artifact.download_url ? undefined : artifact.sensitivity_level,
              subtitle: artifact.artifact_type,
              title: artifact.file_name
            }))}
          />
        </OperationalPanel>

        <OperationalPanel
          ariaLabel="Rate batch evidence"
          emptyText="No evidence registered for this batch."
          hasItems={(batchEvidence.data?.items.length ?? 0) > 0}
          isLoading={batchEvidence.isLoading && Boolean(effectiveBatchId)}
          loadingText="Loading evidence..."
          status={batchEvidence.data?.total ? "ACTIVE" : "EMPTY"}
          title="Batch evidence"
        >
          <ArtifactList
            items={(batchEvidence.data?.items ?? []).map((evidence) => ({
              id: evidence.id,
              meta: [evidence.artifact_id ? "Artifact linked" : "No artifact", evidence.client_safe ? "Client safe" : "Internal"],
              status: evidence.status,
              subtitle: evidence.sensitivity_level,
              title: evidence.evidence_type
            }))}
          />
        </OperationalPanel>
      </section>
    </>
  );
}
