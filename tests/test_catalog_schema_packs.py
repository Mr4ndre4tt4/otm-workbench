import json
import shutil
from pathlib import Path
from uuid import uuid4

from otm_workbench.models import (
    Evidence,
    JobEvent,
    MacroObjectSchemaLink,
    SchemaFile,
    SchemaPack,
    SchemaPath,
    SchemaRoot,
    ServiceOperation,
)


def workspace_test_folder(prefix: str) -> Path:
    root = Path("var/test_schema_packs")
    root.mkdir(parents=True, exist_ok=True)
    folder = root / f"{prefix}_{uuid4().hex}"
    if folder.exists():
        shutil.rmtree(folder)
    return folder


def write_synthetic_schema_pack(folder):
    folder.mkdir()
    (folder / "Order.xsd").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
  targetNamespace="http://xmlns.oracle.com/apps/otm">
  <xs:element name="Release" type="ReleaseType"/>
  <xs:complexType name="ReleaseType">
    <xs:sequence>
      <xs:element name="TransactionCode" type="xs:string" minOccurs="1" maxOccurs="1"/>
      <xs:element name="ReleaseLine" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="LineNumber" type="xs:string"/>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
""",
        encoding="utf-8",
    )
    (folder / "OrderReleaseService.wsdl").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<wsdl:definitions xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
  targetNamespace="http://xmlns.oracle.com/apps/otm/OrderReleaseService">
  <wsdl:service name="OrderReleaseService"/>
  <wsdl:portType name="OrderReleaseServicePortType">
    <wsdl:operation name="processAction">
      <wsdl:input message="tns:AgentMessage"/>
      <wsdl:output message="tns:AgentReplyMessage"/>
    </wsdl:operation>
  </wsdl:portType>
</wsdl:definitions>
""",
        encoding="utf-8",
    )


def write_sensitive_schema_pack(folder):
    folder.mkdir()
    (folder / "ExternalService.wsdl").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<wsdl:definitions xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
  targetNamespace="http://xmlns.oracle.com/apps/otm/ExternalService">
  <wsdl:service name="ExternalService">
    <wsdl:port name="ExternalPort" binding="tns:ExternalBinding">
      <soap:address location="https://real-client.example.com/otm/service"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""",
        encoding="utf-8",
    )


def write_wsdl_with_sanitizable_address(folder):
    folder.mkdir()
    (folder / "TransmissionService.wsdl").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<wsdl:definitions xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
  targetNamespace="http://xmlns.oracle.com/apps/otm/TransmissionService">
  <wsdl:service name="TransmissionService">
    <wsdl:port name="TransmissionPort" binding="tns:TransmissionBinding">
      <soap:address location="https://example.invalid/GC3Services/TransmissionService/call"/>
    </wsdl:port>
  </wsdl:service>
  <wsdl:portType name="TransmissionServicePortType">
    <wsdl:operation name="execute">
      <wsdl:input message="tns:Transmission"/>
      <wsdl:output message="tns:TransmissionAck"/>
    </wsdl:operation>
  </wsdl:portType>
</wsdl:definitions>
""",
        encoding="utf-8",
    )


def write_cross_file_schema_pack(folder):
    folder.mkdir()
    (folder / "Common.xsd").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
  targetNamespace="http://xmlns.oracle.com/apps/otm/common">
  <xs:complexType name="GidType">
    <xs:sequence>
      <xs:element name="DomainName" type="xs:string"/>
      <xs:element name="Xid" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
""",
        encoding="utf-8",
    )
    (folder / "Order.xsd").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns:common="http://xmlns.oracle.com/apps/otm/common"
  targetNamespace="http://xmlns.oracle.com/apps/otm/order">
  <xs:import namespace="http://xmlns.oracle.com/apps/otm/common" schemaLocation="Common.xsd"/>
  <xs:element name="Release" type="ReleaseType"/>
  <xs:complexType name="ReleaseType">
    <xs:sequence>
      <xs:element name="ReleaseGid" type="common:GidType"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
""",
        encoding="utf-8",
    )


