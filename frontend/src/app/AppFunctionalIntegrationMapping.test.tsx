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
    const loopRequests: unknown[] = [];
    const joinRequests: unknown[] = [];
    const lookupRequests: unknown[] = [];
    const artifactDownloadRequests: string[] = [];
    const actionRequests: string[] = [];
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
    let lookups: Array<Record<string, unknown>> = [];
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
    const createObjectURL = vi.fn(() => "blob:integration-mapping-artifact");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
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
      }
    ];
    const targetSchemaNodes = [
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
              }
            ],
            total: 1,
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
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/mappings")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          mappingRequests.push(body);
          expect(body).toEqual({
            source_schema_document_id: "schema_source",
            target_schema_document_id: "schema_target",
            source_path: "/Transmission/Shipment/ShipmentGid",
            target_path: "$.header.shipmentId",
            transform_type: "DIRECT",
            description: "Synthetic direct mapping from shipment id.",
            sequence_index: 10
          });
          const mapping = {
            id: "mapping_1",
            definition_id: "definition_1",
            ...body,
            status: "ACTIVE",
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:03:00",
            updated_at: "2026-05-21T10:03:00"
          };
          mappings = [mapping];
          return Promise.resolve(jsonResponse(mapping));
        }
        return Promise.resolve(jsonResponse({ items: mappings, total: mappings.length, page: 1, page_size: 50 }));
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
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/validate")) {
        actionRequests.push("validate");
        return Promise.resolve(
          jsonResponse({ is_valid: true, issue_count: 0, issues: [], readiness: validIntegrationReadiness() })
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
            validation: { is_valid: true, issue_count: 0, issues: [], readiness: validIntegrationReadiness() },
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
            validation: { is_valid: true, issue_count: 0, issues: [], readiness: validIntegrationReadiness() }
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
        url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_2/lookups")
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

    await userEvent.click(screen.getByRole("button", { name: /4Mapping rules/ }));
    expect(screen.getByLabelText("Integration mapping authoring")).toBeInTheDocument();
    expect(screen.queryByLabelText("Integration system authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration definition authoring")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration payload and schema authoring")).not.toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Source schema"), "schema_source");
    await userEvent.selectOptions(screen.getByLabelText("Target schema"), "schema_target");
    await userEvent.selectOptions(
      await screen.findByLabelText("Mapping source node"),
      "/Transmission/Shipment/ShipmentGid"
    );
    await userEvent.selectOptions(await screen.findByLabelText("Mapping target node"), "$.header.shipmentId");
    expect(screen.getByLabelText("Source path")).toHaveValue("/Transmission/Shipment/ShipmentGid");
    expect(screen.getByLabelText("Target path")).toHaveValue("$.header.shipmentId");
    await userEvent.selectOptions(screen.getByLabelText("Transform type"), "DIRECT");
    await userEvent.type(screen.getByLabelText("Mapping description"), "Synthetic direct mapping from shipment id.");
    await userEvent.click(screen.getByRole("button", { name: "Create mapping" }));

    await waitFor(() => expect(mappingRequests).toHaveLength(1));
    expect(await within(await screen.findByLabelText("Selected definition mappings")).findByText("$.header.shipmentId")).toBeInTheDocument();
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
    const reviewPanel = await screen.findByLabelText("Integration mapping grouped executable review");
    expect(reviewPanel).toHaveTextContent("Header");
    expect(reviewPanel).toHaveTextContent("Entregas loop");
    expect(reviewPanel).toHaveTextContent("Joins");
    expect(reviewPanel).toHaveTextContent("Lookups");
    expect(reviewPanel).toHaveTextContent("Response Handling");
    expect(reviewPanel).toHaveTextContent("Synthetic shipment stop join");
    expect(reviewPanel).toHaveTextContent("Synthetic carrier lookup");
    expect(reviewPanel).toHaveTextContent("No response handling rules defined.");

    await userEvent.click(screen.getByRole("button", { name: "Reset mapping rule drafts" }));
    expect(screen.getByLabelText("Source schema")).toHaveValue("");
    expect(screen.getByLabelText("Target schema")).toHaveValue("");
    expect(screen.getByLabelText("Source path")).toHaveValue("");
    expect(screen.getByLabelText("Target path")).toHaveValue("");
    expect(screen.getByLabelText("Transform type")).toHaveValue("DIRECT");
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
    expect(screen.getByLabelText("Lookup source schema")).toHaveValue("");
    expect(screen.getByLabelText("Lookup target schema")).toHaveValue("");
    expect(screen.getByLabelText("Lookup name")).toHaveValue("");
    expect(screen.getByLabelText("Lookup input path")).toHaveValue("");
    expect(screen.getByLabelText("Lookup output path")).toHaveValue("");
    expect(screen.getByLabelText("Lookup type")).toHaveValue("MOCK");
    expect(screen.getByLabelText("Lookup description")).toHaveValue("");
    expect(screen.getByLabelText("Lookup mock response JSON")).toHaveValue("");
    expect(screen.queryByText("Created lookup Synthetic carrier lookup.")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Validate definition" }));
    await screen.findByText("Validation passed with 0 issue(s).");
    const readinessPanel = await screen.findByLabelText("Integration mapping readiness");
    expect(readinessPanel).toHaveTextContent("Specification readiness");
    expect(readinessPanel).toHaveTextContent("Preview executable");
    expect(readinessPanel).toHaveTextContent("No specification blockers reported");
    await userEvent.click(screen.getByRole("button", { name: "Preview definition" }));
    await screen.findByText("Preview artifact artifact_preview generated by job job_preview.");
    await userEvent.click(screen.getByRole("button", { name: "Generate spec" }));
    await screen.findByText("Spec artifact artifact_spec generated by job job_spec.");
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
    expect(screen.queryByText("Download started: integration_mapping_spec.md.")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Integration mapping readiness")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Integration mapping generated artifacts")).toHaveTextContent("No generated artifacts for this definition.");
    await userEvent.click(screen.getByRole("button", { name: /4Mapping rules/ }));
    expect(screen.getByLabelText("Source schema")).toHaveValue("");
    expect(screen.getByLabelText("Target schema")).toHaveValue("");

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(screen.getByRole("link", { name: /Integration Mapping Studio/ }));
    await screen.findByRole("heading", { name: "Integration Mapping Studio" });
    expect((await screen.findAllByText("PS_TO_EXTERNAL_DELIVERY_UI")).length).toBeGreaterThan(0);
  }, 60000);
});
