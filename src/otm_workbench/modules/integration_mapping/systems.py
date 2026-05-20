from collections.abc import Mapping

from otm_workbench.models import IntegrationEndpoint, IntegrationSystem, User


SECRET_MARKERS = ("password", "secret", "token", "api_key", "apikey", "credential", "authorization", "bearer")


def reject_secret_like_payload(payload: Mapping[str, object]) -> None:
    for key, value in payload.items():
        key_text = str(key).lower()
        value_text = str(value).lower() if value is not None else ""
        if any(marker in key_text or marker in value_text for marker in SECRET_MARKERS):
            raise ValueError("Integration metadata must not contain credentials or secret-like values.")


def normalize_code(value: str) -> str:
    return value.strip().upper()


def create_integration_system(db, *, payload: dict[str, object], user: User) -> IntegrationSystem:
    reject_secret_like_payload(payload)
    system = IntegrationSystem(
        code=normalize_code(str(payload["code"])),
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        system_type=normalize_code(str(payload["system_type"])),
        base_url=str(payload.get("base_url") or "").strip(),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


def create_integration_endpoint(
    db,
    *,
    system: IntegrationSystem,
    payload: dict[str, object],
    user: User,
) -> IntegrationEndpoint:
    reject_secret_like_payload(payload)
    endpoint = IntegrationEndpoint(
        system_id=system.id,
        code=normalize_code(str(payload["code"])),
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        path=str(payload["path"]).strip(),
        method=normalize_code(str(payload["method"])),
        payload_format=normalize_code(str(payload["payload_format"])),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


def serialize_integration_system(system: IntegrationSystem) -> dict[str, object]:
    return {
        "id": system.id,
        "code": system.code,
        "name": system.name,
        "description": system.description,
        "system_type": system.system_type,
        "base_url": system.base_url,
        "status": system.status,
        "created_by": system.created_by,
        "created_at": system.created_at.isoformat() if system.created_at else None,
        "updated_at": system.updated_at.isoformat() if system.updated_at else None,
    }


def serialize_integration_endpoint(endpoint: IntegrationEndpoint) -> dict[str, object]:
    return {
        "id": endpoint.id,
        "system_id": endpoint.system_id,
        "code": endpoint.code,
        "name": endpoint.name,
        "description": endpoint.description,
        "path": endpoint.path,
        "method": endpoint.method,
        "payload_format": endpoint.payload_format,
        "status": endpoint.status,
        "created_by": endpoint.created_by,
        "created_at": endpoint.created_at.isoformat() if endpoint.created_at else None,
        "updated_at": endpoint.updated_at.isoformat() if endpoint.updated_at else None,
    }