def write_invalid_schema_pack(folder):
    folder.mkdir()
    (folder / "Broken.xsd").write_text(
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"Broken\"",
        encoding="utf-8",
    )


def write_missing_import_schema_pack(folder):
    folder.mkdir()
    (folder / "Order.xsd").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
  targetNamespace="http://xmlns.oracle.com/apps/otm/order">
  <xs:import namespace="http://xmlns.oracle.com/apps/otm/common" schemaLocation="MissingCommon.xsd"/>
  <xs:element name="Release" type="ReleaseType"/>
  <xs:complexType name="ReleaseType">
    <xs:sequence>
      <xs:element name="ReleaseGid" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
""",
        encoding="utf-8",
    )


def write_duplicate_root_schema_pack(folder):
    folder.mkdir()
    for file_name in ("OrderA.xsd", "OrderB.xsd"):
        (folder / file_name).write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
  targetNamespace="http://xmlns.oracle.com/apps/otm/order">
  <xs:element name="Release" type="xs:string"/>
</xs:schema>
""",
            encoding="utf-8",
        )


def test_catalog_schema_pack_create_and_list_is_client_safe(client, admin_header):
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_CORE",
            "name": "OTM 26A core contracts",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": "C:/otm/contracts/26A",
            "content_hash": "hash-26a",
        },
        headers=admin_header,
    )

    assert created.status_code == 200
    payload = created.json()
    assert payload["code"] == "OTM_26A_CORE"
    assert payload["otm_version"] == "26A"
    assert payload["status"] == "DRAFT"
    assert payload["root_count"] == 0
    assert "source_path" not in payload

    listed = client.get("/api/v1/catalog/schema-packs?otm_version=26A", headers=admin_header)

    assert listed.status_code == 200
    list_payload = listed.json()
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["code"] == "OTM_26A_CORE"
    assert "C:/otm/contracts/26A" not in str(list_payload)


def test_catalog_schema_pack_index_local_folder_extracts_roots_paths_operations_and_evidence(
    client,
    admin_header,
    db_session,
):
    schema_folder = workspace_test_folder("synthetic_26a")
    write_synthetic_schema_pack(schema_folder)
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_SYNTH",
            "name": "Synthetic OTM 26A pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(schema_folder),
            "content_hash": "synthetic-hash",
        },
        headers=admin_header,
    )

    indexed = client.post(f"/api/v1/catalog/schema-packs/{created.json()['id']}/index", headers=admin_header)

    assert indexed.status_code == 200
    index_payload = indexed.json()
    assert index_payload["status"] == "READY"
    assert index_payload["files_parsed"] == 2
    assert index_payload["roots_created"] == 1
    assert index_payload["paths_created"] == 4
    assert index_payload["operations_created"] == 1
    assert "source_path" not in str(index_payload)
    assert str(schema_folder) not in str(index_payload)

    roots = client.get("/api/v1/catalog/schema-roots?root_name=Release", headers=admin_header)
    paths = client.get(
        f"/api/v1/catalog/schema-roots/{roots.json()['items'][0]['id']}/paths",
        headers=admin_header,
    )
    operations = client.get(
        "/api/v1/catalog/schema-operations?service_name=OrderReleaseService",
        headers=admin_header,
    )
    evidence = db_session.get(Evidence, index_payload["evidence_id"])

    assert roots.json()["items"][0]["recommended_modules"] == [
        "order_release_generator",
        "integration_mapping",
    ]
    assert "/Release/ReleaseLine" in [item["path"] for item in paths.json()["items"]]
    assert "/Release/ReleaseLine/LineNumber" in [item["path"] for item in paths.json()["items"]]
    assert operations.json()["items"][0]["operation_name"] == "processAction"
    assert evidence is not None
    assert evidence.client_safe is True
    assert evidence.evidence_type == "schema_pack_index"
    summary = json.loads(evidence.summary_json)
    assert summary["schema_pack_code"] == "OTM_26A_SYNTH"
    assert summary["files_parsed"] == 2
    assert "source_path" not in summary


