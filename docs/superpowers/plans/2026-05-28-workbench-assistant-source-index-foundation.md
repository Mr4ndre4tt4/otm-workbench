# Workbench Assistant Source Index Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local source index foundation for the future Workbench Assistant, allowing authenticated users to index approved local/help/documentation sources and search scoped snippets without adding the assistant to the main UI navigation.

**Architecture:** Add an isolated backend module under `src/otm_workbench/assistant/` with SQLAlchemy metadata in the existing monolith, SQLite FTS5 for local full-text search, and FastAPI endpoints under `/api/v1/assistant`. The first slice stores source metadata, chunks sanitized text, rebuilds an FTS index, and returns source-linked search results with scope filtering; it does not call an LLM and does not change the current Workbench UI.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, SQLAlchemy, SQLite FTS5, pytest, existing `require_user` authentication, existing `ActiveContext` scope model.

---

## Scope Guard

This plan implements only Phase 1: local source inventory, chunk indexing, FTS search, and backend contract tests.

In scope:
- Backend-only assistant package and API.
- SQLite-backed source/chunk/index run tables.
- FTS5 virtual table creation and rebuild logic.
- Search endpoint with authenticated access and scope-aware filtering.
- Synthetic fixtures only.
- Documentation update for the Assistant planning track.

Out of scope:
- Floating robot launcher UI.
- Chat orchestration.
- Oracle web lookup connector.
- SQL generation or SQL execution.
- Embeddings, vector database, local LLM, or remote AI provider.
- Adding `assistant` to `/api/v1/platform/navigation`.
- Reading `OTM_RESOURCES/`.

## File Structure

- Modify `src/otm_workbench/models.py`
  - Add `AssistantSource`, `AssistantChunk`, and `AssistantIndexRun` SQLAlchemy models near other operational models.
- Create `src/otm_workbench/assistant/__init__.py`
  - Package marker.
- Create `src/otm_workbench/assistant/services.py`
  - Source creation, text normalization, chunking, SQLite FTS table lifecycle, rebuild, scoped search, serializers.
- Create `src/otm_workbench/assistant/routes.py`
  - FastAPI request/response models and endpoints.
- Modify `src/otm_workbench/main.py`
  - Include the assistant router under `/api/v1/assistant`.
- Create `tests/test_assistant_source_index.py`
  - End-to-end API tests and service-level FTS behavior.
- Modify `docs/agent/assistant-planning/README.md`
  - Link this implementation plan as the first executable backend slice.
- Modify `docs/agent/HANDOFF.md`
  - Record that the implementation plan was created and that code execution is still pending.

## API Contract

- `GET /api/v1/assistant/health`
  - Requires bearer auth.
  - Returns `{"status": "ok", "module": "assistant", "capabilities": ["source_index", "fts_search"]}`.
- `POST /api/v1/assistant/sources`
  - Requires bearer auth.
  - Creates source metadata and optional initial text.
  - Accepts explicit scope fields, defaulting from `ActiveContext` when present.
- `POST /api/v1/assistant/index/rebuild`
  - Requires bearer auth.
  - Rebuilds all accessible local text chunks into SQLite FTS5.
- `GET /api/v1/assistant/search?query=rate+geo&limit=5`
  - Requires bearer auth.
  - Returns ranked snippets and source metadata, filtered to the user active context.

## Data Model

```python
class AssistantSource(Base, TimestampMixin):
    __tablename__ = "assistant_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String, index=True)
    source_type: Mapped[str] = mapped_column(String, index=True)
    source_uri: Mapped[str] = mapped_column(Text, default="")
    module_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    domain_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    visibility: Mapped[str] = mapped_column(String, default="PRIVATE", index=True)
    access_policy_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    content_hash: Mapped[str] = mapped_column(String, default="", index=True)
    status: Mapped[str] = mapped_column(String, default="ACTIVE", index=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class AssistantChunk(Base, TimestampMixin):
    __tablename__ = "assistant_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("assistant_sources.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    heading: Mapped[str] = mapped_column(String, default="")
    body_text: Mapped[str] = mapped_column(Text)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)


class AssistantIndexRun(Base, TimestampMixin):
    __tablename__ = "assistant_index_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

## Task 1: Model Foundation

**Files:**
- Modify: `src/otm_workbench/models.py`
- Test: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write the failing table creation test**

```python
from otm_workbench.models import AssistantChunk, AssistantIndexRun, AssistantSource


