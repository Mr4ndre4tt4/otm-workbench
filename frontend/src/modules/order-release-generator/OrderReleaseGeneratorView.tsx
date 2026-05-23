import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import {
  createOrderReleaseBatch,
  downloadOrderReleaseArtifact,
  generateOrderReleaseXmlArtifact,
  previewOrderReleaseXml,
  submitOrderReleaseToOtm,
  useOrderReleaseArtifacts,
  useOrderReleaseBatches,
  useOrderReleaseTemplates
} from '../../platform/hooks';
import type {
  OrderReleaseArtifact,
  OrderReleaseBatch,
  OrderReleaseTemplate,
  OrderReleaseXmlArtifact,
  OrderReleaseXmlPreview
} from '../../platform/types';
import { ApiError } from '../../platform/api';
import { PageHeader } from '../../app/shell';
import {
  ArtifactList,
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

function orderReleaseTemplateMeta(item: OrderReleaseTemplate) {
  return [
    item.macro_object_code,
    `v${item.version}`,
    `${item.required_columns.length} required`,
    `${item.optional_columns.length} optional`
  ];
}

const workflowStages = [
  { id: "templates", title: "Templates", status: "1" },
  { id: "batch", title: "Batch", status: "2" },
  { id: "preview", title: "Preview", status: "3" },
  { id: "artifact", title: "Artifact", status: "4" },
  { id: "submit", title: "Submit", status: "5" }
] as const;

type OrderReleaseWorkflowStage = (typeof workflowStages)[number]["id"];

const syntheticOrderReleaseRows = [
  {
    release_gid: "OTM1.OR_SYN_001",
    source_location_gid: "OTM1.SOURCE_A",
    destination_location_gid: "OTM1.DEST_A",
    early_pickup_date: "2026-05-20 08:00:00",
    late_delivery_date: "2026-05-21 17:00:00",
    item_gid: "OTM1.ITEM_A",
    packaged_item_gid: "OTM1.PACK_A",
    weight: "100",
    weight_uom: "KG"
  },
  {
    release_gid: "OTM1.OR_SYN_001",
    source_location_gid: "OTM1.SOURCE_A",
    destination_location_gid: "OTM1.DEST_A",
    early_pickup_date: "2026-05-20 08:00:00",
    late_delivery_date: "2026-05-21 17:00:00",
    item_gid: "OTM1.ITEM_B",
    packaged_item_gid: "OTM1.PACK_B",
    weight: "55",
    weight_uom: "KG"
  },
  {
    release_gid: "OTM1.OR_SYN_002",
    source_location_gid: "OTM1.SOURCE_B",
    destination_location_gid: "OTM1.DEST_B",
    early_pickup_date: "2026-05-22 08:00:00",
    late_delivery_date: "2026-05-23 17:00:00",
    item_gid: "OTM1.ITEM_C",
    packaged_item_gid: "OTM1.PACK_C",
    weight: "75",
    weight_uom: "KG"
  }
];

type DraftOrderReleaseRow = Record<string, string>;

function batchMeta(batch: OrderReleaseBatch) {
  return [
    batch.file_name,
    `${batch.row_count} row(s)`,
    `${batch.release_count} release(s)`,
    `${batch.issue_count} issue(s)`
  ];
}

function batchRowIssueItems(batch: OrderReleaseBatch | null) {
  return (batch?.rows ?? []).flatMap((row) =>
    row.issues.map((issue, issueIndex) => ({
      id: `${row.id}-${issueIndex}`,
      meta: [`Row ${row.row_number}`, String(issue.column ?? "row"), String(issue.severity ?? "ERROR")],
      status: row.status,
      title: String(issue.code ?? "ROW_ISSUE")
    }))
  );
}

function normalizeDraftRows(rows: Array<Record<string, unknown>>): DraftOrderReleaseRow[] {
  return rows.map((row) =>
    Object.fromEntries(Object.entries(row).map(([key, value]) => [key, String(value ?? "")]))
  );
}

function templateColumns(template: OrderReleaseTemplate | null) {
  if (!template) return [];
  return Array.from(new Set([...template.required_columns, ...template.optional_columns]));
}

function emptyDraftRow(template: OrderReleaseTemplate | null): DraftOrderReleaseRow {
  const row: DraftOrderReleaseRow = {};
  for (const column of templateColumns(template)) {
    row[column] = String(template?.defaults[column] ?? "");
  }
  return row;
}

function draftRowsForTemplate(template: OrderReleaseTemplate | null, existingRows: DraftOrderReleaseRow[]) {
  const columns = templateColumns(template);
  if (!template || !columns.length) return existingRows;
  return existingRows.map((row) => {
    const next = emptyDraftRow(template);
    for (const column of columns) {
      next[column] = row[column] ?? next[column] ?? "";
    }
    return next;
  });
}

function serializeDraftRows(rows: DraftOrderReleaseRow[]) {
  return rows.map((row) =>
    Object.fromEntries(
      Object.entries(row)
        .map(([key, value]) => [key, value.trim()])
        .filter(([, value]) => value)
    )
  );
}

export function OrderReleaseGeneratorView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const templates = useOrderReleaseTemplates(token);
  const batches = useOrderReleaseBatches(token);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<OrderReleaseWorkflowStage>("templates");
  const [fileName, setFileName] = useState("synthetic_order_release_rows.json");
  const [draftRows, setDraftRows] = useState<DraftOrderReleaseRow[]>(normalizeDraftRows(syntheticOrderReleaseRows));
  const [createdBatch, setCreatedBatch] = useState<OrderReleaseBatch | null>(null);
  const [xmlPreview, setXmlPreview] = useState<OrderReleaseXmlPreview | null>(null);
  const [xmlArtifact, setXmlArtifact] = useState<OrderReleaseXmlArtifact | null>(null);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const [submitGuard, setSubmitGuard] = useState<Record<string, unknown> | null>(null);
  const [operationMessage, setOperationMessage] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const templateItems = templates.data?.items ?? [];
  const batchItems = batches.data?.items ?? [];
  const effectiveTemplateId = selectedTemplateId ?? templateItems[0]?.id ?? null;
  const effectiveBatchId = selectedBatchId ?? createdBatch?.id ?? batchItems[0]?.id ?? null;
  const selectedTemplate = templateItems.find((item) => item.id === effectiveTemplateId) ?? null;
  const selectedBatch = createdBatch?.id === effectiveBatchId
    ? createdBatch
    : batchItems.find((item) => item.id === effectiveBatchId) ?? null;
  const requiredColumnCount = selectedTemplate?.required_columns.length ?? 0;
  const optionalColumnCount = selectedTemplate?.optional_columns.length ?? 0;
  const defaultCount = selectedTemplate ? Object.keys(selectedTemplate.defaults).length : 0;
  const activeBatch = selectedBatch ?? createdBatch;
  const artifacts = useOrderReleaseArtifacts(token, activeBatch?.id ?? null);
  const activeBatchIsValid = activeBatch?.status === "VALID";
  const activeBatchRowIssues = batchRowIssueItems(activeBatch);

  if (templates.isLoading) {
    return <StatePanel>Loading Order Release Generator...</StatePanel>;
  }

  if (templates.isError || !templates.data) {
    return <StatePanel tone="error">Order Release Generator is unavailable.</StatePanel>;
  }

  const runAction = async <T,>(action: () => Promise<T>, onSuccess: (result: T) => string) => {
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await action();
      setOperationMessage(onSuccess(result));
    } catch (error) {
      if (error instanceof ApiError) {
        setOperationError(error.message);
        setSubmitGuard(error.details);
      } else {
        setOperationError(error instanceof Error ? error.message : "Order Release action failed.");
      }
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateBatch = () => {
    if (!effectiveTemplateId) return;
    void runAction(
      async () => {
        const rows = serializeDraftRows(draftRows);
        const result = await createOrderReleaseBatch(token, {
          template_id: effectiveTemplateId,
          file_name: fileName.trim() || "synthetic_order_release_rows.json",
          rows
        });
        setCreatedBatch(result);
        setSelectedBatchId(result.id);
        setXmlPreview(null);
        setXmlArtifact(null);
        setSubmitGuard(null);
        await queryClient.invalidateQueries({ queryKey: ["modules", "order-release-generator", "batches"] });
        await queryClient.invalidateQueries({
          queryKey: ["modules", "order-release-generator", "batches", result.id, "artifacts"]
        });
        return result;
      },
      (result) => `Order Release batch ${result.id} created.`
    );
  };

  const handleSelectTemplate = (templateId: string) => {
    const nextTemplate = templateItems.find((item) => item.id === templateId) ?? null;
    setSelectedTemplateId(templateId);
    setDraftRows((currentRows) => draftRowsForTemplate(nextTemplate, currentRows));
  };

  const handleDraftRowChange = (rowIndex: number, column: string, value: string) => {
    setDraftRows((rows) =>
      rows.map((row, index) => (index === rowIndex ? { ...row, [column]: value } : row))
    );
  };

  const handleAddDraftRow = () => {
    setDraftRows((rows) => [...rows, emptyDraftRow(selectedTemplate)]);
  };

  const handleRemoveDraftRow = (rowIndex: number) => {
    setDraftRows((rows) => rows.filter((_, index) => index !== rowIndex));
  };

  const handlePreviewXml = () => {
    if (!activeBatch) return;
    void runAction(
      async () => {
        const result = await previewOrderReleaseXml(token, activeBatch.id);
        setXmlPreview(result);
        return result;
      },
      () => "Order Release XML preview generated."
    );
  };

  const handleGenerateArtifact = () => {
    if (!activeBatch) return;
    void runAction(
      async () => {
        const result = await generateOrderReleaseXmlArtifact(token, activeBatch.id);
        setXmlArtifact(result);
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ["modules", "order-release-generator", "batches"] }),
          queryClient.invalidateQueries({
            queryKey: ["modules", "order-release-generator", "batches", activeBatch.id, "artifacts"]
          })
        ]);
        return result;
      },
      (result) => `Order Release XML artifact ${result.artifact_id} generated.`
    );
  };

  const handleDownloadArtifact = async (artifactId: string, href: string, fallbackName: string) => {
    setDownloadingArtifactId(artifactId);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await downloadOrderReleaseArtifact(token, href);
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.filename ?? fallbackName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setOperationMessage(`Order Release artifact ${link.download} downloaded.`);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not download Order Release artifact.");
    } finally {
      setDownloadingArtifactId(null);
    }
  };

  const handleSubmitGuard = () => {
    if (!activeBatch) return;
    void runAction(
      async () => submitOrderReleaseToOtm(token, activeBatch.id),
      () => "Order Release submitted to OTM."
    );
  };

  const generatedArtifacts: OrderReleaseArtifact[] = artifacts.data?.items.length
    ? artifacts.data.items
    : xmlArtifact
      ? [
          {
            artifact_type: "order_release_xml",
            batch_id: xmlArtifact.batch_id,
            content_type: xmlArtifact.content_type ?? "application/xml",
            download_url: xmlArtifact.download_url ?? null,
            file_name: xmlArtifact.file_name,
            id: xmlArtifact.artifact_id,
            sensitivity_level: "internal",
            sha256: xmlArtifact.sha256,
            size_bytes: xmlArtifact.size_bytes,
            source_module: "order_release_generator"
          }
        ]
      : [];

  return (
    <>
      <PageHeader
        description="Order release template, batch, XML preview, artifact, and job orchestration workspace."
        label="Module workspace"
        title="Order Release Generator"
      />

      <MetricGrid
        ariaLabel="Order Release Generator metrics"
        items={[
          { key: "templates", label: "Templates", status: booleanStatus(templates.data.total), value: templates.data.total },
          { key: "required", label: "Required columns", status: booleanStatus(requiredColumnCount), value: requiredColumnCount },
          { key: "optional", label: "Optional columns", status: booleanStatus(optionalColumnCount), value: optionalColumnCount },
          { key: "defaults", label: "Defaults", status: booleanStatus(defaultCount), value: defaultCount }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Order Release Generator workspace"
        side={
          <SelectedObjectPanel
            ariaLabel="Selected Order Release template"
            emptyText="Select a template to inspect backend-owned Order Release metadata."
            fields={
              selectedTemplate
                ? [
                    { label: "Macro object", value: selectedTemplate.macro_object_code },
                    { label: "Version", value: selectedTemplate.version },
                    { label: "Required columns", value: selectedTemplate.required_columns.length },
                    { label: "Optional columns", value: selectedTemplate.optional_columns.length }
                  ]
                : []
            }
            isLoading={templates.isLoading}
            loadingText="Loading selected template..."
            status={selectedTemplate?.status ?? "PENDING"}
            subtitle={selectedTemplate?.name}
            title={selectedTemplate?.code}
          >
            {selectedTemplate?.description ? <p className="empty-text">{selectedTemplate.description}</p> : null}
            <DetailList
              ariaLabel="Selected order release required columns"
              emptyText="No required columns defined for this template."
              items={(selectedTemplate?.required_columns ?? []).map((column) => ({
                id: `required-${column}`,
                meta: ["Required"],
                status: "REQUIRED",
                title: column
              }))}
            />
            <DetailList
              ariaLabel="Selected order release optional columns and defaults"
              emptyText="No optional columns or defaults defined for this template."
              items={[
                ...(selectedTemplate?.optional_columns ?? []).map((column) => ({
                  id: `optional-${column}`,
                  meta: ["Optional"],
                  status: "OPTIONAL",
                  title: column
                })),
                ...Object.entries(selectedTemplate?.defaults ?? {}).map(([key, value]) => ({
                  id: `default-${key}`,
                  meta: [`Default: ${String(value)}`],
                  status: "DEFAULT",
                  title: key
                }))
              ]}
            />
          </SelectedObjectPanel>
        }
        status={activeBatch?.status ?? (templateItems.length ? "ACTIVE" : "EMPTY")}
        title="Generator workflow"
      >
        <div className="workflow-tabs" aria-label="Order Release Generator workflow">
          {workflowStages.map((stage) => (
            <Button
              key={stage.id}
              onClick={() => setActiveStage(stage.id)}
              variant={activeStage === stage.id ? "primary" : "secondary"}
            >
              {stage.status}
              {stage.title}
            </Button>
          ))}
        </div>

        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        {activeStage === "templates" ? (
          <OperationalPanel
            ariaLabel="Order Release template selection"
            emptyText="No Order Release templates available for the current context."
            hasItems={Boolean(templateItems.length)}
            status={templateItems.length ? "ACTIVE" : "EMPTY"}
            title="Templates"
          >
            <ModuleObjectList
              ariaLabel="Order Release templates"
              emptyText="No Order Release templates available for the current context."
              items={templateItems.map((item) => ({
                id: item.id,
                meta: orderReleaseTemplateMeta(item),
                status: item.status,
                subtitle: item.name,
                title: item.code
              }))}
              onSelect={handleSelectTemplate}
              selectedId={effectiveTemplateId}
            />
          </OperationalPanel>
        ) : null}

        {activeStage === "batch" ? (
          <OperationalPanel
            ariaLabel="Order Release batch authoring"
            emptyText="Select a template before creating an Order Release batch."
            hasItems={Boolean(effectiveTemplateId)}
            status={activeBatch?.status ?? "PENDING"}
            title="Batch"
          >
            <div className="master-data-author-grid">
              <label>
                Batch file name
                <input
                  aria-label="Batch file name"
                  onChange={(event) => setFileName(event.target.value)}
                  value={fileName}
                />
              </label>
            </div>
            <div className="master-data-action-bar">
              <Button disabled={!selectedTemplate} onClick={handleAddDraftRow} variant="secondary">
                Add row
              </Button>
            </div>
            <div aria-label="Order Release row editor" className="template-author-table-list">
              {draftRows.map((row, rowIndex) => (
                <section aria-label={`Order Release row ${rowIndex + 1}`} className="template-author-table-card" key={rowIndex}>
                  <div className="template-author-table-card__header">
                    <h4>Row {rowIndex + 1}</h4>
                    <Button
                      disabled={draftRows.length === 1}
                      onClick={() => handleRemoveDraftRow(rowIndex)}
                      variant="secondary"
                    >
                      Remove row
                    </Button>
                  </div>
                  <div className="master-data-author-grid">
                    {templateColumns(selectedTemplate).map((column) => {
                      const required = Boolean(selectedTemplate?.required_columns.includes(column));
                      return (
                        <label key={`${rowIndex}-${column}`}>
                          {column}
                          <input
                            aria-label={`Row ${rowIndex + 1} ${column}`}
                            onChange={(event) => handleDraftRowChange(rowIndex, column, event.target.value)}
                            required={required}
                            value={row[column] ?? ""}
                          />
                        </label>
                      );
                    })}
                  </div>
                </section>
              ))}
            </div>
            <div className="master-data-action-bar">
              <Button disabled={isMutating || !effectiveTemplateId || !draftRows.length} onClick={handleCreateBatch} variant="primary">
                Create batch
              </Button>
            </div>
            {activeBatch ? (
              <>
                <DetailList
                  ariaLabel="Active Order Release batch"
                  items={[
                    {
                      id: activeBatch.id,
                      meta: batchMeta(activeBatch),
                      status: activeBatch.status,
                      title: activeBatch.id
                    }
                  ]}
                />
                {activeBatchRowIssues.length ? (
                  <DetailList ariaLabel="Order Release batch row issues" items={activeBatchRowIssues} />
                ) : null}
              </>
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "preview" ? (
          <OperationalPanel
            ariaLabel="Order Release XML preview workflow"
            emptyText="Create or select a valid batch before previewing XML."
            hasItems={Boolean(activeBatch)}
            status={xmlPreview ? "PREVIEWED" : activeBatch?.status ?? "PENDING"}
            title="Preview"
          >
            <div className="master-data-action-bar">
              <Button disabled={isMutating || !activeBatch || !activeBatchIsValid} onClick={handlePreviewXml} variant="primary">
                Preview XML
              </Button>
            </div>
            {!activeBatchIsValid && activeBatch ? (
              <FeedbackMessage tone="error">Fix invalid batch rows before previewing XML.</FeedbackMessage>
            ) : null}
            {xmlPreview ? (
              <DetailList
                ariaLabel="Order Release XML preview"
                items={[
                  {
                    id: xmlPreview.job_id,
                    meta: [`${xmlPreview.release_count} release(s)`, `${xmlPreview.line_count} line(s)`, xmlPreview.xml],
                    status: "PREVIEWED",
                    title: "Transmission"
                  }
                ]}
              />
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "artifact" ? (
          <OperationalPanel
            ariaLabel="Order Release XML artifact workflow"
            emptyText="Create or select a valid batch before generating XML artifacts."
            hasItems={Boolean(activeBatch)}
            status={xmlArtifact?.status ?? (xmlArtifact ? "GENERATED" : "PENDING")}
            title="Artifact"
          >
            <div className="master-data-action-bar">
              <Button disabled={isMutating || !activeBatch || !activeBatchIsValid} onClick={handleGenerateArtifact} variant="primary">
                Generate XML artifact
              </Button>
            </div>
            {!activeBatchIsValid && activeBatch ? (
              <FeedbackMessage tone="error">Fix invalid batch rows before generating XML artifacts.</FeedbackMessage>
            ) : null}
            {generatedArtifacts.length ? (
              <section aria-label="Order Release XML artifact" className="integration-generated-artifacts">
                <ArtifactList
                  items={generatedArtifacts.map((artifact) => ({
                  action: artifact.download_url ? (
                    <Button
                      disabled={downloadingArtifactId === artifact.id}
                      onClick={() => void handleDownloadArtifact(artifact.id, artifact.download_url!, artifact.file_name)}
                      variant="secondary"
                    >
                      {downloadingArtifactId === artifact.id ? "Downloading..." : "Download"}
                    </Button>
                  ) : undefined,
                  id: artifact.id,
                  meta: [
                    artifact.file_name,
                    artifact.content_type,
                    `${artifact.size_bytes} byte(s)`,
                    artifact.sha256
                  ],
                  status: artifact.download_url ? "READY" : "UNAVAILABLE",
                  subtitle: artifact.artifact_type,
                  title: artifact.id
                }))}
                />
              </section>
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "submit" ? (
          <OperationalPanel
            ariaLabel="Order Release OTM submit guard workflow"
            emptyText="Create or select a batch before verifying submit guard state."
            hasItems={Boolean(activeBatch)}
            status={submitGuard ? "GUARDED" : "PENDING"}
            title="Submit"
          >
            <div className="master-data-action-bar">
              <Button disabled={isMutating || !activeBatch} onClick={handleSubmitGuard} variant="primary">
                Verify OTM submit guard
              </Button>
            </div>
            {submitGuard ? (
              <DetailList
                ariaLabel="OTM submit guard"
                items={[
                  {
                    id: String(submitGuard.batch_id ?? activeBatch?.id ?? "submit-guard"),
                    meta: [
                      String(submitGuard.required_capability ?? "No capability"),
                      String(submitGuard.reason ?? "No guard reason")
                    ],
                    status: "GUARDED",
                    title: "Direct OTM submit disabled"
                  }
                ]}
              />
            ) : null}
          </OperationalPanel>
        ) : null}

        <DetailList
          ariaLabel="Recent Order Release batches"
          emptyText="No backend-owned Order Release batches created yet."
          items={batchItems.map((batch) => ({
            id: batch.id,
            meta: batchMeta(batch),
            status: batch.status,
            title: batch.id
          }))}
        />
      </ModuleWorkspaceLayout>
    </>
  );
}