def test_catalog_schema_pack_index_rejects_missing_local_folder(client, admin_header):
    missing_folder = workspace_test_folder("missing")
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_MISSING",
            "name": "Missing OTM 26A pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(missing_folder),
        },
        headers=admin_header,
    )

    indexed = client.post(f"/api/v1/catalog/schema-packs/{created.json()['id']}/index", headers=admin_header)

    assert indexed.status_code == 400
    assert indexed.json()["code"] == "SCHEMA_PACK_SOURCE_NOT_FOUND"
    assert str(missing_folder) not in str(indexed.json())


def test_catalog_schema_pack_index_ignores_wsdl_soap_address_without_storing_location(
    client,
    admin_header,
):
    schema_folder = workspace_test_folder("address_26a")
    write_wsdl_with_sanitizable_address(schema_folder)
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_ADDRESS",
            "name": "Synthetic address pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(schema_folder),
        },
        headers=admin_header,
    )

    indexed = client.post(f"/api/v1/catalog/schema-packs/{created.json()['id']}/index", headers=admin_header)
    operations = client.get(
        "/api/v1/catalog/schema-operations?service_name=TransmissionService",
        headers=admin_header,
    )

    assert indexed.status_code == 200
    assert indexed.json()["operations_created"] == 1
    assert operations.status_code == 200
    assert operations.json()["items"][0]["operation_name"] == "execute"
    assert "example.invalid" not in str(indexed.json())
    assert "example.invalid" not in str(operations.json())


def test_catalog_schema_pack_index_resolves_cross_file_complex_type_paths(client, admin_header):
    schema_folder = workspace_test_folder("cross_file_26a")
    write_cross_file_schema_pack(schema_folder)
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_CROSS_FILE",
            "name": "Synthetic cross-file pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(schema_folder),
        },
        headers=admin_header,
    )

    indexed = client.post(f"/api/v1/catalog/schema-packs/{created.json()['id']}/index", headers=admin_header)
    roots = client.get("/api/v1/catalog/schema-roots?root_name=Release", headers=admin_header)
    paths = client.get(
        f"/api/v1/catalog/schema-roots/{roots.json()['items'][0]['id']}/paths",
        headers=admin_header,
    )

    assert indexed.status_code == 200
    assert indexed.json()["files_parsed"] == 2
    path_values = [item["path"] for item in paths.json()["items"]]
    assert "/Release/ReleaseGid" in path_values
    assert "/Release/ReleaseGid/DomainName" in path_values
    assert "/Release/ReleaseGid/Xid" in path_values


def test_catalog_schema_pack_index_rejects_sensitive_wsdl_content(client, admin_header):
    schema_folder = workspace_test_folder("sensitive_26a")
    write_sensitive_schema_pack(schema_folder)
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_SENSITIVE",
            "name": "Sensitive synthetic pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(schema_folder),
        },
        headers=admin_header,
    )

    indexed = client.post(f"/api/v1/catalog/schema-packs/{created.json()['id']}/index", headers=admin_header)

    assert indexed.status_code == 400
    assert indexed.json()["code"] == "SCHEMA_PACK_SENSITIVE_CONTENT"
    assert "real-client" not in str(indexed.json()).lower()
    assert str(schema_folder) not in str(indexed.json())


def test_catalog_schema_pack_index_marks_invalid_xsd_failed_with_client_safe_evidence(
    client,
    admin_header,
    db_session,
):
    schema_folder = workspace_test_folder("invalid_xsd_26a")
    write_invalid_schema_pack(schema_folder)
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_INVALID",
            "name": "Invalid synthetic pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(schema_folder),
        },
        headers=admin_header,
    )

    indexed = client.post(f"/api/v1/catalog/schema-packs/{created.json()['id']}/index", headers=admin_header)
    evidence = db_session.get(Evidence, indexed.json()["evidence_id"])

    assert indexed.status_code == 200
    assert indexed.json()["status"] == "FAILED"
    assert indexed.json()["files_failed"] == 1
    assert indexed.json()["files_parsed"] == 0
    assert str(schema_folder) not in str(indexed.json())
    assert evidence is not None
    summary = json.loads(evidence.summary_json)
    assert summary["status"] == "FAILED"
    assert "Broken.xsd" not in str(summary)


