from urllib.parse import quote_plus, urlparse
import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from otm_workbench.models import AssistantOracleDocCache, utcnow


def official_oracle_doc_domain(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        return None
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if host == "docs.oracle.com":
        return host
    if host == "www.oracle.com" and "/documentation/" in path:
        return host
    return None


def is_official_oracle_doc_url(url: str) -> bool:
    return official_oracle_doc_domain(url) is not None


def create_oracle_doc_cache(
    db: Session,
    *,
    title: str,
    url: str,
    product_area: str,
    topic: str,
    version_label: str,
    summary: str,
    created_by: str | None = None,
) -> AssistantOracleDocCache:
    source_domain = official_oracle_doc_domain(url)
    if source_domain is None:
        raise ValueError("Oracle docs cache entries must use an official Oracle documentation URL.")
    record = AssistantOracleDocCache(
        title=title.strip(),
        url=url.strip(),
        source_domain=source_domain,
        product_area=product_area.strip(),
        topic=topic.strip(),
        version_label=version_label.strip(),
        summary=summary.strip(),
        created_by=created_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def approve_oracle_doc_cache(
    db: Session,
    record_id: str,
    *,
    reviewed_by: str,
) -> AssistantOracleDocCache:
    record = db.get(AssistantOracleDocCache, record_id)
    if record is None:
        raise ValueError("Oracle docs cache record not found.")
    record.status = "APPROVED"
    record.reviewed_by = reviewed_by
    record.reviewed_at = utcnow()
    db.commit()
    db.refresh(record)
    return record


def serialize_oracle_doc_cache(record: AssistantOracleDocCache) -> dict[str, object]:
    return {
        "id": record.id,
        "title": record.title,
        "url": record.url,
        "source_domain": record.source_domain,
        "product_area": record.product_area,
        "topic": record.topic,
        "version_label": record.version_label,
        "summary": record.summary,
        "status": record.status,
        "reviewed_by": record.reviewed_by,
        "reviewed_at": record.reviewed_at.isoformat() if record.reviewed_at else None,
        "fetched_at": record.fetched_at.isoformat() if record.fetched_at else None,
    }


def search_oracle_doc_cache(
    db: Session,
    *,
    query_text: str = "",
    product_area: str | None = None,
    topic: str | None = None,
    include_draft: bool = False,
) -> list[dict[str, object]]:
    query = db.query(AssistantOracleDocCache)
    if not include_draft:
        query = query.filter(AssistantOracleDocCache.status == "APPROVED")
    if product_area:
        query = query.filter(AssistantOracleDocCache.product_area == product_area.strip())
    if topic:
        query = query.filter(AssistantOracleDocCache.topic == topic.strip())
    normalized = query_text.strip().lower()
    rows = query.order_by(AssistantOracleDocCache.updated_at.desc()).all()
    items = []
    for row in rows:
        haystack = f"{row.title} {row.product_area} {row.topic} {row.version_label} {row.summary} {row.url}".lower()
        if normalized and normalized not in haystack:
            continue
        items.append(serialize_oracle_doc_cache(row))
    return items


def blocked_live_lookup(query_text: str) -> dict[str, object]:
    return {
        "answer_type": "blocked",
        "summary": "Oracle documentation live lookup is not enabled yet.",
        "confidence": "high",
        "source_mode": "none",
        "cost_level": "web",
        "warnings": [
            "Use approved cached Oracle documentation links until the explicit web connector is implemented.",
            f"Requested query: {query_text.strip()}",
        ],
    }


URL_TOKEN_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
LONG_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9_-]{16,}\b")


def sanitize_oracle_doc_query(query_text: str, private_terms: list[str] | None = None) -> str:
    sanitized = query_text.strip()
    sanitized = URL_TOKEN_PATTERN.sub(" ", sanitized)
    sanitized = LONG_TOKEN_PATTERN.sub(" ", sanitized)
    for term in private_terms or []:
        cleaned = term.strip()
        if not cleaned:
            continue
        sanitized = re.sub(re.escape(cleaned), " ", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized


def oracle_search_links(sanitized_query: str) -> list[dict[str, str]]:
    encoded_query = quote_plus(sanitized_query)
    return [
        {
            "label": "Search official Oracle docs",
            "url": f"https://docs.oracle.com/search/?q={encoded_query}",
            "source_domain": "docs.oracle.com",
        }
    ]


def prepare_live_lookup_request(
    query_text: str,
    private_terms: list[str] | None = None,
) -> dict[str, object]:
    sanitized_query = sanitize_oracle_doc_query(query_text, private_terms)
    return {
        "answer_type": "lookup_request",
        "summary": "Oracle documentation lookup is prepared and requires an explicit web action.",
        "confidence": "high",
        "source_mode": "official_search_link",
        "cost_level": "web",
        "network_performed": False,
        "sanitized_query": sanitized_query,
        "actions": oracle_search_links(sanitized_query),
        "warnings": [
            "No external request was performed.",
            "Review the sanitized query before running a future live lookup.",
        ],
    }
