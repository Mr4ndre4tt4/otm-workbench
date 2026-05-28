from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from otm_workbench.models import Asset, AssetVersion, AssistantChunk, AssistantIndexRun, AssistantSource, utcnow


class AssistantSourceIndexError(ValueError):
    pass


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


@dataclass(frozen=True)
class AssistantMarkdownIndexResult:
    source_count: int
    chunk_count: int
    skipped_count: int


@dataclass(frozen=True)
class AssistantAssetIndexResult:
    source: AssistantSource
    content_indexed: bool
    chunk_count: int


TEXT_ASSET_CONTENT_TYPES = {
    "application/json",
    "application/xml",
    "text/csv",
    "text/markdown",
    "text/plain",
    "text/xml",
}
MAX_TEXT_ASSET_BYTES = 256 * 1024


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


def replace_assistant_source(db: Session, payload: AssistantSourceInput) -> AssistantSource:
    existing = db.query(AssistantSource).filter(AssistantSource.source_uri == payload.source_uri).all()
    for source in existing:
        db.query(AssistantChunk).filter(AssistantChunk.source_id == source.id).delete()
        db.delete(source)
    db.flush()
    return create_assistant_source(db, payload)


def safe_resolve_path(path: Path) -> Path:
    return path.expanduser().resolve()


def reject_blocked_source_path(root: Path) -> None:
    if any(part.upper() == "OTM_RESOURCES" for part in root.parts):
        raise AssistantSourceIndexError("OTM_RESOURCES is not an approved assistant source root.")


def require_allowlisted_root(root: Path, allowed_roots: list[Path]) -> Path:
    resolved_root = safe_resolve_path(root)
    reject_blocked_source_path(resolved_root)
    for allowed_root in allowed_roots:
        resolved_allowed = safe_resolve_path(allowed_root)
        try:
            resolved_root.relative_to(resolved_allowed)
            return resolved_root
        except ValueError:
            continue
    raise AssistantSourceIndexError("Assistant source root is not in the approved source allowlist.")


def markdown_title(path: Path, content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or path.stem.replace("-", " ").title()
    return path.stem.replace("-", " ").title()


def index_markdown_directory(
    db: Session,
    *,
    root: Path,
    allowed_roots: list[Path],
    module_id: str | None = None,
    visibility: str = "PUBLIC",
    created_by: str | None = None,
) -> AssistantMarkdownIndexResult:
    resolved_root = require_allowlisted_root(root, allowed_roots)
    source_count = 0
    chunk_count = 0
    skipped_count = 0
    for path in sorted(resolved_root.rglob("*.md")):
        if not path.is_file():
            skipped_count += 1
            continue
        reject_blocked_source_path(path.resolve())
        content = path.read_text(encoding="utf-8")
        normalized = normalize_text(content)
        if not normalized:
            skipped_count += 1
            continue
        relative_uri = path.resolve().relative_to(resolved_root).as_posix()
        before_chunks = db.query(AssistantChunk).count()
        create_assistant_source(
            db,
            AssistantSourceInput(
                title=markdown_title(path, content),
                source_type="WORKBENCH_DOC",
                source_uri=f"workbench-doc://{relative_uri}",
                body_text=content,
                module_id=module_id,
                visibility=visibility,
                created_by=created_by,
            ),
        )
        after_chunks = db.query(AssistantChunk).count()
        source_count += 1
        chunk_count += after_chunks - before_chunks
    return AssistantMarkdownIndexResult(source_count=source_count, chunk_count=chunk_count, skipped_count=skipped_count)


def asset_metadata_text(asset: Asset, version: AssetVersion) -> str:
    parts = [
        asset.name,
        asset.description,
        asset.asset_type,
        asset.category,
        asset.module_id or "",
        asset.macro_object_code or "",
        asset.otm_table_name or "",
        version.file_name,
        version.content_type,
    ]
    return "\n".join(part for part in parts if part)


def readable_asset_version_text(version: AssetVersion) -> str:
    if version.content_type not in TEXT_ASSET_CONTENT_TYPES:
        return ""
    if version.size_bytes > MAX_TEXT_ASSET_BYTES:
        return ""
    storage_path = safe_resolve_path(Path(version.storage_path))
    reject_blocked_source_path(storage_path)
    if not storage_path.exists() or not storage_path.is_file():
        return ""
    try:
        return storage_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def index_asset_source(db: Session, *, asset: Asset, version: AssetVersion) -> AssistantAssetIndexResult:
    version_text = readable_asset_version_text(version)
    body_text = "\n\n".join(part for part in [asset_metadata_text(asset, version), version_text] if normalize_text(part))
    source_uri = f"asset://{asset.id}/versions/{version.id}"
    before_chunks = db.query(AssistantChunk).count()
    source = replace_assistant_source(
        db,
        AssistantSourceInput(
            title=asset.name,
            source_type="ASSET",
            source_uri=source_uri,
            body_text=body_text,
            module_id=asset.module_id,
            project_id=asset.project_id,
            profile_id=asset.profile_id,
            environment_id=asset.environment_id,
            domain_name=asset.domain_name,
            visibility=asset.visibility,
            access_policy_id=asset.access_policy_id,
            created_by=asset.created_by,
        ),
    )
    after_chunks = db.query(AssistantChunk).count()
    return AssistantAssetIndexResult(source=source, content_indexed=bool(normalize_text(version_text)), chunk_count=after_chunks - before_chunks)


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


def search_assistant_sources(
    db: Session,
    *,
    query_text: str,
    allowed_domains: list[str],
    project_id: str | None = None,
    environment_id: str | None = None,
    profile_id: str | None = None,
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
    can_view_all_domains = "*" in allowed
    for row in rows:
        chunk = db.get(AssistantChunk, row["chunk_id"])
        if chunk is None:
            continue
        source = db.get(AssistantSource, chunk.source_id)
        if source is None or source.status != "ACTIVE":
            continue
        source_domain = source.domain_name or "PUBLIC"
        if source.visibility != "PUBLIC" and not can_view_all_domains and source_domain.upper() not in allowed:
            continue
        if source.visibility != "PUBLIC" and not can_view_all_domains:
            if source.project_id and source.project_id != project_id:
                continue
            if source.environment_id and source.environment_id != environment_id:
                continue
            if source.profile_id and source.profile_id != profile_id:
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