def test_catalog_schema_pack_index_marks_missing_import_failed(client, admin_header):
    schema_folder = workspace_test_folder("missing_import_26a")
    write_missing_import_schema_pack(schema_folder)
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_MISSING_IMPORT",
            "name": "Missing import synthetic pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(schema_folder),
        },
        headers=admin_header,
    )

    indexed = client.post(f"/api/v1/catalog/schema-packs/{created.json()['id']}/index", headers=admin_header)

    assert indexed.status_code == 200
    assert indexed.json()["status"] == "FAILED"
    assert indexed.json()["files_failed"] == 1
    assert indexed.json()["files_parsed"] == 0
    assert "MissingCommon.xsd" not in str(indexed.json())
    assert str(schema_folder) not in str(indexed.json())


def test_catalog_schema_pack_index_marks_duplicate_root_failed(client, admin_header):
    schema_folder = workspace_test_folder("duplicate_root_26a")
    write_duplicate_root_schema_pack(schema_folder)
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_DUPLICATE_ROOT",
            "name": "Duplicate root synthetic pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(schema_folder),
        },
        headers=admin_header,
    )

    indexed = client.post(f"/api/v1/catalog/schema-packs/{created.json()['id']}/index", headers=admin_header)

    assert indexed.status_code == 200
    assert indexed.json()["status"] == "FAILED"
    assert indexed.json()["files_failed"] == 1
    assert "Release" not in str(indexed.json())


def test_schema_pack_index_job_runs_through_jobs_processing(client, admin_header, db_session):
    schema_folder = workspace_test_folder("job_synthetic_26a")
    write_synthetic_schema_pack(schema_folder)
    pack = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_JOB",
            "name": "Synthetic job-indexed OTM 26A pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(schema_folder),
            "content_hash": "synthetic-hash",
        },
        headers=admin_header,
    ).json()

    job = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "SCHEMA_PACK_INDEX",
            "source_module": "catalog",
            "input": {"schema_pack_id": pack["id"]},
            "execute_now": True,
        },
        headers=admin_header,
    )

    assert job.status_code == 200
    payload = job.json()
    assert payload["status"] == "SUCCEEDED"
    assert payload["result"]["schema_pack_id"] == pack["id"]
    assert payload["result"]["roots_created"] == 1
    assert payload["result"]["paths_created"] == 4
    assert payload["result"]["evidence_id"]
    assert "source_path" not in str(payload["result"])
    assert str(schema_folder) not in str(payload)
    events = db_session.query(JobEvent).filter(JobEvent.job_id == payload["id"]).order_by(JobEvent.created_at).all()
    assert [event.event_type for event in events] == ["JOB_CREATED", "JOB_STARTED", "JOB_SUCCEEDED"]


def test_schema_pack_index_job_fails_safely_for_missing_pack(client, admin_header):
    job = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "SCHEMA_PACK_INDEX",
            "source_module": "catalog",
            "input": {"schema_pack_id": "missing-pack"},
            "execute_now": True,
        },
        headers=admin_header,
    )

    assert job.status_code == 200
    payload = job.json()
    assert payload["status"] == "FAILED"
    assert payload["error"]["code"] == "SCHEMA_PACK_JOB_FAILED"
    assert "missing-pack" not in payload["error"]["message"]
    assert payload["result"] == {}


def test_schema_pack_index_job_fails_safely_for_sensitive_content(client, admin_header):
    schema_folder = workspace_test_folder("job_sensitive_26a")
    write_sensitive_schema_pack(schema_folder)
    pack = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_JOB_SENSITIVE",
            "name": "Sensitive job pack",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": str(schema_folder),
        },
        headers=admin_header,
    ).json()

    job = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "SCHEMA_PACK_INDEX",
            "source_module": "catalog",
            "input": {"schema_pack_id": pack["id"]},
            "execute_now": True,
        },
        headers=admin_header,
    )

    assert job.status_code == 200
    payload = job.json()
    assert payload["status"] == "FAILED"
    assert payload["error"]["code"] == "SCHEMA_PACK_JOB_FAILED"
    assert "real-client" not in str(payload).lower()
    assert str(schema_folder) not in str(payload)
    assert payload["result"] == {}


