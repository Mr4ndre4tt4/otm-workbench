import re


SECRET_PATTERNS = [
    re.compile(r"\b(password|passwd|pwd|token|api[_-]?key|secret)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
]


def has_secret_risk_text(text: str) -> bool:
    if not text:
        return False
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def has_secret_risk_bytes(content: bytes) -> bool:
    if not content:
        return False
    sample = content[:65536].decode("utf-8", errors="ignore")
    return has_secret_risk_text(sample)


def metadata_has_secret_risk(payload: dict[str, object]) -> bool:
    values: list[str] = []
    for field_name in ("name", "description", "module_id", "macro_object_code", "otm_table_name"):
        value = payload.get(field_name)
        if value is not None:
            values.append(str(value))
    raw_tags = payload.get("tags") or []
    if isinstance(raw_tags, list):
        values.extend(str(tag) for tag in raw_tags)
    return has_secret_risk_text("\n".join(values))


def assert_global_asset_without_secret_risk(scope_type: str | None, payload: dict[str, object]) -> None:
    if (scope_type or "").strip().upper() == "GLOBAL" and metadata_has_secret_risk(payload):
        raise ValueError("Global assets cannot include secret-like metadata.")


def assert_global_content_without_secret_risk(scope_type: str | None, content: bytes) -> None:
    if (scope_type or "").strip().upper() == "GLOBAL" and has_secret_risk_bytes(content):
        raise ValueError("Global assets cannot include secret-like file content.")