def test_assistant_models_are_created(db_session):
    source = AssistantSource(
        title="Rates quick help",
        source_type="WORKBENCH_HELP",
        source_uri="workbench://rates/help",
        module_id="rates",
        domain_name="OTM1",
        visibility="PRIVATE",
        created_by="synthetic-user",
    )
    db_session.add(source)
    db_session.flush()
    chunk = AssistantChunk(
        source_id=source.id,
        chunk_index=0,
        heading="Rates",
        body_text="Use rate offering and rate record together.",
        token_estimate=8,
    )
    run = AssistantIndexRun(status="PENDING")
    db_session.add_all([chunk, run])
    db_session.commit()

    assert db_session.query(AssistantSource).count() == 1
    assert db_session.query(AssistantChunk).count() == 1
    assert db_session.query(AssistantIndexRun).count() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_assistant_source_index.py::test_assistant_models_are_created -v`

Expected: FAIL with `ImportError` for `AssistantSource`.

- [ ] **Step 3: Add the SQLAlchemy models**

Add the three model classes from the Data Model section to `src/otm_workbench/models.py` after `JobEvent` or near the operational support models. Reuse existing imports: `DateTime`, `ForeignKey`, `Integer`, `String`, `Text`, `Mapped`, `mapped_column`, `new_id`, `utcnow`, and `TimestampMixin`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_assistant_source_index.py::test_assistant_models_are_created -v`

Expected: PASS.

- [ ] **Step 5: Commit model foundation**

```bash
git add src/otm_workbench/models.py tests/test_assistant_source_index.py
git commit -m "feat: add assistant source index models"
```

## Task 2: Source Service And FTS Lifecycle

**Files:**
- Create: `src/otm_workbench/assistant/__init__.py`
- Create: `src/otm_workbench/assistant/services.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write the failing service tests**

```python
from otm_workbench.assistant.services import (
    AssistantSourceInput,
    create_assistant_source,
    rebuild_assistant_fts_index,
    search_assistant_sources,
)


def test_assistant_service_chunks_and_searches_text(db_session):
    source = create_assistant_source(
        db_session,
        AssistantSourceInput(
            title="Rate record help",
            source_type="WORKBENCH_HELP",
            source_uri="workbench://rates/rate-record",
            body_text="Rate records need rate geo and rate offering context.",
            module_id="rates",
            domain_name="OTM1",
            visibility="PRIVATE",
            created_by="synthetic-user",
        ),
    )
    run = rebuild_assistant_fts_index(db_session)
    results = search_assistant_sources(
        db_session,
        query_text="rate geo",
        allowed_domains=["PUBLIC", "OTM1"],
        limit=5,
    )

    assert source.title == "Rate record help"
    assert run.status == "COMPLETED"
    assert run.chunk_count == 1
    assert [item["source_title"] for item in results] == ["Rate record help"]
    assert "rate geo" in results[0]["snippet"].lower()


def test_assistant_search_filters_private_domain_chunks(db_session):
    create_assistant_source(
        db_session,
        AssistantSourceInput(
            title="OTM1 private help",
            source_type="WORKBENCH_HELP",
            source_uri="workbench://one",
            body_text="Shipment reference guide for domain one.",
            domain_name="OTM1",
            visibility="PRIVATE",
        ),
    )
    create_assistant_source(
        db_session,
        AssistantSourceInput(
            title="OTM2 private help",
            source_type="WORKBENCH_HELP",
            source_uri="workbench://two",
            body_text="Shipment reference guide for domain two.",
            domain_name="OTM2",
            visibility="PRIVATE",
        ),
    )
    rebuild_assistant_fts_index(db_session)

    results = search_assistant_sources(
        db_session,
        query_text="shipment reference",
        allowed_domains=["PUBLIC", "OTM1"],
        limit=10,
    )

    assert [item["source_title"] for item in results] == ["OTM1 private help"]
    assert "OTM2" not in str(results)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_assistant_source_index.py -v`

Expected: FAIL with `ModuleNotFoundError` for `otm_workbench.assistant`.

- [ ] **Step 3: Create package marker**

Create `src/otm_workbench/assistant/__init__.py` with:

```python
"""Workbench Assistant backend package."""
```

- [ ] **Step 4: Implement service dataclass and chunk creation**

Add to `src/otm_workbench/assistant/services.py`:

```python
from dataclasses import dataclass
from hashlib import sha256
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from otm_workbench.models import AssistantChunk, AssistantIndexRun, AssistantSource, utcnow