def test_catalog_schema_roots_paths_and_operations_are_queryable(client, admin_header, db_session):
    pack = SchemaPack(
        code="OTM_26A_CORE",
        name="OTM 26A core contracts",
        otm_version="26A",
        source_type="LOCAL_FOLDER",
        source_path="C:/otm/contracts/26A",
        content_hash="hash-26a",
        status="READY",
        namespace_count=3,
        root_count=2,
        operation_count=1,
        created_by="admin@example.com",
    )
    db_session.add(pack)
    db_session.flush()
    schema_file = SchemaFile(
        schema_pack_id=pack.id,
        file_name="Order.xsd",
        relative_path="Order.xsd",
        file_type="XSD",
        namespace="http://xmlns.oracle.com/apps/otm",
        import_count=2,
        top_level_element_count=9,
        complex_type_count=49,
        status="PARSED",
    )
    db_session.add(schema_file)
    db_session.flush()
    root = SchemaRoot(
        schema_pack_id=pack.id,
        schema_file_id=schema_file.id,
        root_name="Release",
        namespace="http://xmlns.oracle.com/apps/otm",
        domain_area="ORDER",
        root_type="DOMAIN_ROOT",
        envelope_role="NONE",
        recommended_modules_json='["order_release_generator","integration_mapping"]',
        documentation="Synthetic docs only.",
    )
    db_session.add(root)
    db_session.flush()
    db_session.add_all(
        [
            SchemaPath(
                schema_root_id=root.id,
                parent_path=None,
                path="/Release",
                node_name="Release",
                data_type="ReleaseType",
                min_occurs="1",
                max_occurs="1",
                is_required=True,
                is_repeatable=False,
                documentation="Root release element.",
                source_file="Order.xsd",
                sequence_index=1,
            ),
            SchemaPath(
                schema_root_id=root.id,
                parent_path="/Release",
                path="/Release/ReleaseLine",
                node_name="ReleaseLine",
                data_type="ReleaseLineType",
                min_occurs="0",
                max_occurs="unbounded",
                is_required=False,
                is_repeatable=True,
                documentation="Release line collection.",
                source_file="Order.xsd",
                sequence_index=2,
            ),
        ]
    )
    db_session.add(
        ServiceOperation(
            schema_pack_id=pack.id,
            schema_file_id=schema_file.id,
            service_name="OrderReleaseService",
            operation_name="processAction",
            input_message="AgentMessage",
            output_message="AgentReplyMessage",
            fault_message="",
            target_namespace="http://xmlns.oracle.com/apps/otm/OrderReleaseService",
            related_roots_json='["Release"]',
        )
    )
    db_session.commit()

    roots = client.get(
        "/api/v1/catalog/schema-roots?recommended_module=order_release_generator",
        headers=admin_header,
    )
    paths = client.get(f"/api/v1/catalog/schema-roots/{root.id}/paths?query=ReleaseLine", headers=admin_header)
    operations = client.get("/api/v1/catalog/schema-operations?service_name=OrderReleaseService", headers=admin_header)

    assert roots.status_code == 200
    assert paths.status_code == 200
    assert operations.status_code == 200
    assert roots.json()["items"][0]["root_name"] == "Release"
    assert paths.json()["items"][0]["path"] == "/Release/ReleaseLine"
    assert paths.json()["items"][0]["is_repeatable"] is True
    assert operations.json()["items"][0]["operation_name"] == "processAction"
    assert "source_path" not in str(roots.json())
    assert "C:/otm/contracts/26A" not in str(operations.json())


