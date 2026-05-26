import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/integration-mapping") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }
    }
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={[initialPath]}>
          <App />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

function platformPreferences() {
  return {
    theme_mode: "light",
    follow_system_theme: false,
    density: "comfortable",
    sidebar_mode: "expanded"
  };
}

function validIntegrationReadiness() {
  return {
    specification_ready: true,
    preview_executable: true,
    specification_blockers: [],
    preview_blockers: []
  };
}

function coveredScenarioPack() {
  return {
    code: "PS_TO_EXTERNAL_DELIVERY_NDD",
    name: "PlannedShipment to External Delivery",
    description: "Synthetic required target checklist.",
    missing_required_targets: [],
    required_targets: [
      { path: "$.NumeroViagem", covered: true, coverage_type: "mapping" },
      { path: "$.DataEmissao", covered: true, coverage_type: "mapping" },
      { path: "$.Entregas[]", covered: true, coverage_type: "loop" },
      { path: "$.Entregas[].NumeroDocumento", covered: true, coverage_type: "mapping" },
      { path: "$.Entregas[].ChaveAcesso", covered: true, coverage_type: "mapping" }
    ]
  };
}

function catalogSchemaRootsByRole(role: string) {
  const roots = {
    ENVELOPE_ONLY: [
      {
        id: "root_transmission",
        schema_pack_id: "pack_26a",
        schema_file_id: "file_transmission",
        root_name: "Transmission",
        root_display_label: "Transmission",
        canonical_root_name: "Transmission",
        schema_root_aliases: ["Transmission"],
        data_dictionary_family: "",
        schema_guidance_role: "ENVELOPE_ONLY",
        namespace: "http://xmlns.oracle.com/apps/otm/transmission",
        domain_area: "TRANSMISSION",
        root_type: "ENVELOPE",
        envelope_role: "TRANSMISSION",
        recommended_modules: ["integration_mapping"],
        documentation: "Synthetic official OTM transmission root."
      }
    ]
  };
  return {
    items: roots[role as keyof typeof roots] ?? [],
    total: roots[role as keyof typeof roots]?.length ?? 0,
    page: 1,
    page_size: roots[role as keyof typeof roots]?.length ?? 0
  };
}

function catalogSchemaRootPaths(schemaRootId: string, query = "") {
  const paths = {
    root_transmission: [
      {
        id: "catalog_path_shipment_gid",
        schema_root_id: "root_transmission",
        parent_path: "/Transmission/Shipment",
        path: "/Transmission/Shipment/ShipmentGid",
        node_name: "ShipmentGid",
        data_type: "complexType",
        min_occurs: "1",
        max_occurs: "1",
        is_required: true,
        is_repeatable: false,
        documentation: "Synthetic official shipment identifier path.",
        source_file: "Shipment.xsd",
        sequence_index: 10
      },
      {
        id: "catalog_path_planned_time",
        schema_root_id: "root_transmission",
        parent_path: "/Transmission/Shipment/StartDt",
        path: "/Transmission/Shipment/StartDt/PlannedTime",
        node_name: "PlannedTime",
        data_type: "string",
        min_occurs: "0",
        max_occurs: "1",
        is_required: false,
        is_repeatable: false,
        documentation: "Synthetic official planned time path.",
        source_file: "Shipment.xsd",
        sequence_index: 20
      }
    ]
  };
  const allItems = paths[schemaRootId as keyof typeof paths] ?? [];
  const items = query ? allItems.filter((item) => item.path.includes(query)) : allItems;
  return { items, total: items.length, page: 1, page_size: items.length };
}