@dataclass(frozen=True)
class AssistantSourceInput:
    title: str
    source_type: str
    source_uri: str = ""
    body_text: str = ""
    module_id: str | None = None
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    visibility: str = "PRIVATE"
    access_policy_id: str | None = None
    created_by: str | None = None


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def estimate_tokens(value: str) -> int:
    normalized = normalize_text(value)
    return 0 if not normalized else max(1, len(normalized.split()))


def chunk_text(value: str, *, max_words: int = 180) -> list[str]:
    words = normalize_text(value).split()
    if not words:
        return []
    return [" ".join(words[index : index + max_words]) for index in range(0, len(words), max_words)]


def create_assistant_source(db: Session, payload: AssistantSourceInput) -> AssistantSource:
    body_text = normalize_text(payload.body_text)
    source = AssistantSource(
        title=payload.title.strip(),
        source_type=payload.source_type.strip().upper(),
        source_uri=payload.source_uri.strip(),
        module_id=payload.module_id,
        project_id=payload.project_id,
        profile_id=payload.profile_id,
        environment_id=payload.environment_id,
        domain_name=payload.domain_name.upper() if payload.domain_name else None,
        visibility=payload.visibility.strip().upper(),
        access_policy_id=payload.access_policy_id,
        content_hash=sha256(body_text.encode("utf-8")).hexdigest() if body_text else "",
        created_by=payload.created_by,
    )
    db.add(source)
    db.flush()
    for index, chunk in enumerate(chunk_text(body_text)):
        db.add(
            AssistantChunk(
                source_id=source.id,
                chunk_index=index,
                heading=source.title,
                body_text=chunk,
                token_estimate=estimate_tokens(chunk),
            )
        )
    db.commit()
    db.refresh(source)
    return source
