from sqlalchemy.orm import Session

from otm_workbench.models import AssetClassification


DEFAULT_CLASSIFICATIONS = [
    ("asset_type", "TEMPLATE", "Template", "Reusable project or module template.", 10),
    ("asset_type", "SPEC", "Specification", "Functional or technical specification.", 20),
    ("asset_type", "SAMPLE_PAYLOAD", "Sample Payload", "Synthetic sample payload.", 30),
    ("asset_category", "OTM_SETUP", "OTM Setup", "Setup-oriented OTM artifact.", 10),
    ("asset_category", "INTEGRATION", "Integration", "Integration-oriented artifact.", 20),
    ("asset_category", "TESTING", "Testing", "Testing support artifact.", 30),
    ("asset_visibility", "PROJECT", "Project", "Visible inside the active project.", 10),
    ("asset_visibility", "PROFILE", "Profile", "Visible inside the active profile.", 20),
    ("asset_visibility", "MODULE", "Module", "Visible inside one module context.", 30),
    ("asset_scope", "GLOBAL", "Global", "Reusable across project contexts when sensitivity allows.", 10),
    ("asset_scope", "PROJECT", "Project", "Scoped to one project.", 20),
    ("asset_scope", "MODULE", "Module", "Scoped to one module.", 30),
    ("asset_status", "DRAFT", "Draft", "Editable draft asset.", 10),
    ("asset_status", "ACTIVE", "Active", "Current usable asset.", 20),
    ("asset_status", "ARCHIVED", "Archived", "Retained but hidden from active use.", 30),
    ("asset_sensitivity", "PUBLIC", "Public", "Safe for general sharing.", 10),
    ("asset_sensitivity", "INTERNAL", "Internal", "Internal project material.", 20),
    ("asset_sensitivity", "SECRET", "Secret", "Potentially sensitive or credential-like material.", 30),
    ("asset_link_type", "MODULE", "Module", "Links an asset to a module.", 10),
    ("asset_link_type", "MACRO_OBJECT", "Macro Object", "Links an asset to an OTM macro-object.", 20),
    ("asset_link_type", "OTM_TABLE", "OTM Table", "Links an asset to an OTM table.", 30),
    ("asset_link_type", "ARTIFACT", "Artifact", "Links an asset to an artifact.", 40),
    ("asset_link_type", "EVIDENCE", "Evidence", "Links an asset to evidence.", 50),
    ("asset_link_type", "BATCH", "Batch", "Links an asset to a backend-owned operational batch.", 60),
    ("asset_link_type", "CHECKLIST", "Checklist", "Links an asset to a backend-owned cutover checklist.", 70),
]

ALLOWED_CLASSIFICATION_TYPES = {item[0] for item in DEFAULT_CLASSIFICATIONS}


def seed_asset_classifications(db: Session) -> None:
    existing = {
        (classification.classification_type, classification.code)
        for classification in db.query(AssetClassification).all()
    }
    for classification_type, code, name, description, sort_order in DEFAULT_CLASSIFICATIONS:
        if (classification_type, code) in existing:
            continue
        db.add(
            AssetClassification(
                classification_type=classification_type,
                code=code,
                name=name,
                description=description,
                sort_order=sort_order,
                system_protected=True,
                is_active=True,
            )
        )
    db.commit()


def serialize_asset_classification(classification: AssetClassification) -> dict[str, object]:
    return {
        "id": classification.id,
        "classification_type": classification.classification_type,
        "code": classification.code,
        "name": classification.name,
        "description": classification.description,
        "sort_order": classification.sort_order,
        "system_protected": classification.system_protected,
        "is_active": classification.is_active,
    }


def create_asset_classification(db: Session, payload: dict[str, object]) -> AssetClassification:
    seed_asset_classifications(db)
    classification_type = str(payload["classification_type"]).strip().lower()
    code = str(payload["code"]).strip().upper()
    if classification_type not in ALLOWED_CLASSIFICATION_TYPES:
        raise ValueError("Unsupported asset classification type.")
    if not code:
        raise ValueError("Asset classification code is required.")
    existing = (
        db.query(AssetClassification)
        .filter(AssetClassification.classification_type == classification_type)
        .filter(AssetClassification.code == code)
        .first()
    )
    if existing is not None:
        raise ValueError("Asset classification already exists.")
    classification = AssetClassification(
        classification_type=classification_type,
        code=code,
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        sort_order=int(payload.get("sort_order") or 0),
        system_protected=False,
        is_active=True,
    )
    db.add(classification)
    db.commit()
    db.refresh(classification)
    return classification


def update_asset_classification(
    db: Session,
    *,
    classification: AssetClassification,
    payload: dict[str, object],
) -> AssetClassification:
    if classification.system_protected:
        raise PermissionError("System-protected asset classifications cannot be changed.")
    if "name" in payload and payload["name"] is not None:
        classification.name = str(payload["name"]).strip()
    if "description" in payload and payload["description"] is not None:
        classification.description = str(payload["description"]).strip()
    if "sort_order" in payload and payload["sort_order"] is not None:
        classification.sort_order = int(payload["sort_order"])
    if "is_active" in payload and payload["is_active"] is not None:
        classification.is_active = bool(payload["is_active"])
    db.commit()
    db.refresh(classification)
    return classification


def grouped_asset_classifications(db: Session) -> list[dict[str, object]]:
    seed_asset_classifications(db)
    classifications = (
        db.query(AssetClassification)
        .filter(AssetClassification.is_active.is_(True))
        .order_by(
            AssetClassification.classification_type,
            AssetClassification.sort_order,
            AssetClassification.code,
        )
        .all()
    )
    groups: dict[str, list[dict[str, object]]] = {}
    for classification in classifications:
        groups.setdefault(classification.classification_type, []).append(
            serialize_asset_classification(classification)
        )
    return [
        {
            "classification_type": classification_type,
            "items": items,
            "total": len(items),
        }
        for classification_type, items in groups.items()
    ]