def test_catalog_schema_roots_are_queryable_by_backend_owned_alias(client, admin_header, db_session):
    pack = SchemaPack(
        code="OTM_26A_CORE",
        name="OTM 26A core contracts",
        otm_version="26A",
        source_type="LOCAL_FOLDER",
        source_path="C:/otm/contracts/26A",
        content_hash="hash-26a",
        status="READY",
    )
    db_session.add(pack)
    db_session.flush()
    schema_file = SchemaFile(
        schema_pack_id=pack.id,
        file_name="Rate.xsd",
        relative_path="Rate.xsd",
        file_type="XSD",
        namespace="http://xmlns.oracle.com/apps/otm",
        status="PARSED",
    )
    db_session.add(schema_file)
    db_session.flush()
    db_session.add(
        SchemaRoot(
            schema_pack_id=pack.id,
            schema_file_id=schema_file.id,
            root_name="RATE_GEO",
            namespace="http://xmlns.oracle.com/apps/otm",
            domain_area="RATE",
            root_type="ROWSET",
            envelope_role="NONE",
            recommended_modules_json='["rates"]',
        )
    )
    db_session.commit()

    response = client.get("/api/v1/catalog/schema-roots?root_name=RateGeo", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["root_name"] == "RATE_GEO"
    assert payload["items"][0]["root_display_label"] == "Rate Record / Rate Geo"
    assert payload["items"][0]["canonical_root_name"] == "RATE_GEO"
    assert "RateGeo" in payload["items"][0]["schema_root_aliases"]
    assert payload["items"][0]["data_dictionary_family"] == "RATE_GEO"


def test_catalog_macro_object_schema_links_return_official_roots(client, admin_header, db_session):
    pack = SchemaPack(
        code="OTM_26A_CORE",
        name="OTM 26A core contracts",
        otm_version="26A",
        source_type="LOCAL_FOLDER",
        source_path="C:/otm/contracts/26A",
        content_hash="hash-26a",
        status="READY",
    )
    db_session.add(pack)
    db_session.flush()
    schema_file = SchemaFile(
        schema_pack_id=pack.id,
        file_name="Rate.xsd",
        relative_path="Rate.xsd",
        file_type="XSD",
        namespace="http://xmlns.oracle.com/apps/otm",
        status="PARSED",
    )
    db_session.add(schema_file)
    db_session.flush()
    root = SchemaRoot(
        schema_pack_id=pack.id,
        schema_file_id=schema_file.id,
        root_name="RATE_OFFERING",
        namespace="http://xmlns.oracle.com/apps/otm",
        domain_area="RATE",
        root_type="ROWSET",
        envelope_role="NONE",
        recommended_modules_json='["rates"]',
    )
    db_session.add(root)
    db_session.flush()
    db_session.add(
        MacroObjectSchemaLink(
            macro_object_code="RATE_OFFERING",
            schema_root_id=root.id,
            relationship_role="SEMANTIC_ROOT",
            confidence="HIGH",
            functional_confidence="ORACLE_OFFICIAL_PINNED",
            source_reference_status="PINNED",
            source_reference_label="Oracle Rate Offering",
            source_reference_url="https://docs.oracle.com/en/cloud/saas/transportation/26a/otmol/planning/rate_manager/create_rate_offering.htm?agt=index",
            notes="Rate.xsd top-level RATE_OFFERING root.",
        )
    )
    db_session.commit()

    response = client.get("/api/v1/catalog/macro-objects/RATE_OFFERING/schema-links", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["macro_object_code"] == "RATE_OFFERING"
    assert payload["total"] == 1
    assert payload["items"][0]["root_name"] == "RATE_OFFERING"
    assert payload["items"][0]["relationship_role"] == "SEMANTIC_ROOT"
    assert payload["items"][0]["confidence"] == "HIGH"
    assert payload["items"][0]["functional_confidence"] == "ORACLE_OFFICIAL_PINNED"
    assert payload["items"][0]["source_reference_status"] == "PINNED"
    assert payload["items"][0]["source_reference_label"] == "Oracle Rate Offering"
    assert payload["items"][0]["source_reference_url"].startswith("https://docs.oracle.com/")
    assert payload["items"][0]["root_display_label"] == "Rate Offering"
    assert payload["items"][0]["data_dictionary_family"] == "RATE_OFFERING"