describe("Functional Integration Mapping Studio journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("creates a definition, sample schemas, mapping, preview, and spec from backend APIs", async () => {
    const definitionRequests: unknown[] = [];
    const payloadRequests: unknown[] = [];
    const schemaRequests: string[] = [];
    const mappingRequests: unknown[] = [];
    const mappingSuggestionRequests: string[] = [];
    const deletedMappingRequests: string[] = [];
    const loopRequests: unknown[] = [];
    const joinRequests: unknown[] = [];
    const joinBindingRequests: unknown[] = [];
    const lookupRequests: unknown[] = [];
    const responseHandlerRequests: unknown[] = [];
    const artifactDownloadRequests: string[] = [];
    const actionRequests: string[] = [];
    const catalogRootRequests: string[] = [];
    const catalogPathRequests: string[] = [];
    const systemRequests: unknown[] = [];
    const endpointRequests: unknown[] = [];
    let definitions: Array<Record<string, unknown>> = [];
    let systems: Array<Record<string, unknown>> = [];
    const endpointsBySystem: Record<string, Array<Record<string, unknown>>> = {};
    let payloadArtifacts: Array<Record<string, unknown>> = [];
    let schemaDocuments: Array<Record<string, unknown>> = [];
    let mappings: Array<Record<string, unknown>> = [];
    let loops: Array<Record<string, unknown>> = [];
    let joins: Array<Record<string, unknown>> = [];
    let joinBindings: Array<Record<string, unknown>> = [];
    let lookups: Array<Record<string, unknown>> = [];
    let responseHandlers: Array<Record<string, unknown>> = [];
    let generatedArtifacts: Array<Record<string, unknown>> = [];
    const alternateDefinition = {
      id: "definition_2",
      code: "ALT_EXTERNAL_DELIVERY_UI",
      name: "Alternate External Delivery UI",
      description: "Synthetic alternate mapping definition.",
      source_system: "OTM",
      target_system: "EXTERNAL_DELIVERY_ALT",
      source_format: "XML",
      target_format: "JSON",
      status: "DRAFT",
      created_by: "admin@example.test",
      created_at: "2026-05-21T10:10:00",
      updated_at: "2026-05-21T10:10:00"
    };
    const NativeURL = URL;
    const createObjectURL = vi.fn(() => "blob:integration-mapping-artifact");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", Object.assign(NativeURL, { createObjectURL, revokeObjectURL }));
    const sourceSchemaNodes = [
      {
        id: "node_source_gid",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment",
        path: "/Transmission/Shipment/ShipmentGid",
        name: "ShipmentGid",
        node_type: "string",
        sequence_index: 3
      },
      {
        id: "node_source_planned_time",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment/StartDt",
        path: "/Transmission/Shipment/StartDt/PlannedTime",
        name: "PlannedTime",
        node_type: "string",
        sequence_index: 4
      },
      {
        id: "node_source_stop",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment",
        path: "/Transmission/Shipment/ShipmentStop",
        name: "ShipmentStop",
        node_type: "object",
        sequence_index: 4
      },
      {
        id: "node_source_stop_sequence",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment/ShipmentStop",
        path: "/Transmission/Shipment/ShipmentStop/StopSequence",
        name: "StopSequence",
        node_type: "number",
        sequence_index: 5
      },
      {
        id: "node_source_stop_ship_unit",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment/ShipmentStop/ShipmentStopDetail/ShipUnitGid/Gid",
        path: "/Transmission/Shipment/ShipmentStop/ShipmentStopDetail/ShipUnitGid/Gid/Xid",
        name: "Xid",
        node_type: "string",
        sequence_index: 6
      },
      {
        id: "node_source_ship_unit",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment",
        path: "/Transmission/Shipment/ShipUnit",
        name: "ShipUnit",
        node_type: "object",
        sequence_index: 7
      },
      {
        id: "node_source_ship_unit_gid",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment/ShipUnit/ShipUnitGid/Gid",
        path: "/Transmission/Shipment/ShipUnit/ShipUnitGid/Gid/Xid",
        name: "Xid",
        node_type: "string",
        sequence_index: 8
      },
      {
        id: "node_source_ship_unit_release",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment/ShipUnit/ShipUnitContent/ReleaseGid/Gid",
        path: "/Transmission/Shipment/ShipUnit/ShipUnitContent/ReleaseGid/Gid/Xid",
        name: "Xid",
        node_type: "string",
        sequence_index: 9
      },
      {
        id: "node_source_release",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment",
        path: "/Transmission/Shipment/Release",
        name: "Release",
        node_type: "object",
        sequence_index: 10
      },
      {
        id: "node_source_release_gid",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment/Release/ReleaseGid/Gid",
        path: "/Transmission/Shipment/Release/ReleaseGid/Gid/Xid",
        name: "Xid",
        node_type: "string",
        sequence_index: 11
      },
      {
        id: "node_source_release_refnum_value",
        schema_document_id: "schema_source",
        parent_path: "/Transmission/Shipment/Release/ReleaseRefnum",
        path: "/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue",
        name: "ReleaseRefnumValue",
        node_type: "string",
        sequence_index: 12
      }
    ];
    const targetSchemaNodes = [
      {
        id: "node_target_status",
        schema_document_id: "schema_target",
        parent_path: "$",
        path: "$.status",
        name: "status",
        node_type: "string",
        sequence_index: 2
      },
      {
        id: "node_target_issued_at",
        schema_document_id: "schema_target",
        parent_path: "$",
        path: "$.issuedAt",
        name: "issuedAt",
        node_type: "string",
        sequence_index: 3
      },
      {
        id: "node_target_shipment_id",
        schema_document_id: "schema_target",
        parent_path: "$.header",
        path: "$.header.shipmentId",
        name: "shipmentId",
        node_type: "string",
        sequence_index: 3
      },
      {
        id: "node_target_deliveries",
        schema_document_id: "schema_target",
        parent_path: "$",
        path: "$.deliveries[]",
        name: "deliveries",
        node_type: "array",
        sequence_index: 4
      },
      {
        id: "node_target_access_key",
        schema_document_id: "schema_target",
        parent_path: "$.header",
        path: "$.header.accessKey",
        name: "accessKey",
        node_type: "string",
        sequence_index: 5
      },
      {
        id: "node_target_filtered_access_key",
        schema_document_id: "schema_target",
        parent_path: "$.header",
        path: "$.header.filteredAccessKey",
        name: "filteredAccessKey",
        node_type: "string",
        sequence_index: 6
      },
      {
        id: "node_target_release_count",
        schema_document_id: "schema_target",
        parent_path: "$.header",
        path: "$.header.releaseCount",
        name: "releaseCount",
        node_type: "number",
        sequence_index: 7
      }
    ];

    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
              { id: "integration_mapping", label: "Integration Mapping Studio", path: "/integration-mapping", status: "ACTIVE" }
            ],
            total: 2,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.includes("/api/v1/catalog/schema-roots/root_transmission/paths")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        catalogPathRequests.push(url);
        const parsedUrl = new NativeURL(url, "http://localhost");
        return Promise.resolve(jsonResponse(catalogSchemaRootPaths("root_transmission", parsedUrl.searchParams.get("query") ?? "")));
      }
      if (url.includes("/api/v1/catalog/schema-roots")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        catalogRootRequests.push(url);
        const parsedUrl = new NativeURL(url, "http://localhost");
        const response = catalogSchemaRootsByRole(parsedUrl.searchParams.get("schema_guidance_role") ?? "");
        expect(response.total).toBe(1);
        return Promise.resolve(jsonResponse(response));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/transform-types")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                id: "transform_direct",
                code: "DIRECT",
                name: "Direct copy",
                description: "Copy value directly.",
                requires_expression: false,
                status: "ACTIVE",
                sequence_index: 1,
                system_seeded: true,
                created_at: "2026-05-21T10:00:00",
                updated_at: "2026-05-21T10:00:00"
              },
              {
                id: "transform_constant",
                code: "CONSTANT",
                name: "Constant value",
                description: "Use a controlled constant value.",
                requires_expression: true,
                status: "ACTIVE",
                sequence_index: 2,
                system_seeded: true,
                created_at: "2026-05-21T10:00:00",
                updated_at: "2026-05-21T10:00:00"
              },
              {
                id: "transform_date_format",
                code: "DATE_FORMAT",
                name: "Date format",
                description: "Declare date format conversion metadata.",
                requires_expression: true,
                status: "ACTIVE",
                sequence_index: 3,
                system_seeded: true,
                created_at: "2026-05-21T10:00:00",
                updated_at: "2026-05-21T10:00:00"
              },
              {
                id: "transform_filter_by_qualifier",
                code: "FILTER_BY_QUALIFIER",
                name: "Filter by qualifier",
                description: "Select a source value from a repeated collection.",
                requires_expression: true,
                status: "ACTIVE",
                sequence_index: 4,
                system_seeded: true,
                created_at: "2026-05-21T10:00:00",
                updated_at: "2026-05-21T10:00:00"
              },
              {
                id: "transform_count_distinct",
                code: "COUNT_DISTINCT",
                name: "Count distinct",
                description: "Count distinct source values from a collection.",
                requires_expression: true,
                status: "ACTIVE",
                sequence_index: 5,
                system_seeded: true,
                created_at: "2026-05-21T10:00:00",
                updated_at: "2026-05-21T10:00:00"
              }
            ],
            total: 5,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/systems")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          systemRequests.push(body);
          expect(body).toEqual({
            code: "EXT_DELIVERY_API_UI",
            name: "External Delivery API UI",
            system_type: "EXTERNAL_API",
            base_url: "https://api.example.test",
            description: "Synthetic external system metadata."
          });
          const system = {
            id: "system_1",
            ...body,
            code: "EXT_DELIVERY_API_UI",
            system_type: "EXTERNAL_API",
            status: "ACTIVE",
            created_by: "admin@example.test",
            created_at: "2026-05-21T09:00:00",
            updated_at: "2026-05-21T09:00:00"
          };
          systems = [system];
          endpointsBySystem.system_1 = [];
          return Promise.resolve(jsonResponse(system));
        }
        return Promise.resolve(jsonResponse({ items: systems, total: systems.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/systems/system_1/endpoints")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          endpointRequests.push(body);
          expect(body).toEqual({
            code: "CREATE_DELIVERY_UI",
            name: "Create Delivery UI",
            path: "/deliveries",
            method: "POST",
            payload_format: "JSON",
            description: "Synthetic endpoint metadata."
          });
          const endpoint = {
            id: "endpoint_1",
            system_id: "system_1",
            ...body,
            status: "ACTIVE",
            created_by: "admin@example.test",
            created_at: "2026-05-21T09:01:00",
            updated_at: "2026-05-21T09:01:00"
          };
          endpointsBySystem.system_1 = [endpoint];
          return Promise.resolve(jsonResponse(endpoint));
        }
        const items = endpointsBySystem.system_1 ?? [];
        return Promise.resolve(jsonResponse({ items, total: items.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          definitionRequests.push(body);
          expect(body).toEqual({
            code: "PS_TO_EXTERNAL_DELIVERY_UI",
            name: "Planned Shipment to External Delivery UI",
            description: "Synthetic UI mapping definition.",
            source_system: "OTM",
            target_system: "EXTERNAL_DELIVERY",
            source_format: "XML",
            target_format: "JSON"
          });
          const definition = {
            id: "definition_1",
            ...body,
            status: "DRAFT",
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:00:00",
            updated_at: "2026-05-21T10:00:00"
          };
          definitions = [definition, alternateDefinition];
          return Promise.resolve(jsonResponse(definition));
        }
        return Promise.resolve(jsonResponse({ items: definitions, total: definitions.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1")) {
        return Promise.resolve(jsonResponse(definitions[0]));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2")) {
        return Promise.resolve(jsonResponse(alternateDefinition));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/payload-artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          payloadRequests.push(body);
          const id = body.payload_role === "SOURCE_SAMPLE" ? "payload_source" : "payload_target";
          const artifact = {
            id,
            definition_id: "definition_1",
            artifact_id: `artifact_${id}`,
            payload_role: body.payload_role,
            payload_format: body.payload_format,
            file_name: body.file_name,
            description: body.description,
            content_type: body.payload_format === "XML" ? "application/xml" : "application/json",
            sha256: `sha_${id}`,
            size_bytes: String(body.content).length,
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:01:00",
            updated_at: "2026-05-21T10:01:00"
          };
          payloadArtifacts = [...payloadArtifacts, artifact];
          return Promise.resolve(jsonResponse(artifact));
        }
        return Promise.resolve(jsonResponse({ items: payloadArtifacts, total: payloadArtifacts.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/payload-artifacts/payload_source/schema-documents")) {
        schemaRequests.push(url);
        const source = {
          id: "schema_source",
          definition_id: "definition_1",
          payload_artifact_id: "payload_source",
          payload_format: "XML",
          root_name: "Transmission",
          node_count: 4,
          status: "PARSED",
          created_by: "admin@example.test",
          created_at: "2026-05-21T10:02:00",
          updated_at: "2026-05-21T10:02:00"
        };
        schemaDocuments = [...schemaDocuments.filter((item) => item.id !== source.id), source];
        return Promise.resolve(jsonResponse(source));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/payload-artifacts/payload_target/schema-documents")) {
        schemaRequests.push(url);
        const target = {
          id: "schema_target",
          definition_id: "definition_1",
          payload_artifact_id: "payload_target",
          payload_format: "JSON",
          root_name: "$",
          node_count: 4,
          status: "PARSED",
          created_by: "admin@example.test",
          created_at: "2026-05-21T10:02:00",
          updated_at: "2026-05-21T10:02:00"
        };
        schemaDocuments = [...schemaDocuments.filter((item) => item.id !== target.id), target];
        return Promise.resolve(jsonResponse(target));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/schema-documents")) {
        return Promise.resolve(jsonResponse({ items: schemaDocuments, total: schemaDocuments.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/schema-documents/schema_source/nodes")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ items: sourceSchemaNodes, total: sourceSchemaNodes.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/schema-documents/schema_target/nodes")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ items: targetSchemaNodes, total: targetSchemaNodes.length, page: 1, page_size: 50 }));
      }
      if (url.includes("/api/v1/modules/integration-mapping/definitions/") && url.includes("/mapping-suggestions")) {
        const requestUrl = new URL(url, "http://localhost");
        mappingSuggestionRequests.push(url);
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        expect(url).toContain("/api/v1/modules/integration-mapping/definitions/definition_1/mapping-suggestions");
        expect(requestUrl.searchParams.get("source_schema_document_id")).toBe("schema_source");
        expect(requestUrl.searchParams.get("target_schema_document_id")).toBe("schema_target");
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                id: "schema_source:/Transmission/Shipment/ShipmentGid->schema_target:$.header.shipmentId",
                definition_id: "definition_1",
                source_schema_document_id: "schema_source",
                target_schema_document_id: "schema_target",
                source_path: "/Transmission/Shipment/ShipmentGid",
                target_path: "$.header.shipmentId",
                transform_type: "DIRECT",
                confidence: 0.9,
                reason: "Normalized schema leaf names match: shipmentid"
              }
            ],
            total: 1,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/mappings")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          mappingRequests.push(body);
          if (body.target_path === "$.header.shipmentId") {
            expect(body).toEqual({
              source_schema_document_id: "schema_source",
              target_schema_document_id: "schema_target",
              source_path: "/Transmission/Shipment/ShipmentGid",
              target_path: "$.header.shipmentId",
              transform_type: "DIRECT",
              transform_config: {},
              description: "Synthetic direct mapping from shipment id.",
              sequence_index: 10
            });
          } else if (body.target_path === "$.header.accessKey") {
            expect(body).toEqual({
              source_schema_document_id: "schema_source",
              target_schema_document_id: "schema_target",
              source_path: "/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue",
              target_path: "$.header.accessKey",
              transform_type: "DIRECT",
              transform_config: { source_alias: "ship_unit_release" },
              description: "Synthetic alias-backed access key mapping.",
              sequence_index: 10
            });
          } else if (body.target_path === "$.status") {
            expect(body).toEqual({
              source_schema_document_id: "schema_source",
              target_schema_document_id: "schema_target",
              source_path: "/Transmission/Shipment/ShipmentGid",
              target_path: "$.status",
              transform_type: "CONSTANT",
              transform_config: { value: "ACCEPTED" },
              description: "Synthetic constant status mapping.",
              sequence_index: 10
            });
          } else if (body.target_path === "$.issuedAt") {
            expect(body).toEqual({
              source_schema_document_id: "schema_source",
              target_schema_document_id: "schema_target",
              source_path: "/Transmission/Shipment/StartDt/PlannedTime",
              target_path: "$.issuedAt",
              transform_type: "DATE_FORMAT",
              transform_config: {
                source_format: "OTM_GLOGDATE",
                target_format: "ISO8601",
                timezone_offset: "-03:00"
              },
              description: "Synthetic planned time ISO mapping.",
              sequence_index: 10
            });
          } else if (body.target_path === "$.header.filteredAccessKey") {
            expect(body).toEqual({
              source_schema_document_id: "schema_source",
              target_schema_document_id: "schema_target",
              source_path: "/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue",
              target_path: "$.header.filteredAccessKey",
              transform_type: "FILTER_BY_QUALIFIER",
              transform_config: {
                collection_path: "/Transmission/Shipment/Release/ReleaseRefnum",
                qualifier_path: "ReleaseRefnumQualifierGid/Gid/Xid",
                qualifier_value: "RFN_CHAVE_ACESSO",
                value_path: "ReleaseRefnumValue"
              },
              description: "Synthetic filtered access key mapping.",
              sequence_index: 10
            });
          } else {
            expect(body).toEqual({
              source_schema_document_id: "schema_source",
              target_schema_document_id: "schema_target",
              source_path: "/Transmission/Shipment/Release/ReleaseGid/Gid/Xid",
              target_path: "$.header.releaseCount",
              transform_type: "COUNT_DISTINCT",
              transform_config: {
                collection_path: "/Transmission/Shipment/Release",
                value_path: "ReleaseGid/Gid/Xid"
              },
              description: "Synthetic release count mapping.",
              sequence_index: 10
            });
          }
          const mapping = {
            id: `mapping_${mappingRequests.length}`,
            definition_id: "definition_1",
            ...body,
            status: "ACTIVE",
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:03:00",
            updated_at: "2026-05-21T10:03:00"
          };
          mappings = [...mappings, mapping];
          return Promise.resolve(jsonResponse(mapping));
        }
        return Promise.resolve(jsonResponse({ items: mappings, total: mappings.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/mappings/mapping_2") && init?.method === "DELETE") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        deletedMappingRequests.push(url);
        mappings = mappings.filter((mapping) => mapping.id !== "mapping_2");
        return Promise.resolve(jsonResponse({ deleted: true, id: "mapping_2", definition_id: "definition_1" }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/loops")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          loopRequests.push(body);
          expect(body).toEqual({
            source_schema_document_id: "schema_source",
            target_schema_document_id: "schema_target",
            source_collection_path: "/Transmission/Shipment/ShipmentStop",
            target_collection_path: "$.deliveries[]",
            name: "Synthetic delivery loop",
            description: "Synthetic delivery loop metadata.",
            sequence_index: 20
          });
          const loop = {
            id: "loop_1",
            definition_id: "definition_1",
            ...body,
            status: "ACTIVE",
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:04:00",
            updated_at: "2026-05-21T10:04:00"
          };
          loops = [loop];
          return Promise.resolve(jsonResponse(loop));
        }
        return Promise.resolve(jsonResponse({ items: loops, total: loops.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/joins")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          joinRequests.push(body);
          const join = {
            id: "join_1",
            definition_id: "definition_1",
            ...body,
            status: "ACTIVE",
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:05:00",
            updated_at: "2026-05-21T10:05:00"
          };
          joins = [join];
          return Promise.resolve(jsonResponse(join));
        }
        return Promise.resolve(jsonResponse({ items: joins, total: joins.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/join-bindings")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          joinBindingRequests.push(body);
          expect(body).toEqual({
            source_schema_document_id: "schema_source",
            root_collection_path: "/Transmission/Shipment/ShipmentStop",
            target_collection_path: "/Transmission/Shipment/Release",
            name: "Stop to release binding",
            description: "Synthetic two-hop binding metadata.",
            sequence_index: 35,
            hops: [
              {
                hop_sequence: 1,
                left_collection_path: "/Transmission/Shipment/ShipmentStop",
                left_value_path: "ShipmentStopDetail/ShipUnitGid/Gid/Xid",
                right_collection_path: "/Transmission/Shipment/ShipUnit",
                right_value_path: "ShipUnitGid/Gid/Xid",
                operator: "EQ",
                result_alias: "stop_ship_unit"
              },
              {
                hop_sequence: 2,
                left_collection_path: "/Transmission/Shipment/ShipUnit",
                left_value_path: "ShipUnitContent/ReleaseGid/Gid/Xid",
                right_collection_path: "/Transmission/Shipment/Release",
                right_value_path: "ReleaseGid/Gid/Xid",
                operator: "EQ",
                result_alias: "ship_unit_release"
              }
            ]
          });
          const binding = {
            id: "join_binding_1",
            definition_id: "definition_1",
            ...body,
            status: "ACTIVE",
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:05:30",
            updated_at: "2026-05-21T10:05:30"
          };
          joinBindings = [binding];
          return Promise.resolve(jsonResponse(binding));
        }
        return Promise.resolve(jsonResponse({ items: joinBindings, total: joinBindings.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/lookups")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          lookupRequests.push(body);
          const lookup = {
            id: "lookup_1",
            definition_id: "definition_1",
            ...body,
            status: "ACTIVE",
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:06:00",
            updated_at: "2026-05-21T10:06:00"
          };
          lookups = [lookup];
          return Promise.resolve(jsonResponse(lookup));
        }
        return Promise.resolve(jsonResponse({ items: lookups, total: lookups.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/response-handlers")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          responseHandlerRequests.push(body);
          expect(body).toEqual({
            target_schema_document_id: "schema_target",
            response_path: "$.status",
            success_condition: "EQUALS",
            expected_value: "ACCEPTED",
            outcome: "SUCCESS",
            name: "Accepted delivery response",
            description: "Synthetic response handler metadata.",
            sequence_index: 50
          });
          const handler = {
            id: "response_handler_1",
            definition_id: "definition_1",
            ...body,
            status: "ACTIVE",
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:06:30",
            updated_at: "2026-05-21T10:06:30"
          };
          responseHandlers = [handler];
          return Promise.resolve(jsonResponse(handler));
        }
        return Promise.resolve(jsonResponse({ items: responseHandlers, total: responseHandlers.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/validate")) {
        actionRequests.push("validate");
        return Promise.resolve(
          jsonResponse({
            is_valid: true,
            issue_count: 0,
            issues: [],
            readiness: validIntegrationReadiness(),
            scenario_pack: coveredScenarioPack()
          })
        );
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/preview")) {
        actionRequests.push("preview");
        generatedArtifacts = [
          {
            id: "artifact_preview",
            definition_id: "definition_1",
            source_module: "integration_mapping",
            artifact_type: "integration_preview",
            file_name: "integration_preview.json",
            content_type: "application/json",
            sha256: "sha_preview",
            size_bytes: 256,
            sensitivity_level: "internal",
            download_url:
              "/api/v1/modules/integration-mapping/definitions/definition_1/artifacts/artifact_preview/download"
          },
          ...generatedArtifacts.filter((artifact) => artifact.id !== "artifact_preview")
        ];
        return Promise.resolve(
          jsonResponse({
            artifact_id: "artifact_preview",
            job_id: "job_preview",
            validation: {
              is_valid: true,
              issue_count: 0,
              issues: [],
              readiness: validIntegrationReadiness(),
              scenario_pack: coveredScenarioPack()
            },
            preview: {
              scenario: { code: "planned_shipment_to_external_delivery" },
              entity_counts: { mappings: 1, loops: 0, joins: 0, lookups: 0 }
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/generate-spec")) {
        actionRequests.push("generate-spec");
        generatedArtifacts = [
          {
            id: "artifact_spec",
            definition_id: "definition_1",
            source_module: "integration_mapping",
            artifact_type: "integration_markdown_spec",
            file_name: "integration_mapping_spec.md",
            content_type: "text/markdown",
            sha256: "sha_spec",
            size_bytes: 512,
            sensitivity_level: "internal",
            download_url: "/api/v1/modules/integration-mapping/definitions/definition_1/artifacts/artifact_spec/download"
          },
          ...generatedArtifacts.filter((artifact) => artifact.id !== "artifact_spec")
        ];
        return Promise.resolve(
          jsonResponse({
            artifact_id: "artifact_spec",
            job_id: "job_spec",
            validation: {
              is_valid: true,
              issue_count: 0,
              issues: [],
              readiness: validIntegrationReadiness(),
              scenario_pack: coveredScenarioPack()
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ definition_id: "definition_1", items: generatedArtifacts, total: generatedArtifacts.length }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/payload-artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ items: [], total: 0, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/schema-documents")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ items: [], total: 0, page: 1, page_size: 50 }));
      }
      if (
        url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/mappings") ||
        url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/loops") ||
        url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/joins") ||
        url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/join-bindings") ||
        url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/lookups") ||
        url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/response-handlers")
      ) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ items: [], total: 0, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ definition_id: "definition_2", items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/artifacts/artifact_spec/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        artifactDownloadRequests.push(url);
        return Promise.resolve(
          new Response(new Blob(["# Synthetic Integration Mapping Spec"], { type: "text/markdown" }), {
            status: 200,
            headers: {
              "Content-Disposition": 'attachment; filename="integration_mapping_spec.md"',
              "Content-Type": "text/markdown"
            }
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Integration Mapping Studio" });
    expect(screen.getByLabelText("Integration Mapping workflow")).toBeInTheDocument();
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("Select definition");
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("BLOCKED");
    expect(screen.getByLabelText("Integration system authoring")).toBeInTheDocument();
    expect(screen.queryByLabelText("Integration definition authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration payload and schema authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration mapping authoring")).not.toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("System code"), "EXT_DELIVERY_API_UI");
    await userEvent.type(screen.getByLabelText("System name"), "External Delivery API UI");
    await userEvent.selectOptions(screen.getByLabelText("System type"), "EXTERNAL_API");
    await userEvent.type(screen.getByLabelText("System base URL"), "https://api.example.test");
    await userEvent.type(screen.getByLabelText("System description"), "Synthetic external system metadata.");
    await userEvent.click(screen.getByRole("button", { name: "Create system" }));
    await waitFor(() => expect(systemRequests).toHaveLength(1));
    expect(await within(await screen.findByLabelText("Integration systems")).findByText("EXT_DELIVERY_API_UI")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Endpoint system"), "system_1");
    await userEvent.type(screen.getByLabelText("Endpoint code"), "CREATE_DELIVERY_UI");
    await userEvent.type(screen.getByLabelText("Endpoint name"), "Create Delivery UI");
    await userEvent.type(screen.getByLabelText("Endpoint path"), "/deliveries");
    await userEvent.selectOptions(screen.getByLabelText("Endpoint method"), "POST");
    await userEvent.selectOptions(screen.getByLabelText("Endpoint payload format"), "JSON");
    await userEvent.type(screen.getByLabelText("Endpoint description"), "Synthetic endpoint metadata.");
    await userEvent.click(screen.getByRole("button", { name: "Create endpoint" }));
    await waitFor(() => expect(endpointRequests).toHaveLength(1));
    expect(await within(await screen.findByLabelText("Integration endpoints")).findByText("CREATE_DELIVERY_UI")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /2Definition/ }));
    expect(screen.getByLabelText("Integration definition authoring")).toBeInTheDocument();
    expect(screen.queryByLabelText("Integration system authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration payload and schema authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration mapping authoring")).not.toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Definition code"), "PS_TO_EXTERNAL_DELIVERY_UI");
    await userEvent.type(screen.getByLabelText("Definition name"), "Planned Shipment to External Delivery UI");
    await userEvent.type(screen.getByLabelText("Source system"), "OTM");
    await userEvent.type(screen.getByLabelText("Target system"), "EXTERNAL_DELIVERY");
    await userEvent.selectOptions(screen.getByLabelText("Source format"), "XML");
    await userEvent.selectOptions(screen.getByLabelText("Target format"), "JSON");
    await userEvent.type(screen.getByLabelText("Definition description"), "Synthetic UI mapping definition.");
    await userEvent.click(screen.getByRole("button", { name: "Create definition" }));

    await waitFor(() => expect(definitionRequests).toHaveLength(1));
    expect((await screen.findAllByText("PS_TO_EXTERNAL_DELIVERY_UI")).length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("Create payload samples");
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("NEXT");

    await userEvent.click(screen.getByRole("button", { name: /3Payloads & schemas/ }));
    expect(screen.getByLabelText("Integration payload and schema authoring")).toBeInTheDocument();
    expect(screen.queryByLabelText("Integration system authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration definition authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration mapping authoring")).not.toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Payload role"), "SOURCE_SAMPLE");
    await userEvent.selectOptions(screen.getByLabelText("Payload format"), "XML");
    await userEvent.type(screen.getByLabelText("Payload file name"), "planned_shipment_manual.xml");
    await userEvent.type(screen.getByLabelText("Payload description"), "Synthetic manual source payload.");
    fireEvent.change(screen.getByLabelText("Payload content"), {
      target: {
        value:
          "<Transmission><Shipment><ShipmentGid>DEMO.SHIPMENT_001</ShipmentGid><ShipmentStop><StopSequence>1</StopSequence></ShipmentStop></Shipment></Transmission>"
      }
    });
    await userEvent.click(screen.getByRole("button", { name: "Create payload and schema" }));
    await screen.findByText("Payload planned_shipment_manual.xml and schema Transmission created.");

    await userEvent.selectOptions(screen.getByLabelText("Payload role"), "TARGET_SAMPLE");
    await userEvent.selectOptions(screen.getByLabelText("Payload format"), "JSON");
    await userEvent.type(screen.getByLabelText("Payload file name"), "external_delivery_manual.json");
    await userEvent.type(screen.getByLabelText("Payload description"), "Synthetic manual target payload.");
    fireEvent.change(screen.getByLabelText("Payload content"), {
      target: { value: '{"header":{"shipmentId":"DEMO"},"deliveries":[{"sequence":1}]}' }
    });
    await userEvent.click(screen.getByRole("button", { name: "Create payload and schema" }));
    await screen.findByText("Payload external_delivery_manual.json and schema $ created.");

    await waitFor(() => expect(payloadRequests).toHaveLength(2));
    await waitFor(() => expect(schemaRequests).toHaveLength(2));
    expect(payloadRequests).toEqual([
      {
        payload_role: "SOURCE_SAMPLE",
        payload_format: "XML",
        file_name: "planned_shipment_manual.xml",
        content:
          "<Transmission><Shipment><ShipmentGid>DEMO.SHIPMENT_001</ShipmentGid><ShipmentStop><StopSequence>1</StopSequence></ShipmentStop></Shipment></Transmission>",
        description: "Synthetic manual source payload."
      },
      {
        payload_role: "TARGET_SAMPLE",
        payload_format: "JSON",
        file_name: "external_delivery_manual.json",
        content: '{"header":{"shipmentId":"DEMO"},"deliveries":[{"sequence":1}]}',
        description: "Synthetic manual target payload."
      }
    ]);
    expect(await within(await screen.findByLabelText("Selected definition schema documents")).findByText("Transmission")).toBeInTheDocument();
    expect(await within(await screen.findByLabelText("Selected definition schema documents")).findByText("$")).toBeInTheDocument();
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("Create mapping rules");

    await userEvent.click(screen.getByRole("button", { name: /4Mapping rules/ }));
    expect(screen.getByLabelText("Integration mapping authoring")).toBeInTheDocument();
    expect(screen.queryByLabelText("Integration system authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration definition authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration payload and schema authoring")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Source schema"), { target: { value: "schema_source" } });
    fireEvent.change(screen.getByLabelText("Target schema"), { target: { value: "schema_target" } });
    expect(screen.getByLabelText("Source schema")).toHaveValue("schema_source");
    expect(screen.getByLabelText("Target schema")).toHaveValue("schema_target");
    await waitFor(() =>
      expect(catalogRootRequests.some((requestUrl) => requestUrl.includes("schema_guidance_role=ENVELOPE_ONLY"))).toBe(true)
    );
    await waitFor(() =>
      expect(within(screen.getByLabelText("Official source root")).getByRole("option", { name: "Transmission" })).toBeInTheDocument()
    );
    await userEvent.selectOptions(screen.getByLabelText("Official source root"), "root_transmission");
    await userEvent.type(screen.getByLabelText("Official source path search"), "ShipmentGid");
    const officialSourcePaths = await screen.findByLabelText("Official source paths");
    expect(officialSourcePaths).toHaveTextContent("Required");
    expect(officialSourcePaths).toHaveTextContent("Single");
    expect(officialSourcePaths).toHaveTextContent("Synthetic official shipment identifier path.");
    await userEvent.click(await screen.findByRole("button", { name: "Use official source path /Transmission/Shipment/ShipmentGid" }));
    expect(screen.getByLabelText("Source path")).toHaveValue("/Transmission/Shipment/ShipmentGid");
    expect(catalogPathRequests.some((requestUrl) => requestUrl.endsWith("/paths?query=ShipmentGid"))).toBe(true);
    await userEvent.type(await screen.findByLabelText("Mapping source node search"), "shipment");
    await userEvent.type(await screen.findByLabelText("Mapping target node search"), "shipment");
    await userEvent.selectOptions(await screen.findByLabelText("Mapping source node", { exact: true }), "/Transmission/Shipment/ShipmentGid");
    await userEvent.selectOptions(await screen.findByLabelText("Mapping target node", { exact: true }), "$.header.shipmentId");
    fireEvent.change(screen.getByLabelText("Mapping source node search"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("Mapping target node search"), { target: { value: "" } });
    expect(screen.getByLabelText("Source path")).toHaveValue("/Transmission/Shipment/ShipmentGid");
    expect(screen.getByLabelText("Target path")).toHaveValue("$.header.shipmentId");
    expect(screen.getByLabelText("Transform type")).toHaveValue("DIRECT");
    await userEvent.selectOptions(screen.getByLabelText("Transform type"), "DIRECT");
    await userEvent.type(screen.getByLabelText("Mapping description"), "Synthetic direct mapping from shipment id.");
    await userEvent.click(screen.getByRole("button", { name: "Create mapping" }));

    await waitFor(() => expect(mappingRequests).toHaveLength(1));
    expect(await within(await screen.findByLabelText("Selected definition mappings")).findByText("$.header.shipmentId")).toBeInTheDocument();
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("Validate definition");
    const reviewPanelAfterMapping = await screen.findByLabelText("Integration mapping grouped executable review");
    expect(reviewPanelAfterMapping).toHaveTextContent("Header");
    expect(reviewPanelAfterMapping).toHaveTextContent("$.header.shipmentId");
    expect(reviewPanelAfterMapping).toHaveTextContent("DIRECT");

    await userEvent.selectOptions(screen.getByLabelText("Loop source schema"), "schema_source");
    await userEvent.selectOptions(screen.getByLabelText("Loop target schema"), "schema_target");
    await userEvent.type(screen.getByLabelText("Loop name"), "Synthetic delivery loop");
    await userEvent.selectOptions(await screen.findByLabelText("Loop source node"), "/Transmission/Shipment/ShipmentStop");
    await userEvent.selectOptions(await screen.findByLabelText("Loop target node"), "$.deliveries[]");
    expect(screen.getByLabelText("Loop source collection path")).toHaveValue("/Transmission/Shipment/ShipmentStop");
    expect(screen.getByLabelText("Loop target collection path")).toHaveValue("$.deliveries[]");
    await userEvent.type(screen.getByLabelText("Loop description"), "Synthetic delivery loop metadata.");
    await userEvent.click(screen.getByRole("button", { name: "Create loop" }));
    await waitFor(() => expect(loopRequests).toHaveLength(1));
    expect(await within(await screen.findByLabelText("Selected definition loops")).findByText("Synthetic delivery loop")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Join source schema"), "schema_source");
    await userEvent.type(screen.getByLabelText("Join name"), "Synthetic shipment stop join");
    await userEvent.selectOptions(await screen.findByLabelText("Join left node"), "/Transmission/Shipment/ShipmentGid");
    await userEvent.selectOptions(await screen.findByLabelText("Join right node"), "/Transmission/Shipment/ShipmentStop/StopSequence");
    expect(screen.getByLabelText("Join left path")).toHaveValue("/Transmission/Shipment/ShipmentGid");
    expect(screen.getByLabelText("Join right path")).toHaveValue("/Transmission/Shipment/ShipmentStop/StopSequence");
    await userEvent.selectOptions(screen.getByLabelText("Join operator"), "EQ");
    await userEvent.type(screen.getByLabelText("Join description"), "Synthetic join metadata.");
    await userEvent.click(screen.getByRole("button", { name: "Create join" }));
    await waitFor(() => expect(joinRequests).toHaveLength(1));
    expect(await within(await screen.findByLabelText("Selected definition joins")).findByText("Synthetic shipment stop join")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Join binding source schema"), "schema_source");
    await userEvent.type(screen.getByLabelText("Join binding name"), "Stop to release binding");
    await userEvent.selectOptions(await screen.findByLabelText("Join binding root collection"), "/Transmission/Shipment/ShipmentStop");
    await userEvent.selectOptions(await screen.findByLabelText("Join binding target collection"), "/Transmission/Shipment/Release");
    await userEvent.selectOptions(await screen.findByLabelText("Hop 1 left collection"), "/Transmission/Shipment/ShipmentStop");
    await userEvent.type(screen.getByLabelText("Hop 1 left value path"), "ShipmentStopDetail/ShipUnitGid/Gid/Xid");
    await userEvent.selectOptions(await screen.findByLabelText("Hop 1 right collection"), "/Transmission/Shipment/ShipUnit");
    await userEvent.type(screen.getByLabelText("Hop 1 right value path"), "ShipUnitGid/Gid/Xid");
    await userEvent.type(screen.getByLabelText("Hop 1 result alias"), "stop_ship_unit");
    await userEvent.selectOptions(await screen.findByLabelText("Hop 2 left collection"), "/Transmission/Shipment/ShipUnit");
    await userEvent.type(screen.getByLabelText("Hop 2 left value path"), "ShipUnitContent/ReleaseGid/Gid/Xid");
    await userEvent.selectOptions(await screen.findByLabelText("Hop 2 right collection"), "/Transmission/Shipment/Release");
    await userEvent.type(screen.getByLabelText("Hop 2 right value path"), "ReleaseGid/Gid/Xid");
    await userEvent.type(screen.getByLabelText("Hop 2 result alias"), "ship_unit_release");
    await userEvent.type(screen.getByLabelText("Join binding description"), "Synthetic two-hop binding metadata.");
    await userEvent.click(screen.getByRole("button", { name: "Create join binding" }));
    await waitFor(() => expect(joinBindingRequests).toHaveLength(1));
    expect(await within(await screen.findByLabelText("Selected definition join bindings")).findByText("Stop to release binding")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Alias source context"), "ship_unit_release");
    await userEvent.selectOptions(
      await screen.findByLabelText("Mapping source node"),
      "/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue"
    );
    await userEvent.selectOptions(await screen.findByLabelText("Mapping target node"), "$.header.accessKey");
    await userEvent.type(screen.getByLabelText("Mapping description"), "Synthetic alias-backed access key mapping.");
    await userEvent.click(screen.getByRole("button", { name: "Create mapping" }));
    await waitFor(() => expect(mappingRequests).toHaveLength(2));
    expect(await within(await screen.findByLabelText("Selected definition mappings")).findByText("$.header.accessKey")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Remove mapping $.header.accessKey" }));
    await waitFor(() => expect(deletedMappingRequests).toHaveLength(1));
    expect(await screen.findByText("Removed mapping $.header.accessKey.")).toBeInTheDocument();
    expect(within(await screen.findByLabelText("Selected definition mappings")).queryByText("$.header.accessKey")).not.toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Alias source context"), "ship_unit_release");
    await userEvent.selectOptions(
      await screen.findByLabelText("Mapping source node"),
      "/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue"
    );
    await userEvent.selectOptions(await screen.findByLabelText("Mapping target node"), "$.header.accessKey");
    await userEvent.type(screen.getByLabelText("Mapping description"), "Synthetic alias-backed access key mapping.");
    await userEvent.click(screen.getByRole("button", { name: "Create mapping" }));
    await waitFor(() => expect(mappingRequests).toHaveLength(3));
    expect(await within(await screen.findByLabelText("Selected definition mappings")).findByText("$.header.accessKey")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Mapping source node"), "/Transmission/Shipment/ShipmentGid");
    await userEvent.selectOptions(screen.getByLabelText("Mapping target node"), "$.status");
    await userEvent.selectOptions(screen.getByLabelText("Transform type"), "CONSTANT");
    await userEvent.type(await screen.findByLabelText("Constant value"), "ACCEPTED");
    await userEvent.type(screen.getByLabelText("Mapping description"), "Synthetic constant status mapping.");
    await userEvent.click(screen.getByRole("button", { name: "Create mapping" }));
    await waitFor(() => expect(mappingRequests).toHaveLength(4));
    expect(await within(await screen.findByLabelText("Selected definition mappings")).findByText("$.status")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Mapping source node"), "/Transmission/Shipment/StartDt/PlannedTime");
    await userEvent.selectOptions(screen.getByLabelText("Mapping target node"), "$.issuedAt");
    await userEvent.selectOptions(screen.getByLabelText("Transform type"), "DATE_FORMAT");
    expect(screen.getByLabelText("Date source format")).toHaveValue("OTM_GLOGDATE");
    expect(screen.getByLabelText("Date target format")).toHaveValue("ISO8601");
    expect(screen.getByLabelText("Date timezone offset")).toHaveValue("-03:00");
    await userEvent.type(screen.getByLabelText("Mapping description"), "Synthetic planned time ISO mapping.");
    await userEvent.click(screen.getByRole("button", { name: "Create mapping" }));
    await waitFor(() => expect(mappingRequests).toHaveLength(5));
    expect(await within(await screen.findByLabelText("Selected definition mappings")).findByText("$.issuedAt")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Mapping source node"), "/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue");
    await userEvent.selectOptions(screen.getByLabelText("Mapping target node"), "$.header.filteredAccessKey");
    await userEvent.selectOptions(screen.getByLabelText("Transform type"), "FILTER_BY_QUALIFIER");
    await userEvent.type(await screen.findByLabelText("Filter collection path"), "/Transmission/Shipment/Release/ReleaseRefnum");
    await userEvent.type(screen.getByLabelText("Filter qualifier path"), "ReleaseRefnumQualifierGid/Gid/Xid");
    await userEvent.type(screen.getByLabelText("Filter qualifier value"), "RFN_CHAVE_ACESSO");
    await userEvent.type(screen.getByLabelText("Filter value path"), "ReleaseRefnumValue");
    await userEvent.type(screen.getByLabelText("Mapping description"), "Synthetic filtered access key mapping.");
    await userEvent.click(screen.getByRole("button", { name: "Create mapping" }));
    await waitFor(() => expect(mappingRequests).toHaveLength(6));
    expect(await within(await screen.findByLabelText("Selected definition mappings")).findByText("$.header.filteredAccessKey")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Mapping source node"), "/Transmission/Shipment/Release/ReleaseGid/Gid/Xid");
    await userEvent.selectOptions(screen.getByLabelText("Mapping target node"), "$.header.releaseCount");
    await userEvent.selectOptions(screen.getByLabelText("Transform type"), "COUNT_DISTINCT");
    await userEvent.type(screen.getByLabelText("Count collection path"), "/Transmission/Shipment/Release");
    await userEvent.type(screen.getByLabelText("Count value path"), "ReleaseGid/Gid/Xid");
    await userEvent.type(screen.getByLabelText("Mapping description"), "Synthetic release count mapping.");
    await userEvent.click(screen.getByRole("button", { name: "Create mapping" }));
    await waitFor(() => expect(mappingRequests).toHaveLength(7));
    expect(await within(await screen.findByLabelText("Selected definition mappings")).findByText("$.header.releaseCount")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Lookup source schema"), "schema_source");
    await userEvent.selectOptions(screen.getByLabelText("Lookup target schema"), "schema_target");
    await userEvent.type(screen.getByLabelText("Lookup name"), "Synthetic carrier lookup");
    await userEvent.selectOptions(await screen.findByLabelText("Lookup input node"), "/Transmission/Shipment/ShipmentGid");
    await userEvent.selectOptions(await screen.findByLabelText("Lookup output node"), "$.header.shipmentId");
    expect(screen.getByLabelText("Lookup input path")).toHaveValue("/Transmission/Shipment/ShipmentGid");
    expect(screen.getByLabelText("Lookup output path")).toHaveValue("$.header.shipmentId");
    await userEvent.selectOptions(screen.getByLabelText("Lookup type"), "MOCK");
    await userEvent.type(screen.getByLabelText("Lookup description"), "Synthetic lookup metadata.");
    fireEvent.change(screen.getByLabelText("Lookup mock response JSON"), {
      target: { value: '{"shipmentId":"DEMO-SHIPMENT"}' }
    });
    await userEvent.click(screen.getByRole("button", { name: "Create lookup" }));
    await waitFor(() => expect(lookupRequests).toHaveLength(1));
    expect(await within(await screen.findByLabelText("Selected definition lookups")).findByText("Synthetic carrier lookup")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Response schema"), "schema_target");
    await userEvent.type(screen.getByLabelText("Response handler name"), "Accepted delivery response");
    await userEvent.selectOptions(await screen.findByLabelText("Response path node"), "$.status");
    expect(screen.getByLabelText("Response path")).toHaveValue("$.status");
    await userEvent.selectOptions(screen.getByLabelText("Success condition"), "EQUALS");
    await userEvent.type(screen.getByLabelText("Expected value"), "ACCEPTED");
    await userEvent.selectOptions(screen.getByLabelText("Outcome"), "SUCCESS");
    await userEvent.type(screen.getByLabelText("Response handler description"), "Synthetic response handler metadata.");
    await userEvent.click(screen.getByRole("button", { name: "Create response handler" }));
    await waitFor(() => expect(responseHandlerRequests).toHaveLength(1));
    expect(await within(await screen.findByLabelText("Selected definition response handlers")).findByText("Accepted delivery response")).toBeInTheDocument();

    const reviewPanel = await screen.findByLabelText("Integration mapping grouped executable review");
    expect(reviewPanel).toHaveTextContent("Header");
    expect(reviewPanel).toHaveTextContent("Entregas loop");
    expect(reviewPanel).toHaveTextContent("Joins");
    expect(reviewPanel).toHaveTextContent("Join bindings");
    expect(reviewPanel).toHaveTextContent("Lookups");
    expect(reviewPanel).toHaveTextContent("Response Handling");
    expect(reviewPanel).toHaveTextContent("Synthetic shipment stop join");
    expect(reviewPanel).toHaveTextContent("Stop to release binding");
    expect(reviewPanel).toHaveTextContent("stop_ship_unit, ship_unit_release");
    expect(reviewPanel).toHaveTextContent("Synthetic carrier lookup");
    expect(reviewPanel).toHaveTextContent("Accepted delivery response");
    expect(reviewPanel).toHaveTextContent("EQUALS ACCEPTED");

    await userEvent.click(screen.getByRole("button", { name: "Reset mapping rule drafts" }));
    expect(screen.getByLabelText("Source schema")).toHaveValue("");
    expect(screen.getByLabelText("Target schema")).toHaveValue("");
    expect(screen.getByLabelText("Mapping source node search")).toHaveValue("");
    expect(screen.getByLabelText("Mapping target node search")).toHaveValue("");
    expect(screen.getByLabelText("Source path")).toHaveValue("");
    expect(screen.getByLabelText("Target path")).toHaveValue("");
    expect(screen.getByLabelText("Transform type")).toHaveValue("DIRECT");
    expect(screen.getByLabelText("Alias source context")).toHaveValue("");
    expect(screen.getByLabelText("Constant value")).toHaveValue("");
    expect(screen.getByLabelText("Date source format")).toHaveValue("OTM_GLOGDATE");
    expect(screen.getByLabelText("Date target format")).toHaveValue("ISO8601");
    expect(screen.getByLabelText("Date timezone offset")).toHaveValue("-03:00");
    expect(screen.getByLabelText("Filter collection path")).toHaveValue("");
    expect(screen.getByLabelText("Filter qualifier path")).toHaveValue("");
    expect(screen.getByLabelText("Filter qualifier value")).toHaveValue("");
    expect(screen.getByLabelText("Filter value path")).toHaveValue("");
    expect(screen.getByLabelText("Count collection path")).toHaveValue("");
    expect(screen.getByLabelText("Count value path")).toHaveValue("");
    expect(screen.getByLabelText("Mapping description")).toHaveValue("");
    expect(screen.getByLabelText("Loop source schema")).toHaveValue("");
    expect(screen.getByLabelText("Loop target schema")).toHaveValue("");
    expect(screen.getByLabelText("Loop name")).toHaveValue("");
    expect(screen.getByLabelText("Loop source collection path")).toHaveValue("");
    expect(screen.getByLabelText("Loop target collection path")).toHaveValue("");
    expect(screen.getByLabelText("Join source schema")).toHaveValue("");
    expect(screen.getByLabelText("Join name")).toHaveValue("");
    expect(screen.getByLabelText("Join left path")).toHaveValue("");
    expect(screen.getByLabelText("Join right path")).toHaveValue("");
    expect(screen.getByLabelText("Join operator")).toHaveValue("EQ");
    expect(screen.getByLabelText("Join binding source schema")).toHaveValue("");
    expect(screen.getByLabelText("Join binding name")).toHaveValue("");
    expect(screen.getByLabelText("Join binding root collection path")).toHaveValue("");
    expect(screen.getByLabelText("Join binding target collection path")).toHaveValue("");
    expect(screen.getByLabelText("Hop 1 left value path")).toHaveValue("");
    expect(screen.getByLabelText("Hop 1 right value path")).toHaveValue("");
    expect(screen.getByLabelText("Hop 1 result alias")).toHaveValue("");
    expect(screen.getByLabelText("Hop 2 left value path")).toHaveValue("");
    expect(screen.getByLabelText("Hop 2 right value path")).toHaveValue("");
    expect(screen.getByLabelText("Hop 2 result alias")).toHaveValue("");
    expect(screen.getByLabelText("Lookup source schema")).toHaveValue("");
    expect(screen.getByLabelText("Lookup target schema")).toHaveValue("");
    expect(screen.getByLabelText("Lookup name")).toHaveValue("");
    expect(screen.getByLabelText("Lookup input path")).toHaveValue("");
    expect(screen.getByLabelText("Lookup output path")).toHaveValue("");
    expect(screen.getByLabelText("Lookup type")).toHaveValue("MOCK");
    expect(screen.getByLabelText("Lookup description")).toHaveValue("");
    expect(screen.getByLabelText("Lookup mock response JSON")).toHaveValue("");
    expect(screen.getByLabelText("Response schema")).toHaveValue("");
    expect(screen.getByLabelText("Response handler name")).toHaveValue("");
    expect(screen.getByLabelText("Response path")).toHaveValue("");
    expect(screen.getByLabelText("Success condition")).toHaveValue("EXISTS");
    expect(screen.getByLabelText("Expected value")).toHaveValue("");
    expect(screen.getByLabelText("Outcome")).toHaveValue("SUCCESS");
    expect(screen.getByLabelText("Response handler description")).toHaveValue("");
    expect(screen.queryByText("Created lookup Synthetic carrier lookup.")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: "Apply suggestion /Transmission/Shipment/ShipmentGid to $.header.shipmentId"
      })
    ).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Validate definition" }));
    await screen.findByText("Validation passed with 0 issue(s).");
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("Preview definition");
    const readinessPanel = await screen.findByLabelText("Integration mapping readiness");
    expect(readinessPanel).toHaveTextContent("Specification readiness");
    expect(readinessPanel).toHaveTextContent("Preview executable");
    expect(readinessPanel).toHaveTextContent("No specification blockers reported");
    const scenarioPackPanel = await screen.findByLabelText("Integration mapping required target checklist");
    expect(scenarioPackPanel).toHaveTextContent("PlannedShipment to External Delivery");
    expect(scenarioPackPanel).toHaveTextContent("$.NumeroViagem");
    expect(scenarioPackPanel).toHaveTextContent("mapping");
    expect(scenarioPackPanel).toHaveTextContent("$.Entregas[]");
    expect(scenarioPackPanel).toHaveTextContent("loop");
    await userEvent.click(screen.getByRole("button", { name: "Preview definition" }));
    await screen.findByText("Preview artifact artifact_preview generated by job job_preview.");
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("Generate spec");
    await userEvent.click(screen.getByRole("button", { name: "Generate spec" }));
    await screen.findByText("Spec artifact artifact_spec generated by job job_spec.");
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("Review generated artifacts");
    const generatedArtifactsPanel = await screen.findByLabelText("Integration mapping generated artifacts");
    expect(await within(generatedArtifactsPanel).findByText("integration_mapping_spec.md")).toBeInTheDocument();
    await userEvent.click(within(generatedArtifactsPanel).getAllByRole("button", { name: "Download" })[0]);
    await screen.findByText("Download started: integration_mapping_spec.md.");
    expect(artifactDownloadRequests).toHaveLength(1);
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(actionRequests).toEqual(["validate", "preview", "generate-spec"]);

    await userEvent.click(screen.getByRole("button", { name: /5Definitions list/ }));
    await userEvent.click(within(screen.getByLabelText("Integration mapping definitions")).getByRole("button", { name: /ALT_EXTERNAL_DELIVERY_UI/ }));
    expect(await screen.findByLabelText("Selected integration mapping definition")).toHaveTextContent("ALT_EXTERNAL_DELIVERY_UI");
    expect(screen.getByLabelText("Integration Mapping next action")).toHaveTextContent("Create payload samples");
    expect(screen.queryByText("Download started: integration_mapping_spec.md.")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration mapping readiness")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Integration mapping generated artifacts")).toHaveTextContent("No generated artifacts for this definition.");
    await userEvent.click(screen.getByRole("button", { name: /4Mapping rules/ }));
    expect(screen.getByLabelText("Source schema")).toHaveValue("");
    expect(screen.getByLabelText("Target schema")).toHaveValue("");
    expect(
      screen.queryByRole("button", {
        name: "Apply suggestion /Transmission/Shipment/ShipmentGid to $.header.shipmentId"
      })
    ).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(screen.getByRole("link", { name: /Integration Mapping Studio/ }));
    await screen.findByRole("heading", { name: "Integration Mapping Studio" });
    expect((await screen.findAllByText("PS_TO_EXTERNAL_DELIVERY_UI")).length).toBeGreaterThan(0);
  }, 120000);
});