```

- [ ] **Step 5: Implement FTS table creation and rebuild**

Append to `src/otm_workbench/assistant/services.py`:

```python
def ensure_assistant_fts(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS assistant_chunks_fts
            USING fts5(chunk_id UNINDEXED, source_id UNINDEXED, title, heading, body_text)
            """
        )
    )


def rebuild_assistant_fts_index(db: Session) -> AssistantIndexRun:
    run = AssistantIndexRun(status="RUNNING", started_at=utcnow())
    db.add(run)
    db.flush()
    ensure_assistant_fts(db)
    db.execute(text("DELETE FROM assistant_chunks_fts"))
    chunks = (
        db.query(AssistantChunk, AssistantSource)
        .join(AssistantSource, AssistantSource.id == AssistantChunk.source_id)
        .filter(AssistantSource.status == "ACTIVE")
        .all()
    )
    for chunk, source in chunks:
        db.execute(
            text(
                """
                INSERT INTO assistant_chunks_fts(chunk_id, source_id, title, heading, body_text)
                VALUES (:chunk_id, :source_id, :title, :heading, :body_text)
                """
            ),
            {
                "chunk_id": chunk.id,
                "source_id": source.id,
                "title": source.title,
                "heading": chunk.heading,
                "body_text": chunk.body_text,
            },
        )
    run.status = "COMPLETED"
    run.source_count = len({source.id for _, source in chunks})
    run.chunk_count = len(chunks)
    run.message = "Assistant FTS index rebuilt."
    run.finished_at = utcnow()
    db.commit()
    db.refresh(run)
    return run
```

- [ ] **Step 6: Implement scoped search**

Append to `src/otm_workbench/assistant/services.py`:

```python
def search_assistant_sources(
    db: Session,
    *,
    query_text: str,
    allowed_domains: list[str],
    limit: int = 10,
) -> list[dict[str, object]]:
    ensure_assistant_fts(db)
    normalized_query = normalize_text(query_text)
    if not normalized_query:
        return []
    rows = db.execute(
        text(
            """
            SELECT
                fts.chunk_id,
                snippet(assistant_chunks_fts, 4, '<mark>', '</mark>', '...', 16) AS snippet,
                bm25(assistant_chunks_fts) AS rank
            FROM assistant_chunks_fts AS fts
            WHERE assistant_chunks_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
            """
        ),
        {"query": normalized_query, "limit": max(1, min(limit, 25))},
    ).mappings()
    allowed = {domain.upper() for domain in allowed_domains}
    results: list[dict[str, object]] = []
    for row in rows:
        chunk = db.get(AssistantChunk, row["chunk_id"])
        if chunk is None:
            continue
        source = db.get(AssistantSource, chunk.source_id)
        if source is None or source.status != "ACTIVE":
            continue
        source_domain = source.domain_name or "PUBLIC"
        if source.visibility != "PUBLIC" and source_domain.upper() not in allowed:
            continue
        results.append(
            {
                "source_id": source.id,
                "source_title": source.title,
                "source_type": source.source_type,
                "source_uri": source.source_uri,
                "module_id": source.module_id,
                "domain_name": source.domain_name,
                "visibility": source.visibility,
                "chunk_id": chunk.id,
                "snippet": row["snippet"],
                "rank": row["rank"],
            }
        )
    return results
```

- [ ] **Step 7: Run service tests**

Run: `pytest tests/test_assistant_source_index.py::test_assistant_service_chunks_and_searches_text tests/test_assistant_source_index.py::test_assistant_search_filters_private_domain_chunks -v`

Expected: PASS.

- [ ] **Step 8: Commit service foundation**

```bash
git add src/otm_workbench/assistant tests/test_assistant_source_index.py
git commit -m "feat: add assistant local search service"
```

## Task 3: Assistant API Routes

**Files:**
- Create: `src/otm_workbench/assistant/routes.py`
- Modify: `src/otm_workbench/main.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write the failing API tests**

```python
def test_assistant_health_requires_auth(client):
    response = client.get("/api/v1/assistant/health")

    assert response.status_code == 401


def test_assistant_source_create_rebuild_and_search_api(client, admin_header):
    source = client.post(
        "/api/v1/assistant/sources",
        headers=admin_header,
        json={
            "title": "Workbench rates guide",
            "source_type": "WORKBENCH_HELP",
            "source_uri": "workbench://rates/guide",
            "body_text": "Rate geo cost needs a rate record context.",
            "module_id": "rates",
            "domain_name": "OTM1",
            "visibility": "PRIVATE",
        },
    )
    rebuild = client.post("/api/v1/assistant/index/rebuild", headers=admin_header)
    search = client.get("/api/v1/assistant/search?query=rate+geo&limit=5", headers=admin_header)

    assert source.status_code == 201
    assert source.json()["title"] == "Workbench rates guide"
    assert rebuild.status_code == 200
    assert rebuild.json()["status"] == "COMPLETED"
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["source_title"] == "Workbench rates guide"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_assistant_source_index.py::test_assistant_health_requires_auth tests/test_assistant_source_index.py::test_assistant_source_create_rebuild_and_search_api -v`

Expected: FAIL with `404 Not Found` for `/api/v1/assistant/health`.

- [ ] **Step 3: Implement route module**

Create `src/otm_workbench/assistant/routes.py`:

```python
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from otm_workbench.assistant.services import (
    AssistantSourceInput,
    create_assistant_source,
    rebuild_assistant_fts_index,
    search_assistant_sources,
)
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import ActiveContext, User
from otm_workbench.platform.routes import allowed_domains_for_context

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


class AssistantSourceCreateRequest(BaseModel):
    title: str
    source_type: str
    source_uri: str = ""
    body_text: str = ""
    module_id: str | None = None
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    visibility: str = "PRIVATE"
    access_policy_id: str | None = None


class AssistantSearchResponseItem(BaseModel):
    source_id: str
    source_title: str
    source_type: str
    source_uri: str
    module_id: str | None = None
    domain_name: str | None = None
    visibility: str
    chunk_id: str
    snippet: str
    rank: float


def active_context_for_user(db: Session, user: User) -> ActiveContext | None:
    return db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()


@router.get("/health")
def assistant_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "assistant", "capabilities": ["source_index", "fts_search"]}


@router.post("/sources", status_code=status.HTTP_201_CREATED)
def create_source(
    request: AssistantSourceCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = active_context_for_user(db, user)
    source = create_assistant_source(
        db,
        AssistantSourceInput(
            title=request.title,
            source_type=request.source_type,
            source_uri=request.source_uri,
            body_text=request.body_text,
            module_id=request.module_id,
            project_id=request.project_id or (context.project_id if context else None),
            profile_id=request.profile_id or (context.profile_id if context else None),
            environment_id=request.environment_id or (context.environment_id if context else None),
            domain_name=request.domain_name or (context.domain_name if context else None),
            visibility=request.visibility,
            access_policy_id=request.access_policy_id,
            created_by=user.id,
        ),
    )
    return {
        "id": source.id,
        "title": source.title,
        "source_type": source.source_type,
        "source_uri": source.source_uri,
        "module_id": source.module_id,
        "domain_name": source.domain_name,
        "visibility": source.visibility,
        "status": source.status,
    }


@router.post("/index/rebuild")
def rebuild_index(db: Session = Depends(get_db), user: User = Depends(require_user)):
    run = rebuild_assistant_fts_index(db)
    return {
        "id": run.id,
        "status": run.status,
        "source_count": run.source_count,
        "chunk_count": run.chunk_count,
        "message": run.message,
    }


@router.get("/search", response_model=PageResponse[AssistantSearchResponseItem])
def search_sources(
    query: str = Field(min_length=1),
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = active_context_for_user(db, user)
    allowed_domains = allowed_domains_for_context(
        context.domain_name if context else None,
        bool(context and context.can_view_all_domains),
    )
    items = search_assistant_sources(db, query_text=query, allowed_domains=allowed_domains, limit=limit)
    return PageResponse(items=items, total=len(items), page=1, page_size=len(items))
```

- [ ] **Step 4: Register the router**

Modify `src/otm_workbench/main.py`:

```python
from otm_workbench.assistant.routes import router as assistant_router
```

Add inside `create_app()` with the other router includes:

```python
    app.include_router(assistant_router)
```

- [ ] **Step 5: Run API tests**

Run: `pytest tests/test_assistant_source_index.py::test_assistant_health_requires_auth tests/test_assistant_source_index.py::test_assistant_source_create_rebuild_and_search_api -v`

Expected: PASS.

- [ ] **Step 6: Commit API routes**

```bash
git add src/otm_workbench/assistant src/otm_workbench/main.py tests/test_assistant_source_index.py
git commit -m "feat: expose assistant source index api"
```

## Task 4: Scope And Navigation Regression Tests

**Files:**
- Modify: `tests/test_assistant_source_index.py`
- Modify: `tests/test_modules_navigation.py`

- [ ] **Step 1: Add active-context scope regression**

```python
def test_assistant_search_uses_active_context_domains(client, admin_header):
    context = client.post(
        "/api/v1/platform/active-context",
        headers=admin_header,
        json={"domain_name": "otm1"},
    )
    source = client.post(
        "/api/v1/assistant/sources",
        headers=admin_header,
        json={
            "title": "OTM2 private note",
            "source_type": "WORKBENCH_HELP",
            "body_text": "Private shipment lookup instructions.",
            "domain_name": "OTM2",
            "visibility": "PRIVATE",
        },
    )
    rebuild = client.post("/api/v1/assistant/index/rebuild", headers=admin_header)
    search = client.get("/api/v1/assistant/search?query=shipment", headers=admin_header)

    assert context.status_code == 200
    assert source.status_code == 201
    assert rebuild.status_code == 200
    assert search.status_code == 200
    assert search.json()["items"] == []
```

- [ ] **Step 2: Add navigation non-regression**

Append to `tests/test_modules_navigation.py`:

```python
def test_assistant_is_not_added_to_main_navigation(client, admin_header):
    response = client.get("/api/v1/platform/navigation", headers=admin_header)

    assert response.status_code == 200
    assert "assistant" not in [item["id"] for item in response.json()["items"]]
```

- [ ] **Step 3: Run regression tests**

Run: `pytest tests/test_assistant_source_index.py::test_assistant_search_uses_active_context_domains tests/test_modules_navigation.py::test_assistant_is_not_added_to_main_navigation -v`

Expected: PASS.

- [ ] **Step 4: Commit scope regressions**

```bash
git add tests/test_assistant_source_index.py tests/test_modules_navigation.py
git commit -m "test: cover assistant scope and navigation boundaries"
```

## Task 5: Validation Sweep

**Files:**
- No source files created in this task unless a previous test exposes a defect.

- [ ] **Step 1: Run focused assistant tests**

Run: `pytest tests/test_assistant_source_index.py -v`

Expected: PASS.

- [ ] **Step 2: Run navigation regression**

Run: `pytest tests/test_modules_navigation.py -v`

Expected: PASS.

- [ ] **Step 3: Run catalog smoke tests because Assistant reuses context and dictionary-adjacent patterns**

Run: `pytest tests/test_catalog_core.py -v`

Expected: PASS.

- [ ] **Step 4: Run static incompleteness scan on Assistant docs and code**

Run: `rg -n "T[O]DO|T[B]D|place[Hh]older|implement late[r]|fill i[n]" src/otm_workbench/assistant tests/test_assistant_source_index.py docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-source-index-foundation.md`

Expected: no output.

- [ ] **Step 5: Commit validation fixes if any were required**

If no files changed, skip this commit. If a fix was required:

```bash
git add src/otm_workbench/assistant tests/test_assistant_source_index.py tests/test_modules_navigation.py
git commit -m "fix: stabilize assistant source index foundation"
```

## Task 6: Planning Documentation Handoff

**Files:**
- Modify: `docs/agent/assistant-planning/README.md`
- Modify: `docs/agent/HANDOFF.md`

- [ ] **Step 1: Link the implementation plan from the Assistant planning README**

Add a short section:

```markdown
## Executable Plans

- [Source Index Foundation](../../superpowers/plans/2026-05-28-workbench-assistant-source-index-foundation.md) defines the first backend-only implementation slice. It keeps the assistant outside the main UI navigation while establishing local source metadata, SQLite FTS search, scoped result filtering, and API tests.
```

- [ ] **Step 2: Update the handoff capsule**

Add to `docs/agent/HANDOFF.md` under the current Workbench Assistant planning entry:

```markdown
- Added executable implementation plan for Phase 1 source index foundation:
  `docs/superpowers/plans/2026-05-28-workbench-assistant-source-index-foundation.md`.
- Code execution has not started. Next action is to choose subagent-driven execution or inline execution.
```

- [ ] **Step 3: Run documentation scan**

Run: `rg -n "T[O]DO|T[B]D|place[Hh]older|implement late[r]|fill i[n]" docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-source-index-foundation.md docs/agent/HANDOFF.md`

Expected: no output.

- [ ] **Step 4: Commit documentation handoff**

```bash
git add docs/agent/assistant-planning/README.md docs/agent/HANDOFF.md docs/superpowers/plans/2026-05-28-workbench-assistant-source-index-foundation.md
git commit -m "docs: plan assistant source index foundation"
```

## Self-Review

Spec coverage:
- Local and light: covered by SQLite FTS5, no LLM, no vector database.
- Separate from roadmap/UI: covered by router-only API and explicit navigation regression.
- Consultant-focused help source foundation: covered by source types, module links, Workbench help text, and scoped snippets.
- Client/domain/environment guardrails: covered by source metadata, active context defaulting, and private-domain filtering.
- Future Oracle docs and SQL helper compatibility: source metadata and search contracts provide the retrieval foundation, while the connectors themselves remain outside this slice.

Type consistency:
- `AssistantSourceInput`, `create_assistant_source`, `rebuild_assistant_fts_index`, and `search_assistant_sources` are introduced before route usage.
- `AssistantSource`, `AssistantChunk`, and `AssistantIndexRun` names match model imports and tests.
- API response item keys match service result dictionaries.

Residual risks for execution:
- SQLite FTS5 `MATCH` syntax can reject punctuation-heavy queries. The execution pass should add sanitization if tests expose this with real Workbench terms.
- Importing `allowed_domains_for_context` from `platform.routes` is acceptable for a first slice but may later move to `platform.scoping` if reuse grows.
- FTS virtual tables are outside SQLAlchemy metadata. Tests recreate normal tables automatically, while `ensure_assistant_fts()` creates the virtual table on first use.

## Execution Choice

Plan complete and saved to `docs/superpowers/plans/2026-05-28-workbench-assistant-source-index-foundation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - dispatch a fresh subagent per task and review between tasks for fast, isolated iteration.

**2. Inline Execution** - execute tasks in this session using executing-plans with checkpoints.

Recommended next answer: choose `Subagent-Driven` for implementation, or keep planning and create the next plan for the Oracle docs connector policy.
