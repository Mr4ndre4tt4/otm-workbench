import { useState } from "react";
import { Bot, ExternalLink, Search, Truck, X } from "lucide-react";

import {
  draftAssistantSql,
  explainAssistantSql,
  prepareOracleLookup,
  useAssistantHealth,
  useAssistantSearch
} from "../../platform/hooks";
import type { AssistantOracleLookupRequest, AssistantSqlDraft, NavigationItem } from "../../platform/types";
import { Button, IconButton, StatusChip } from "../../ui/components";

type WorkbenchAssistantProps = {
  currentPath: string;
  navigationItems: NavigationItem[];
  token: string;
};

function privateTermsFromInput(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function sqlColumnsFromInput(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function activeModuleLabel(currentPath: string, navigationItems: NavigationItem[]) {
  if (currentPath === "/") {
    return navigationItems.find((item) => item.id === "home")?.label ?? "Current route";
  }
  const sortedItems = [...navigationItems].sort((left, right) => right.path.length - left.path.length);
  const activeItem = sortedItems.find((item) => currentPath === item.path || currentPath.startsWith(`${item.path}/`));
  return activeItem?.label ?? "Current route";
}

export function WorkbenchAssistant({ currentPath, navigationItems, token }: WorkbenchAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [sourceQuery, setSourceQuery] = useState("");
  const [submittedSourceQuery, setSubmittedSourceQuery] = useState("");
  const [oracleQuestion, setOracleQuestion] = useState("");
  const [privateTerms, setPrivateTerms] = useState("");
  const [oracleLookup, setOracleLookup] = useState<AssistantOracleLookupRequest | null>(null);
  const [oracleError, setOracleError] = useState<string | null>(null);
  const [isPreparingOracle, setIsPreparingOracle] = useState(false);
  const [sqlTable, setSqlTable] = useState("");
  const [sqlColumns, setSqlColumns] = useState("");
  const [sqlFilterColumn, setSqlFilterColumn] = useState("");
  const [sqlPurpose, setSqlPurpose] = useState("");
  const [sqlDraft, setSqlDraft] = useState<AssistantSqlDraft | null>(null);
  const [sqlError, setSqlError] = useState<string | null>(null);
  const [isDraftingSql, setIsDraftingSql] = useState(false);
  const [sqlToReview, setSqlToReview] = useState("");
  const [sqlReview, setSqlReview] = useState<AssistantSqlDraft | null>(null);
  const [sqlReviewError, setSqlReviewError] = useState<string | null>(null);
  const [isReviewingSql, setIsReviewingSql] = useState(false);
  const health = useAssistantHealth(token, isOpen);
  const sourceResults = useAssistantSearch(token, submittedSourceQuery, isOpen && Boolean(submittedSourceQuery));
  const moduleLabel = activeModuleLabel(currentPath, navigationItems);

  function setHelpQuery() {
    setSourceQuery(`${moduleLabel} help`);
  }

  function setTemplateQuery() {
    setSourceQuery(`${moduleLabel} template`);
  }

  function setOracleDocsQuestion() {
    setOracleQuestion(`Oracle Transportation Management ${moduleLabel} documentation`);
  }

  async function submitSourceSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmittedSourceQuery(sourceQuery.trim());
  }

  async function submitOracleLookup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!oracleQuestion.trim() || isPreparingOracle) return;
    setOracleError(null);
    setIsPreparingOracle(true);
    try {
      const payload = await prepareOracleLookup(token, oracleQuestion.trim(), privateTermsFromInput(privateTerms));
      setOracleLookup(payload);
    } catch {
      setOracleError("Unable to prepare Oracle lookup.");
    } finally {
      setIsPreparingOracle(false);
    }
  }

  async function submitSqlDraft(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const columns = sqlColumnsFromInput(sqlColumns);
    if (!sqlTable.trim() || !columns.length || !sqlFilterColumn.trim() || isDraftingSql) return;
    setSqlError(null);
    setIsDraftingSql(true);
    try {
      const payload = await draftAssistantSql(token, {
        table_name: sqlTable.trim(),
        columns,
        filter_column: sqlFilterColumn.trim(),
        purpose: sqlPurpose.trim() || "Draft a safe OTM SELECT."
      });
      setSqlDraft(payload);
    } catch {
      setSqlError("Unable to draft SQL from the local Data Dictionary.");
    } finally {
      setIsDraftingSql(false);
    }
  }

  async function submitSqlReview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sqlToReview.trim() || isReviewingSql) return;
    setSqlReviewError(null);
    setIsReviewingSql(true);
    try {
      const payload = await explainAssistantSql(token, { sql_text: sqlToReview.trim() });
      setSqlReview(payload);
    } catch {
      setSqlReviewError("Unable to review SQL from the local Data Dictionary.");
    } finally {
      setIsReviewingSql(false);
    }
  }

  return (
    <div className="assistant-overlay">
      {isOpen ? (
        <section aria-label="Workbench Assistant panel" className="assistant-panel">
          <div className="assistant-panel-header">
            <div>
              <p className="section-label">Consultant assistant</p>
              <h2>Workbench Assistant</h2>
            </div>
            <IconButton label="Close Workbench Assistant" onClick={() => setIsOpen(false)}>
              <X aria-hidden="true" />
            </IconButton>
          </div>

          <div className="assistant-status-row">
            <StatusChip status={health.data?.status === "ok" ? "CONNECTED" : "PENDING"} />
            <span>{health.data?.status === "ok" ? "Assistant backend connected" : "Checking Assistant backend"}</span>
          </div>

          <div className="assistant-context-strip" aria-label="Assistant context">
            <span>Current screen</span>
            <strong>{moduleLabel}</strong>
          </div>

          <div className="assistant-quick-actions" aria-label="Assistant quick actions">
            <button type="button" onClick={setHelpQuery}>
              Help for this screen
            </button>
            <button type="button" onClick={setTemplateQuery}>
              Find template
            </button>
            <button type="button" onClick={setOracleDocsQuestion}>
              Search Oracle docs
            </button>
          </div>

          <form className="assistant-tool" onSubmit={(event) => void submitSourceSearch(event)}>
            <label>
              <span>Search Workbench sources</span>
              <input value={sourceQuery} onChange={(event) => setSourceQuery(event.target.value)} />
            </label>
            <Button type="submit" variant="primary">
              <Search aria-hidden="true" />
              Search sources
            </Button>
          </form>

          {sourceResults.data?.items.length ? (
            <div className="assistant-result-list" aria-label="Assistant source results">
              {sourceResults.data.items.map((item) => (
                <article className="assistant-result" key={item.chunk_id}>
                  <strong>{item.source_title}</strong>
                  <span>{item.source_uri}</span>
                  <p>{item.snippet}</p>
                </article>
              ))}
            </div>
          ) : null}

          <form className="assistant-tool" onSubmit={(event) => void submitOracleLookup(event)}>
            <label>
              <span>Oracle docs question</span>
              <textarea value={oracleQuestion} onChange={(event) => setOracleQuestion(event.target.value)} rows={3} />
            </label>
            <label>
              <span>Private terms</span>
              <input value={privateTerms} onChange={(event) => setPrivateTerms(event.target.value)} />
            </label>
            <Button disabled={isPreparingOracle} type="submit" variant="primary">
              <ExternalLink aria-hidden="true" />
              Prepare Oracle lookup
            </Button>
          </form>

          {oracleError ? <p className="form-error">{oracleError}</p> : null}
          {oracleLookup ? (
            <div className="assistant-oracle-preview">
              <span>Sanitized query</span>
              <strong>{oracleLookup.sanitized_query}</strong>
              {oracleLookup.actions.map((action) => (
                <a href={action.url} key={action.url} rel="noreferrer" target="_blank">
                  {action.label}
                </a>
              ))}
            </div>
          ) : null}

          <form className="assistant-tool" onSubmit={(event) => void submitSqlDraft(event)}>
            <label>
              <span>SQL table</span>
              <input value={sqlTable} onChange={(event) => setSqlTable(event.target.value)} />
            </label>
            <label>
              <span>SQL columns</span>
              <input value={sqlColumns} onChange={(event) => setSqlColumns(event.target.value)} />
            </label>
            <label>
              <span>SQL filter column</span>
              <input value={sqlFilterColumn} onChange={(event) => setSqlFilterColumn(event.target.value)} />
            </label>
            <label>
              <span>SQL purpose</span>
              <input value={sqlPurpose} onChange={(event) => setSqlPurpose(event.target.value)} />
            </label>
            <Button disabled={isDraftingSql} type="submit" variant="primary">
              <Search aria-hidden="true" />
              Draft SQL
            </Button>
          </form>

          {sqlError ? <p className="form-error">{sqlError}</p> : null}
          {sqlDraft ? (
            <div className="assistant-sql-preview">
              <span>{sqlDraft.block ? "SQL draft preview" : "SQL draft blocked"}</span>
              {sqlDraft.block ? (
                <>
                  <pre>{sqlDraft.block.sql}</pre>
                  <p>Review before use; Assistant drafts are not executed.</p>
                  {sqlDraft.block.warnings.map((warning) => (
                    <p key={warning}>{warning}</p>
                  ))}
                </>
              ) : (
                <>
                  <strong>{sqlDraft.summary}</strong>
                  {sqlDraft.warnings?.map((warning) => (
                    <p key={warning}>{warning}</p>
                  ))}
                </>
              )}
            </div>
          ) : null}

          <form className="assistant-tool" onSubmit={(event) => void submitSqlReview(event)}>
            <label>
              <span>SQL to review</span>
              <textarea value={sqlToReview} onChange={(event) => setSqlToReview(event.target.value)} rows={4} />
            </label>
            <Button disabled={isReviewingSql} type="submit" variant="primary">
              <Search aria-hidden="true" />
              Review SQL
            </Button>
          </form>

          {sqlReviewError ? <p className="form-error">{sqlReviewError}</p> : null}
          {sqlReview ? (
            <div className="assistant-sql-preview">
              <span>{sqlReview.block ? "SQL review preview" : "SQL review blocked"}</span>
              {sqlReview.block ? (
                <>
                  <pre>{sqlReview.block.sql}</pre>
                  <p>Review before use; Assistant SQL review is not execution.</p>
                  {sqlReview.block.warnings.map((warning) => (
                    <p key={warning}>{warning}</p>
                  ))}
                </>
              ) : (
                <>
                  <strong>{sqlReview.summary}</strong>
                  {sqlReview.warnings?.map((warning) => (
                    <p key={warning}>{warning}</p>
                  ))}
                </>
              )}
            </div>
          ) : null}
        </section>
      ) : null}

      <button className="assistant-launcher" onClick={() => setIsOpen(true)} type="button">
        <span className="assistant-launcher-icon" aria-hidden="true">
          <Bot />
          <Truck />
        </span>
        <span>Open Workbench Assistant</span>
      </button>
    </div>
  );
}
