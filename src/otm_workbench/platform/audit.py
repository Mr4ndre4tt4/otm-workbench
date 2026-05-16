from sqlalchemy.orm import Session

from otm_workbench.models import AuditLog, User


def write_audit(
    db: Session,
    actor: User | None,
    action: str,
    target_type: str,
    target_id: str | None = None,
    metadata_json: str = "{}",
) -> AuditLog:
    record = AuditLog(
        actor_user_id=actor.id if actor else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata_json,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
