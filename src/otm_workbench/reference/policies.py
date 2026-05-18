from dataclasses import dataclass


MUST_EXIST = "MUST_EXIST"
SHOULD_EXIST_ALLOW_NEW = "SHOULD_EXIST_ALLOW_NEW"
SUGGEST_ONLY = "SUGGEST_ONLY"
FREE_TEXT = "FREE_TEXT"

ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"


@dataclass(frozen=True)
class ReferenceValidationResult:
    valid: bool
    severity: str
    policy: str
    message: str
    object_type: str
    gid: str
    domain_name: str | None = None
