import { useState } from 'react';

import {
  buildMasterDataCsv,
  buildMasterDataOutput,
  buildMasterDataWorkbook,
  createCoordinateQualityBatch,
  createCutoverChecklistFromPackage,
  createMasterDataTemplateDraft,
  downloadBackendArtifact,
  createMasterDataTemplateVersion,
  exportCoordinateQualityBatch,
  exportMasterDataCsvPackage,
  generateCutoverChecklistReadiness,
  getMasterDataBatch,
  mapMasterDataBatch,
  previewCoordinateQuality,
  publishMasterDataTemplate,
  registerMasterDataPackageForLoadPlan,
  updateMasterDataTemplateDraft,
  uploadMasterDataWorkbook,
  useCatalogColumnsByTable,
  useCatalogMacroObjectTables,
  useCatalogMacroObjects,
  useCoordinateQualityBatches,
  useCoordinateQualityResults,
  useMasterDataBatchArtifacts,
  useMasterDataBatchSummary,
  useMasterDataBatches,
  useMasterDataCsvFiles,
  useMasterDataOutputRecords,
  useMasterDataTemplateDetail,
  useMasterDataTemplates,
  validateMasterDataTemplateDefinition,
  validateMasterDataRelationships,
  validateMasterDataTemplate
} from '../../platform/hooks';
import type {
  CoordinateQualityBatch,
  CoordinateQualityExport,
  CoordinateQualityPreview,
  CoordinateQualityRecord,
  CutoverChecklist,
  CutoverChecklistReadiness,
  MasterDataActionResult,
  MasterDataArtifact,
  MasterDataBatch,
  MasterDataRelationshipValidation,
  MasterDataTemplate,
  MasterDataTemplateDraftRequest,
  MasterDataTemplateValidation,
  MasterDataWorkbookArtifact,
  LoadPlanPackage,
  AvailableAction
} from '../../platform/types';
import { ApiError } from '../../platform/api';
import { PageHeader } from '../../app/shell';
import {
  ArtifactList,
  BlockerPanel,
  Button,
  DetailList,
  FeedbackMessage,
  MetricGrid,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  OperationalPanel,
  SelectedObjectPanel,
  StatePanel
} from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function masterDataTemplateMeta(item: MasterDataTemplate) {
  const fieldCount = item.sheets.reduce((total, sheet) => total + sheet.fields.length, 0);
  return [item.catalog_macro_object_code, item.data_category, `${item.sheets.length} sheet(s)`, `${fieldCount} field(s)`];
}

function masterDataErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError) {
    const detail = typeof error.details.error === "string" ? error.details.error : null;
    return detail ? `${error.message} ${detail}` : error.message;
  }
  return error instanceof Error ? error.message : fallback;
}

function masterDataActionDisabled(batch: MasterDataBatch | null, key: string, fallbackDisabled: boolean) {
  const action = batch?.available_actions?.find((item) => item.key === key);
  return action ? action.disabled : fallbackDisabled;
}

function masterDataActionReason(batch: MasterDataBatch | null, key: string) {
  return batch?.available_actions?.find((item) => item.key === key)?.disabled_reason ?? undefined;
}

function masterDataTemplateActionDisabled(
  template: MasterDataTemplate | null | undefined,
  key: string,
  fallbackDisabled: boolean
) {
  const action = template?.available_actions?.find((item) => item.key === key);
  return action ? action.disabled : fallbackDisabled;
}

function masterDataTemplateActionReason(template: MasterDataTemplate | null | undefined, key: string) {
  return template?.available_actions?.find((item) => item.key === key)?.disabled_reason ?? undefined;
}

function masterDataActionGuidanceItems(scope: string, actions: AvailableAction[] | undefined) {
  return (actions ?? []).map((action) => ({
    id: `${scope}-${action.key}`,
    meta: [
      scope,
      action.disabled ? action.disabled_reason ?? "Blocked by backend rule" : action.recommended ? "Recommended next" : "Ready now"
    ],
    status: action.disabled ? "BLOCKED" : action.recommended ? "NEXT" : "AVAILABLE",
    title: action.label
  }));
}

const masterDataWorkflowStages = [
  { id: "templates", title: "Templates", status: "1" },
  { id: "author", title: "Author", status: "2" },
  { id: "workbook", title: "Workbook", status: "3" },
  { id: "upload", title: "Upload", status: "4" },
  { id: "validate", title: "Validate", status: "5" },
  { id: "map", title: "Map", status: "6" },
  { id: "output", title: "Output", status: "7" },
  { id: "quality", title: "Quality", status: "8" }
] as const;

type MasterDataWorkflowStage = (typeof masterDataWorkflowStages)[number]["id"];
type AuthorSourceType = "USER_FIELD" | "FIXED_VALUE" | "DEFAULT_VALUE";
type AuthorMappingConfig = {
  defaultValue?: string;
  fixedValue?: string;
  label?: string;
  sourceType?: AuthorSourceType;
};

function summaryMeta(summary: Record<string, unknown> | undefined) {
  return Object.entries(summary ?? {}).map(([key, value]) => `${key}: ${String(value)}`);
}

function parseJsonObject(text: string) {
  const parsed = JSON.parse(text) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Expected a JSON object.");
  }
  return parsed as Record<string, { lat: number; lon: number; source?: string }>;
}

function parseJsonArray(text: string) {
  const parsed = JSON.parse(text) as unknown;
  if (!Array.isArray(parsed) || parsed.some((item) => !item || typeof item !== "object" || Array.isArray(item))) {
    throw new Error("Expected a JSON array of objects.");
  }
  return parsed as Array<Record<string, unknown>>;
}

const defaultAuthorColumns = ["LOCATION_GID", "LOCATION_XID", "LOCATION_NAME", "COUNTRY_CODE3_GID"];

const defaultCoordinateQualityRecords = [
  {
    location_gid: "SYN.LOC_QA_001",
    location_name: "Synthetic Preview DC",
    address_line: "Rua Um 100",
    city: "Sao Paulo",
    province_code: "SP",
    postal_code: "01000-000",
    country_code3_gid: "BRA",
    lat: null,
    lon: null
  },
  {
    location_gid: "SYN.LOC_QA_002",
    location_name: "Synthetic Corrected DC",
    address_line: "Rua Dois 200",
    city: "Sao Paulo",
    province_code: "SP",
    postal_code: "01000-000",
    country_code3_gid: "BRA",
    lat: -3.73,
    lon: -38.52
  }
];

const defaultCoordinateQualityCandidates = {
  "SYN.LOC_QA_001": { lat: -23.55, lon: -46.63, source: "fake:inline" },
  "SYN.LOC_QA_002": { lat: -23.55, lon: -46.63, source: "fake:inline" }
};

function fieldKeyForColumn(columnName: string) {
  return columnName.toLowerCase();
}

function labelForColumn(columnName: string) {
  return columnName
    .split("_")
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(" ");
}

function sourceFieldKey(tableName: string, columnName: string) {
  if (tableName === "LOCATION" && columnName === "LOCATION_XID") return "location_gid";
  if (tableName === "LOCATION" && columnName === "LOCATION_GID") return "location_gid";
  return `${fieldKeyForColumn(tableName)}_${fieldKeyForColumn(columnName)}`;
}

function authorMappingKey(tableName: string, columnName: string) {
  return `${tableName}.${columnName}`;
}

function defaultSourceType(tableName: string, columnName: string): AuthorSourceType {
  if (tableName === "LOCATION" && columnName === "COUNTRY_CODE3_GID") return "FIXED_VALUE";
  return "USER_FIELD";
}

function defaultFixedValue(tableName: string, columnName: string) {
  if (tableName === "LOCATION" && columnName === "COUNTRY_CODE3_GID") return "USA";
  return "";
}

function selectedAuthorColumns(selectedTables: string[], selectedColumnsByTable: Record<string, string[]>) {
  return selectedTables.flatMap((tableName) =>
    (selectedColumnsByTable[tableName] ?? []).map((columnName) => ({
      columnName,
      key: authorMappingKey(tableName, columnName),
      tableName
    }))
  );
}

function authorStateFromTemplate(template: MasterDataTemplate) {
  const definition = template.definition;
  if (!definition) return null;

  const tables = definition.target_tables.map((table) => table.table_name);
  const columnsByTable = definition.mappings.reduce<Record<string, string[]>>((current, mapping) => {
    const columns = current[mapping.target_table] ?? [];
    return {
      ...current,
      [mapping.target_table]: columns.includes(mapping.target_column)
        ? columns
        : [...columns, mapping.target_column]
    };
  }, {});
  const fieldsByKey = new Map(definition.fields.map((field) => [field.field_key, field]));
  const mappingConfigByKey = definition.mappings.reduce<Record<string, AuthorMappingConfig>>((current, mapping) => {
    const key = authorMappingKey(mapping.target_table, mapping.target_column);
    const field = mapping.source_field_key ? fieldsByKey.get(mapping.source_field_key) : undefined;
    return {
      ...current,
      [key]: {
        defaultValue: mapping.default_value,
        fixedValue: mapping.fixed_value,
        label: field?.label,
        sourceType: mapping.source_type
      }
    };
  }, {});
  const hasLocationAddressRelationship = definition.relationship_rules.some(
    (rule) =>
      rule.rule_key === "location_to_location_address" ||
      (rule.parent_sheet_code === "LOCATIONS" && rule.child_sheet_code === "LOCATION_ADDRESS")
  );

  return {
    columnsByTable: {
      LOCATION: columnsByTable.LOCATION ?? [],
      LOCATION_ADDRESS: columnsByTable.LOCATION_ADDRESS ?? []
    },
    hasLocationAddressRelationship,
    mappingConfigByKey,
    tables: tables.length ? tables : ["LOCATION"]
  };
}

function locationDraftPayload(
  code: string,
  name: string,
  macroObjectCode: string,
  selectedTables: string[],
  selectedColumnsByTable: Record<string, string[]>,
  mappingConfigByKey: Record<string, AuthorMappingConfig>,
  includeLocationAddressRelationship: boolean
): MasterDataTemplateDraftRequest {
  const normalizedTables = selectedTables.length ? selectedTables : ["LOCATION"];
  const targetTables = normalizedTables.map((tableName, index) => ({
    table_name: tableName,
    sequence: (index + 1) * 10,
    required: tableName === "LOCATION"
  }));
  const userFieldColumns = (tableName: string) =>
    (selectedColumnsByTable[tableName] ?? []).filter((column) => {
      const config = mappingConfigByKey[authorMappingKey(tableName, column)] ?? {};
      const sourceType = config.sourceType ?? defaultSourceType(tableName, column);
      return sourceType === "USER_FIELD";
    });
  const sheets = normalizedTables.map((tableName, index) => ({
    code: tableName === "LOCATION" ? "LOCATIONS" : tableName,
    name: labelForColumn(tableName),
    sequence: (index + 1) * 10,
    field_keys: Array.from(
      new Set(
        userFieldColumns(tableName).map((column) => sourceFieldKey(tableName, column))
      )
    )
  }));
  const fields = normalizedTables.flatMap((tableName) => {
    const sheet = sheets.find((item) => item.code === (tableName === "LOCATION" ? "LOCATIONS" : tableName));
    if (!sheet) return [];
    return userFieldColumns(tableName).map((column) => {
      const fieldKey = sourceFieldKey(tableName, column);
      const config = mappingConfigByKey[authorMappingKey(tableName, column)] ?? {};
      return {
        field_key: fieldKey,
        label: config.label?.trim() || (fieldKey === "location_gid" ? "Location ID" : labelForColumn(column)),
        data_type: "string",
        required: tableName === "LOCATION" && (column === "LOCATION_GID" || column === "LOCATION_XID"),
        sheet_code: sheet.code
      };
    });
  });
  const mappings = normalizedTables.flatMap((tableName) =>
    (selectedColumnsByTable[tableName] ?? []).map((column) => {
      const config = mappingConfigByKey[authorMappingKey(tableName, column)] ?? {};
      const sourceType = config.sourceType ?? defaultSourceType(tableName, column);
      if (sourceType === "FIXED_VALUE") {
        return {
          mapping_key: `${fieldKeyForColumn(tableName)}_${fieldKeyForColumn(column)}_fixed`,
          source_type: "FIXED_VALUE" as const,
          fixed_value: config.fixedValue?.trim() || defaultFixedValue(tableName, column),
          target_table: tableName,
          target_column: column,
          required: false
        };
      }
      if (sourceType === "DEFAULT_VALUE") {
        return {
          mapping_key: `${fieldKeyForColumn(tableName)}_${fieldKeyForColumn(column)}_default`,
          source_type: "DEFAULT_VALUE" as const,
          default_value: config.defaultValue?.trim() ?? "",
          target_table: tableName,
          target_column: column,
          required: false
        };
      }
      return {
        mapping_key: `${fieldKeyForColumn(tableName)}_${fieldKeyForColumn(column)}_to_${fieldKeyForColumn(column)}`,
        source_type: "USER_FIELD" as const,
        source_field_key: sourceFieldKey(tableName, column),
        target_table: tableName,
        target_column: column,
        required: tableName === "LOCATION" && (column === "LOCATION_GID" || column === "LOCATION_XID")
      };
    })
  );
  const relationshipRules =
    includeLocationAddressRelationship &&
    normalizedTables.includes("LOCATION_ADDRESS") &&
    (selectedColumnsByTable.LOCATION_ADDRESS ?? []).includes("LOCATION_GID")
      ? [
          {
            rule_key: "location_to_location_address",
            parent_sheet_code: "LOCATIONS",
            parent_field_key: "location_gid",
            child_sheet_code: "LOCATION_ADDRESS",
            child_field_key: sourceFieldKey("LOCATION_ADDRESS", "LOCATION_GID"),
            severity: "ERROR"
          }
        ]
      : [];

  return {
    code,
    name,
    catalog_macro_object_code: macroObjectCode,
    data_category: "MASTER_DATA",
    target_tables: targetTables,
    sheets,
    fields,
    mappings,
    relationship_rules: relationshipRules,
    documentation_refs: [
      {
        source_type: "DATA_DICTIONARY",
        scope: macroObjectCode,
        note: "Validated against local OTM Data Dictionary."
      }
    ]
  };
}

export function MasterDataView({ token }: { token: string }) {
  const templates = useMasterDataTemplates(token);
  const coordinateQualityBatches = useCoordinateQualityBatches(token);
  const catalogMacroObjects = useCatalogMacroObjects(token);
  const [authorMacroObjectCode, setAuthorMacroObjectCode] = useState("LOCATION");
  const catalogAuthorTables = useCatalogMacroObjectTables(token, authorMacroObjectCode);
  const [selectedTemplateCode, setSelectedTemplateCode] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<MasterDataWorkflowStage>("templates");
  const [templateValidation, setTemplateValidation] = useState<MasterDataTemplateValidation | null>(null);
  const [workbookArtifact, setWorkbookArtifact] = useState<MasterDataWorkbookArtifact | null>(null);
  const [uploadedBatch, setUploadedBatch] = useState<MasterDataBatch | null>(null);
  const [relationshipValidation, setRelationshipValidation] = useState<MasterDataRelationshipValidation | null>(null);
  const [mappingResult, setMappingResult] = useState<MasterDataActionResult | null>(null);
  const [outputResult, setOutputResult] = useState<MasterDataActionResult | null>(null);
  const [csvResult, setCsvResult] = useState<MasterDataActionResult | null>(null);
  const [exportResult, setExportResult] = useState<MasterDataActionResult | null>(null);
  const [loadPlanPackage, setLoadPlanPackage] = useState<LoadPlanPackage | null>(null);
  const [cutoverChecklist, setCutoverChecklist] = useState<CutoverChecklist | null>(null);
  const [cutoverChecklistReadiness, setCutoverChecklistReadiness] = useState<CutoverChecklistReadiness | null>(null);
  const [coordinateRecordsJson, setCoordinateRecordsJson] = useState(
    JSON.stringify(defaultCoordinateQualityRecords, null, 2)
  );
  const [coordinateCandidatesJson, setCoordinateCandidatesJson] = useState(
    JSON.stringify(defaultCoordinateQualityCandidates, null, 2)
  );
  const [coordinatePreview, setCoordinatePreview] = useState<CoordinateQualityPreview | null>(null);
  const [coordinateBatch, setCoordinateBatch] = useState<CoordinateQualityBatch | null>(null);
  const [coordinateExport, setCoordinateExport] = useState<CoordinateQualityExport | null>(null);
  const [batchTemplateFilter, setBatchTemplateFilter] = useState("");
  const [batchStatusFilter, setBatchStatusFilter] = useState("");
  const [batchFileNameFilter, setBatchFileNameFilter] = useState("");
  const [batchMinRowCountFilter, setBatchMinRowCountFilter] = useState("");
  const [batchPageSize, setBatchPageSize] = useState(50);
  const [batchPage, setBatchPage] = useState(1);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const [authorTemplateCode, setAuthorTemplateCode] = useState("LOCATIONS_DYNAMIC_UI");
  const [authorTemplateName, setAuthorTemplateName] = useState("Locations Dynamic UI");
  const [authorTables, setAuthorTables] = useState<string[]>(["LOCATION"]);
  const [authorColumnsByTable, setAuthorColumnsByTable] = useState<Record<string, string[]>>({
    LOCATION: defaultAuthorColumns,
    LOCATION_ADDRESS: []
  });
  const [authorMappingConfigByKey, setAuthorMappingConfigByKey] = useState<Record<string, AuthorMappingConfig>>({});
  const [includeLocationAddressRelationship, setIncludeLocationAddressRelationship] = useState(false);
  const [authorTemplate, setAuthorTemplate] = useState<MasterDataTemplate | null>(null);
  const [authorValidation, setAuthorValidation] = useState<MasterDataTemplateValidation | null>(null);
  const [authorVersion, setAuthorVersion] = useState<MasterDataTemplate | null>(null);
  const [selectedUploadFile, setSelectedUploadFile] = useState<File | null>(null);
  const [operationMessage, setOperationMessage] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const templateItems = templates.data?.items ?? [];
  const effectiveTemplateCode = selectedTemplateCode ?? templateItems[0]?.code ?? null;
  const templateDetail = useMasterDataTemplateDetail(token, effectiveTemplateCode);
  const selectedTemplate = templateDetail.data;
  const batchFilters = {
    file_name_contains: batchFileNameFilter.trim() || undefined,
    min_row_count: batchMinRowCountFilter ? Number(batchMinRowCountFilter) : undefined,
    page: batchPage,
    page_size: batchPageSize,
    status: batchStatusFilter || undefined,
    template_code: batchTemplateFilter || undefined
  };
  const batches = useMasterDataBatches(token, batchFilters);
  const batchSummary = useMasterDataBatchSummary(token, batchFilters);
  const targetTableCount = new Set(templateItems.flatMap((item) => item.target_tables)).size;
  const sheetCount = templateItems.reduce((total, item) => total + item.sheets.length, 0);
  const fieldCount =
    selectedTemplate?.sheets.reduce((total, sheet) => total + sheet.fields.length, 0) ??
    templateItems.reduce((total, item) => total + item.sheets.reduce((sheetTotal, sheet) => sheetTotal + sheet.fields.length, 0), 0);
  const authorSelectedColumns = selectedAuthorColumns(authorTables, authorColumnsByTable);
  const authorColumnsCatalog = useCatalogColumnsByTable(token, authorTables);
  const activeBatch = uploadedBatch ?? batches.data?.items[0] ?? null;
  const batchArtifacts = useMasterDataBatchArtifacts(token, activeBatch?.batch_id ?? null);
  const outputRecords = useMasterDataOutputRecords(token, activeBatch?.batch_id ?? null);
  const csvFiles = useMasterDataCsvFiles(token, activeBatch?.batch_id ?? null);
  const canRegisterLoadPlanPackage = Boolean(activeBatch && (exportResult || activeBatch.status === "EXPORTED"));
  const activeCoordinateBatch = coordinateBatch ?? coordinateQualityBatches.data?.items[0] ?? null;
  const coordinateResults = useCoordinateQualityResults(token, activeCoordinateBatch?.batch_id ?? null);
  const coordinateQualityBatchItems =
    coordinateBatch && !(coordinateQualityBatches.data?.items ?? []).some((batch) => batch.batch_id === coordinateBatch.batch_id)
      ? [coordinateBatch, ...(coordinateQualityBatches.data?.items ?? [])]
      : (coordinateQualityBatches.data?.items ?? []);
  const authorDraftPreview = locationDraftPayload(
    authorTemplateCode.trim().toUpperCase() || "LOCATIONS_DYNAMIC_UI",
    authorTemplateName.trim() || "Locations Dynamic UI",
    authorMacroObjectCode,
    authorTables,
    authorColumnsByTable,
    authorMappingConfigByKey,
    includeLocationAddressRelationship
  );

  const runAction = async <T,>(action: () => Promise<T>, onSuccess: (result: T) => string) => {
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await action();
      setOperationMessage(onSuccess(result));
    } catch (error) {
      setOperationError(masterDataErrorMessage(error, "Data Factory action failed."));
    } finally {
      setIsMutating(false);
    }
  };

  const handleValidateTemplate = () => {
    if (!effectiveTemplateCode) return;
    void runAction(
      async () => {
        const result = await validateMasterDataTemplate(token, effectiveTemplateCode);
        setTemplateValidation(result);
        return result;
      },
      (result) => `Template validation is ${result.valid ? "VALID" : result.severity}.`
    );
  };

  const coordinateQualityPayload = () => ({
    fake_candidates: parseJsonObject(coordinateCandidatesJson),
    records: parseJsonArray(coordinateRecordsJson) as CoordinateQualityRecord[],
    source_batch_id: activeBatch?.batch_id ?? null,
    source_type: activeBatch ? "master_data_batch" : "api"
  });

  const handlePreviewCoordinateQuality = () => {
    void runAction(
      async () => {
        const result = await previewCoordinateQuality(token, coordinateQualityPayload());
        setCoordinatePreview(result);
        return result;
      },
      (result) => `Coordinate Quality preview processed ${result.summary.processed_count} location(s).`
    );
  };

  const handleCreateCoordinateQualityBatch = () => {
    void runAction(
      async () => {
        const result = await createCoordinateQualityBatch(token, coordinateQualityPayload());
        setCoordinateBatch(result);
        setCoordinateExport(null);
        return result;
      },
      (result) => `Coordinate Quality batch ${result.batch_id} created.`
    );
  };

  const handleExportCoordinateQuality = () => {
    if (!activeCoordinateBatch) return;
    void runAction(
      async () => {
        const result = await exportCoordinateQualityBatch(token, activeCoordinateBatch.batch_id);
        setCoordinateExport(result);
        return result;
      },
      (result) => `Coordinate Quality package ${result.file_name} exported.`
    );
  };

  const handleCreateDraft = () => {
    const code = authorTemplateCode.trim().toUpperCase();
    if (!code || !authorTemplateName.trim()) return;
    void runAction(
      async () => {
        const result = await createMasterDataTemplateDraft(
          token,
          locationDraftPayload(
            code,
            authorTemplateName.trim(),
            authorMacroObjectCode,
            authorTables,
            authorColumnsByTable,
            authorMappingConfigByKey,
            includeLocationAddressRelationship
          )
        );
        setAuthorTemplate(result);
        setAuthorValidation(null);
        setAuthorVersion(null);
        return result;
      },
      (result) => `Draft ${result.code} created.`
    );
  };

  const handleToggleAuthorTableColumn = (tableName: string, columnName: string) => {
    setAuthorColumnsByTable((current) => {
      const columns = current[tableName] ?? [];
      return {
        ...current,
        [tableName]: columns.includes(columnName)
          ? columns.filter((column) => column !== columnName)
          : [...columns, columnName]
      };
    });
  };

  const handleToggleAuthorTable = (tableName: string) => {
    setAuthorTables((current) => {
      if (!current.includes(tableName)) return [...current, tableName];
      if (tableName === "LOCATION_ADDRESS") {
        setIncludeLocationAddressRelationship(false);
      }
      setAuthorColumnsByTable((columnsByTable) => ({
        ...columnsByTable,
        [tableName]: []
      }));
      setAuthorMappingConfigByKey((currentConfig) =>
        Object.fromEntries(Object.entries(currentConfig).filter(([key]) => !key.startsWith(`${tableName}.`)))
      );
      return current.filter((table) => table !== tableName);
    });
  };

  const handleAuthorMacroObjectChange = (macroObjectCode: string) => {
    const primaryTable = macroObjectCode === "LOCATION" ? "LOCATION" : "";
    setAuthorMacroObjectCode(macroObjectCode);
    setAuthorTables(primaryTable ? [primaryTable] : []);
    setAuthorColumnsByTable(primaryTable === "LOCATION" ? { LOCATION: defaultAuthorColumns } : {});
    setAuthorMappingConfigByKey({});
    setIncludeLocationAddressRelationship(false);
    setAuthorTemplate(null);
    setAuthorValidation(null);
    setAuthorVersion(null);
  };

  const updateAuthorMappingConfig = (key: string, patch: AuthorMappingConfig) => {
    setAuthorMappingConfigByKey((current) => ({
      ...current,
      [key]: {
        ...current[key],
        ...patch
      }
    }));
  };

  const handleLoadSelectedTemplateIntoAuthor = () => {
    if (!selectedTemplate?.definition) return;
    const recoveredState = authorStateFromTemplate(selectedTemplate);
    if (!recoveredState) return;
    setAuthorTemplateCode(selectedTemplate.code);
    setAuthorTemplateName(selectedTemplate.name);
    setAuthorMacroObjectCode(selectedTemplate.catalog_macro_object_code);
    setAuthorTables(recoveredState.tables);
    setAuthorColumnsByTable(recoveredState.columnsByTable);
    setAuthorMappingConfigByKey(recoveredState.mappingConfigByKey);
    setIncludeLocationAddressRelationship(recoveredState.hasLocationAddressRelationship);
    setAuthorTemplate(selectedTemplate);
    setAuthorValidation(null);
    setAuthorVersion(null);
    setOperationMessage(`Template ${selectedTemplate.code} loaded into author.`);
    setOperationError(null);
  };

  const handleUpdateDraft = () => {
    const code = authorTemplate?.code ?? authorTemplateCode.trim().toUpperCase();
    if (!code || !authorTemplateName.trim()) return;
    void runAction(
      async () => {
        const result = await updateMasterDataTemplateDraft(
          token,
          code,
          locationDraftPayload(
            code,
            authorTemplateName.trim(),
            authorMacroObjectCode,
            authorTables,
            authorColumnsByTable,
            authorMappingConfigByKey,
            includeLocationAddressRelationship
          )
        );
        setAuthorTemplate(result);
        setAuthorVersion(null);
        return result;
      },
      (result) => `Draft ${result.code} updated.`
    );
  };

  const handleValidateDefinition = () => {
    if (!authorTemplate?.code) return;
    void runAction(
      async () => {
        const result = await validateMasterDataTemplateDefinition(token, authorTemplate.code);
        setAuthorValidation(result);
        return result;
      },
      (result) => `Definition validation is ${result.valid ? "VALID" : result.severity}.`
    );
  };

  const handlePublishTemplate = () => {
    if (!authorTemplate?.code) return;
    void runAction(
      async () => {
        const result = await publishMasterDataTemplate(token, authorTemplate.code);
        setAuthorTemplate(result);
        return result;
      },
      (result) => `Template ${result.code} published.`
    );
  };

  const handleCreateVersion = () => {
    if (!authorTemplate?.code) return;
    const nextCode = `${authorTemplate.code}_V${Number(authorTemplate.version) + 1}`;
    void runAction(
      async () => {
        const result = await createMasterDataTemplateVersion(token, authorTemplate.code, nextCode);
        setAuthorVersion(result);
        return result;
      },
      (result) => `Version ${result.code} created.`
    );
  };

  const handleBuildWorkbook = () => {
    if (!effectiveTemplateCode) return;
    void runAction(
      async () => {
        const result = await buildMasterDataWorkbook(token, effectiveTemplateCode);
        setWorkbookArtifact(result);
        return result;
      },
      (result) => `Workbook ${result.file_name} generated.`
    );
  };

  const handleUploadWorkbook = () => {
    if (!effectiveTemplateCode || !selectedUploadFile) return;
    void runAction(
      async () => {
        const result = await uploadMasterDataWorkbook(token, effectiveTemplateCode, selectedUploadFile);
        setUploadedBatch(result);
        setRelationshipValidation(null);
        setMappingResult(null);
        setOutputResult(null);
        setCsvResult(null);
        setExportResult(null);
        setLoadPlanPackage(null);
        setCutoverChecklist(null);
        setCutoverChecklistReadiness(null);
        await batches.refetch();
        return result;
      },
      (result) => `Workbook uploaded as batch ${result.batch_id}.`
    );
  };

  const handleValidateRelationships = () => {
    if (!activeBatch) return;
    void runAction(
      async () => {
        const result = await validateMasterDataRelationships(token, activeBatch.batch_id);
        setRelationshipValidation(result);
        setUploadedBatch(await getMasterDataBatch(token, activeBatch.batch_id));
        await batches.refetch();
        return result;
      },
      (result) => `Relationship validation is ${result.valid ? "VALID" : result.status}.`
    );
  };

  const handleMapBatch = () => {
    if (!activeBatch) return;
    void runAction(
      async () => {
        const result = await mapMasterDataBatch(token, activeBatch.batch_id);
        setMappingResult(result);
        setUploadedBatch(await getMasterDataBatch(token, activeBatch.batch_id));
        await batches.refetch();
        return result;
      },
      (result) => `Batch mapping is ${result.status}.`
    );
  };

  const handleBuildOutput = () => {
    if (!activeBatch) return;
    void runAction(
      async () => {
        const result = await buildMasterDataOutput(token, activeBatch.batch_id);
        setOutputResult(result);
        setUploadedBatch(await getMasterDataBatch(token, activeBatch.batch_id));
        await batches.refetch();
        await outputRecords.refetch();
        return result;
      },
      (result) => `Output build is ${result.status}.`
    );
  };

  const handleBuildCsv = () => {
    if (!activeBatch) return;
    void runAction(
      async () => {
        const result = await buildMasterDataCsv(token, activeBatch.batch_id);
        setCsvResult(result);
        setUploadedBatch(await getMasterDataBatch(token, activeBatch.batch_id));
        await batches.refetch();
        await csvFiles.refetch();
        return result;
      },
      (result) => `CSV build is ${result.status}.`
    );
  };

  const handleExportCsvPackage = () => {
    if (!activeBatch) return;
    void runAction(
      async () => {
        const result = await exportMasterDataCsvPackage(token, activeBatch.batch_id);
        setExportResult(result);
        setUploadedBatch(await getMasterDataBatch(token, activeBatch.batch_id));
        setLoadPlanPackage(null);
        setCutoverChecklist(null);
        setCutoverChecklistReadiness(null);
        await batches.refetch();
        await batchArtifacts.refetch();
        await csvFiles.refetch();
        return result;
      },
      (result) => `CSV package export is ${result.status}.`
    );
  };

  const handleRegisterLoadPlanPackage = () => {
    if (!activeBatch) return;
    void runAction(
      async () => {
        const result = await registerMasterDataPackageForLoadPlan(token, activeBatch.batch_id);
        setLoadPlanPackage(result);
        setCutoverChecklist(null);
        setCutoverChecklistReadiness(null);
        return result;
      },
      (result) => `Load Plan package ${result.id} registered.`
    );
  };

  const handleCreateCutoverChecklist = () => {
    if (!loadPlanPackage) return;
    void runAction(
      async () => {
        const result = await createCutoverChecklistFromPackage(token, loadPlanPackage.id);
        setCutoverChecklist(result);
        setCutoverChecklistReadiness(null);
        return result;
      },
      (result) => `Cutover checklist ${result.id} created.`
    );
  };

  const handleGenerateCutoverChecklistReadiness = () => {
    if (!cutoverChecklist) return;
    void runAction(
      async () => {
        const result = await generateCutoverChecklistReadiness(token, cutoverChecklist.id);
        setCutoverChecklistReadiness(result);
        return result;
      },
      (result) => `Cutover checklist readiness is ${result.status}.`
    );
  };

  const handleDownloadArtifact = async (artifact: MasterDataArtifact) => {
    if (!artifact.download_url) return;
    setIsMutating(true);
    setDownloadingArtifactId(artifact.id);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await downloadBackendArtifact(token, artifact.download_url);
      const objectUrl = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = result.filename ?? artifact.file_name;
      link.click();
      URL.revokeObjectURL(objectUrl);
      setOperationMessage(`Download started: ${result.filename ?? artifact.file_name}.`);
    } catch (error) {
      setOperationError(masterDataErrorMessage(error, "Could not download Master Data artifact."));
    } finally {
      setDownloadingArtifactId(null);
      setIsMutating(false);
    }
  };

  if (templates.isLoading) {
    return <StatePanel>Loading Data Factory...</StatePanel>;
  }

  if (templates.isError || !templates.data) {
    return <StatePanel tone="error">Data Factory is unavailable.</StatePanel>;
  }

  return (
    <>
      <PageHeader
        description="Template factory and master data batch preparation for backend-first OTM implementation flows."
        label="Module workspace"
        title="Data Factory"
      />

      <MetricGrid
        ariaLabel="Data Factory metrics"
        items={[
          { key: "templates", label: "Templates", status: booleanStatus(templates.data.total), value: templates.data.total },
          { key: "tables", label: "Target tables", status: booleanStatus(targetTableCount), value: targetTableCount },
          { key: "sheets", label: "Sheets", status: booleanStatus(sheetCount), value: sheetCount },
          { key: "fields", label: "Fields", status: booleanStatus(fieldCount), value: fieldCount }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Data Factory workspace"
        side={
          <SelectedObjectPanel
            ariaLabel="Selected Master Data template"
            emptyText="Select a template to inspect backend-owned metadata."
            fields={
              selectedTemplate
                ? [
                    { label: "Macro object", value: selectedTemplate.catalog_macro_object_code },
                    { label: "Version", value: selectedTemplate.version },
                    { label: "Target tables", value: selectedTemplate.target_tables.length },
                    { label: "Fields", value: fieldCount },
                    { label: "Active batch", value: activeBatch?.batch_id ?? "None" },
                    { label: "Batch status", value: activeBatch?.status ?? "No batch" }
                  ]
                : []
            }
            isLoading={templateDetail.isLoading && Boolean(effectiveTemplateCode)}
            loadingText="Loading selected template..."
            status={selectedTemplate?.status ?? "PENDING"}
            subtitle={selectedTemplate?.name}
            title={selectedTemplate?.code}
          >
            {selectedTemplate?.description ? <p className="empty-text">{selectedTemplate.description}</p> : null}
            <DetailList
              ariaLabel="Selected Master Data action guidance"
              emptyText="No backend action guidance is available for the selected template or active batch."
              items={[
                ...masterDataActionGuidanceItems("Template", selectedTemplate?.available_actions),
                ...masterDataActionGuidanceItems("Batch", activeBatch?.available_actions)
              ]}
            />
            <DetailList
              ariaLabel="Selected template sheets"
              emptyText="No sheets defined for this template."
              items={(selectedTemplate?.sheets ?? []).map((sheet) => ({
                id: sheet.code,
                meta: [sheet.target_table, `${sheet.fields.length} field(s)`],
                status: "ACTIVE",
                title: sheet.code
              }))}
            />
            <DetailList
              ariaLabel="Selected template fields"
              emptyText="No fields defined for this template."
              items={(selectedTemplate?.sheets ?? []).flatMap((sheet) =>
                sheet.fields.map((field) => ({
                  id: `${sheet.code}-${field.name}`,
                  meta: [sheet.code, field.target_column, field.required ? "Required" : "Optional"],
                  status: field.required ? "REQUIRED" : "OPTIONAL",
                  title: field.label
                }))
              )}
            />
          </SelectedObjectPanel>
        }
        status={templateItems.length ? "ACTIVE" : "EMPTY"}
        title="Data Factory workflow"
      >
        <div className="master-data-workflow" aria-label="Data Factory workflow">
          {masterDataWorkflowStages.map((stage) => (
            <button
              aria-pressed={activeStage === stage.id}
              className={
                activeStage === stage.id
                  ? "master-data-workflow-step master-data-workflow-step-active"
                  : "master-data-workflow-step"
              }
              key={stage.id}
              onClick={() => setActiveStage(stage.id)}
              type="button"
            >
              <span>{stage.status}</span>
              <strong>{stage.title}</strong>
            </button>
          ))}
        </div>

        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        {activeStage === "templates" ? (
          <ModuleObjectList
            ariaLabel="Master Data templates"
            emptyText="No Master Data templates available for the current context."
            items={templateItems.map((item) => ({
              id: item.code,
              meta: masterDataTemplateMeta(item),
              status: item.status,
              subtitle: item.name,
              title: item.code
            }))}
            onSelect={setSelectedTemplateCode}
            selectedId={effectiveTemplateCode}
          />
        ) : null}

        {activeStage === "author" ? (
          <OperationalPanel
            ariaLabel="Template authoring workflow"
            emptyText="Create a backend-owned draft before validating and publishing."
            hasItems
            status={authorVersion?.status ?? authorTemplate?.status ?? "DRAFT"}
            title="Author template"
          >
            <div className="master-data-author-grid">
              <label>
                Template code
                <input
                  onChange={(event) => setAuthorTemplateCode(event.target.value)}
                  value={authorTemplateCode}
                />
              </label>
              <label>
                Template name
                <input
                  onChange={(event) => setAuthorTemplateName(event.target.value)}
                  value={authorTemplateName}
                />
              </label>
              <label>
                Catalog macro-object
                <select
                  aria-label="Catalog macro-object"
                  onChange={(event) => handleAuthorMacroObjectChange(event.target.value)}
                  value={authorMacroObjectCode}
                >
                  {(catalogMacroObjects.data?.items ?? []).map((macroObject) => (
                    <option key={macroObject.code} value={macroObject.code}>
                      {macroObject.code} - {macroObject.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div aria-label={`Catalog tables for ${authorMacroObjectCode}`} className="master-data-column-picker">
              {(catalogAuthorTables.data?.items ?? []).map((table) => (
                <label key={table.table_name}>
                  <input
                    aria-label={table.table_name}
                    checked={authorTables.includes(table.table_name)}
                    disabled={table.is_primary_table && authorTables.includes(table.table_name)}
                    onChange={() => handleToggleAuthorTable(table.table_name)}
                    type="checkbox"
                  />
                  <span>{table.table_name}</span>
                  <small>{table.relationship_role}</small>
                </label>
              ))}
            </div>
            {authorTables.map((tableName) => (
              <div aria-label={`Catalog columns for ${tableName}`} className="master-data-column-picker" key={tableName}>
                {(authorColumnsCatalog.byTable[tableName] ?? []).map((column) => (
                  <label key={column.column_name}>
                    <input
                      aria-label={column.column_name}
                      checked={(authorColumnsByTable[tableName] ?? []).includes(column.column_name)}
                      onChange={() => handleToggleAuthorTableColumn(tableName, column.column_name)}
                      type="checkbox"
                    />
                    <span>{column.column_name}</span>
                    <small>{column.data_type}</small>
                  </label>
                ))}
              </div>
            ))}
            <div aria-label="Authoring mapping editor" className="master-data-mapping-editor">
              {authorSelectedColumns.map(({ columnName, key, tableName }) => {
                const config = authorMappingConfigByKey[key] ?? {};
                const sourceType = config.sourceType ?? defaultSourceType(tableName, columnName);
                return (
                  <div className="master-data-mapping-row" key={key}>
                    <strong>{key}</strong>
                    {sourceType === "USER_FIELD" ? (
                      <label>
                        Friendly label
                        <input
                          aria-label={`Friendly label for ${key}`}
                          onChange={(event) => updateAuthorMappingConfig(key, { label: event.target.value })}
                          value={config.label ?? labelForColumn(columnName)}
                        />
                      </label>
                    ) : null}
                    <label>
                      Source type
                      <select
                        aria-label={`Source type for ${key}`}
                        onChange={(event) =>
                          updateAuthorMappingConfig(key, { sourceType: event.target.value as AuthorSourceType })
                        }
                        value={sourceType}
                      >
                        <option value="USER_FIELD">USER_FIELD</option>
                        <option value="FIXED_VALUE">FIXED_VALUE</option>
                        <option value="DEFAULT_VALUE">DEFAULT_VALUE</option>
                      </select>
                    </label>
                    {sourceType === "FIXED_VALUE" ? (
                      <label>
                        Fixed value
                        <input
                          aria-label={`Fixed value for ${key}`}
                          onChange={(event) => updateAuthorMappingConfig(key, { fixedValue: event.target.value })}
                          value={config.fixedValue ?? defaultFixedValue(tableName, columnName)}
                        />
                      </label>
                    ) : null}
                    {sourceType === "DEFAULT_VALUE" ? (
                      <label>
                        Default value
                        <input
                          aria-label={`Default value for ${key}`}
                          onChange={(event) => updateAuthorMappingConfig(key, { defaultValue: event.target.value })}
                          value={config.defaultValue ?? ""}
                        />
                      </label>
                    ) : null}
                  </div>
                );
              })}
            </div>
            {authorTables.includes("LOCATION_ADDRESS") ? (
              <div aria-label="Authoring relationship rules" className="master-data-relationship-editor">
                <label>
                  <input
                    aria-label="Require LOCATION parent for LOCATION_ADDRESS"
                    checked={includeLocationAddressRelationship}
                    disabled={!(authorColumnsByTable.LOCATION_ADDRESS ?? []).includes("LOCATION_GID")}
                    onChange={(event) => setIncludeLocationAddressRelationship(event.target.checked)}
                    type="checkbox"
                  />
                  <span>Require LOCATION parent for LOCATION_ADDRESS</span>
                  <small>LOCATIONS.location_gid -&gt; LOCATION_ADDRESS.location_address_location_gid</small>
                </label>
              </div>
            ) : null}
            <DetailList
              ariaLabel="Authoring mapping preview"
              items={[
                {
                  id: "author-draft-preview",
                  meta: [
                    `${authorDraftPreview.fields.length} user field(s)`,
                    `${authorDraftPreview.mappings.length} OTM mapping(s)`,
                    `${authorDraftPreview.relationship_rules.length} relationship rule(s)`,
                    authorDraftPreview.documentation_refs.map((ref) => ref.source_type).join(" + ")
                  ],
                  status: "READY",
                  title: authorDraftPreview.target_tables.map((table) => table.table_name).join(" + ")
                }
              ]}
            />
            <div className="master-data-action-bar">
              <Button
                disabled={isMutating || !selectedTemplate?.definition}
                onClick={handleLoadSelectedTemplateIntoAuthor}
                variant="secondary"
              >
                Load selected template
              </Button>
              <Button disabled={isMutating || !authorTemplateCode.trim()} onClick={handleCreateDraft} variant="primary">
                Create draft
              </Button>
              <Button disabled={isMutating || !authorTemplate} onClick={handleUpdateDraft} variant="secondary">
                Update draft
              </Button>
              <Button
                disabled={
                  isMutating || masterDataTemplateActionDisabled(authorTemplate, "validate_definition", !authorTemplate)
                }
                onClick={handleValidateDefinition}
                title={masterDataTemplateActionReason(authorTemplate, "validate_definition")}
                variant="secondary"
              >
                Validate definition
              </Button>
              <Button
                disabled={
                  isMutating ||
                  masterDataTemplateActionDisabled(
                    authorTemplate,
                    "publish_template",
                    !authorTemplate || authorValidation?.valid === false
                  ) ||
                  authorValidation?.valid === false
                }
                onClick={handlePublishTemplate}
                title={masterDataTemplateActionReason(authorTemplate, "publish_template")}
                variant="secondary"
              >
                Publish template
              </Button>
              <Button
                disabled={isMutating || masterDataTemplateActionDisabled(authorTemplate, "create_version", !authorTemplate)}
                onClick={handleCreateVersion}
                title={masterDataTemplateActionReason(authorTemplate, "create_version")}
                variant="secondary"
              >
                Create next version
              </Button>
            </div>
            {authorTemplate ? (
              <DetailList
                ariaLabel="Authoring result"
                items={[
                  {
                    id: authorTemplate.id,
                    meta: [
                      authorTemplate.catalog_macro_object_code,
                      `v${authorTemplate.version}`,
                      `${authorTemplate.target_tables.length} table(s)`
                    ],
                    status: authorTemplate.status,
                    title: authorTemplate.code
                  }
                ]}
              />
            ) : null}
            {authorValidation ? (
              <BlockerPanel
                emptyText="Definition validation has no blockers."
                items={authorValidation.issues.map((issue) => ({
                  codes: [issue.code],
                  id: issue.code,
                  message: issue.message
                }))}
                title="Definition validation issues"
              />
            ) : null}
            {authorVersion ? (
              <DetailList
                ariaLabel="Version result"
                items={[
                  {
                    id: authorVersion.id,
                    meta: [authorVersion.code, `v${authorVersion.version}`],
                    status: authorVersion.status,
                    title: authorVersion.name
                  }
                ]}
              />
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "workbook" ? (
          <OperationalPanel
            ariaLabel="Template workbook workflow"
            emptyText="Select a template before generating workbook artifacts."
            hasItems={Boolean(effectiveTemplateCode)}
            status={templateValidation?.valid ? "VALID" : workbookArtifact?.template_code ? "GENERATED" : "PENDING"}
            title="Workbook"
          >
            <div className="master-data-action-bar">
              <Button disabled={!effectiveTemplateCode || isMutating} onClick={handleValidateTemplate} variant="primary">
                Validate template
              </Button>
              <Button
                disabled={
                  isMutating ||
                  masterDataTemplateActionDisabled(selectedTemplate, "build_workbook", !effectiveTemplateCode)
                }
                onClick={handleBuildWorkbook}
                title={masterDataTemplateActionReason(selectedTemplate, "build_workbook")}
                variant="secondary"
              >
                Build workbook
              </Button>
            </div>
            {templateValidation ? (
              <>
                <DetailList
                  ariaLabel="Template validation summary"
                  items={[
                    {
                      id: "template-validation",
                      meta: [
                        `${templateValidation.summary.sheet_count} sheets`,
                        `${templateValidation.summary.field_count} fields`,
                        `${templateValidation.summary.validated_table_count} tables`
                      ],
                      status: templateValidation.valid ? "VALID" : templateValidation.severity,
                      title: templateValidation.valid ? "VALID" : templateValidation.severity
                    }
                  ]}
                />
                <BlockerPanel
                  emptyText="Template validation has no blockers."
                  items={templateValidation.issues.map((issue) => ({
                    codes: [issue.code],
                    id: issue.code,
                    message: issue.message
                  }))}
                  title="Template validation issues"
                />
              </>
            ) : null}
            {workbookArtifact ? (
              <DetailList
                ariaLabel="Workbook artifact"
                items={[
                  {
                    id: workbookArtifact.artifact_id,
                    meta: [
                      workbookArtifact.artifact_id,
                      `${workbookArtifact.sheet_count} sheets`,
                      `${workbookArtifact.field_count} fields`
                    ],
                    status: "GENERATED",
                    title: workbookArtifact.file_name
                  }
                ]}
              />
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "upload" ? (
          <OperationalPanel
            ariaLabel="Workbook upload workflow"
            emptyText="Build or choose a workbook before uploading a batch."
            hasItems={Boolean(effectiveTemplateCode)}
            status={activeBatch?.status ?? "PENDING"}
            title="Upload"
          >
            <div className="master-data-action-bar">
              <label>
                Workbook file
                <input
                  accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  onChange={(event) => setSelectedUploadFile(event.target.files?.[0] ?? null)}
                  type="file"
                />
              </label>
              <Button disabled={!effectiveTemplateCode || !selectedUploadFile || isMutating} onClick={handleUploadWorkbook} variant="primary">
                Upload workbook
              </Button>
            </div>
            {activeBatch ? (
              <DetailList
                ariaLabel="Active batch summary"
                items={[
                  {
                    id: activeBatch.batch_id,
                    meta: [
                      activeBatch.template_code,
                      activeBatch.file_name ?? "Uploaded workbook",
                      `${activeBatch.row_count ?? 0} row(s)`
                    ],
                    status: activeBatch.status,
                    title: activeBatch.batch_id
                  }
                ]}
              />
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "validate" ? (
          <OperationalPanel
            ariaLabel="Relationship validation workflow"
            emptyText="Upload a batch before validating relationships."
            hasItems={Boolean(activeBatch)}
            status={relationshipValidation?.valid ? "VALID" : relationshipValidation?.status ?? "PENDING"}
            title="Validate"
          >
            <div className="master-data-action-bar">
              <Button
                disabled={isMutating || masterDataActionDisabled(activeBatch, "validate_relationships", !activeBatch)}
                onClick={handleValidateRelationships}
                title={masterDataActionReason(activeBatch, "validate_relationships")}
                variant="primary"
              >
                Validate relationships
              </Button>
            </div>
            {relationshipValidation ? (
              <>
                <DetailList
                  ariaLabel="Relationship validation summary"
                  items={[
                    {
                      id: "relationship-validation",
                      meta: summaryMeta(relationshipValidation.summary),
                      status: relationshipValidation.valid ? "VALID" : relationshipValidation.status,
                      title: relationshipValidation.valid ? "VALID" : relationshipValidation.status
                    }
                  ]}
                />
                <BlockerPanel
                  emptyText="Relationship validation has no blockers."
                  items={relationshipValidation.issues.map((issue) => ({
                    codes: [issue.code],
                    id: `${issue.code}-${issue.row_number ?? "batch"}`,
                    message: issue.message
                  }))}
                  title="Relationship validation issues"
                />
              </>
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "map" ? (
          <OperationalPanel
            ariaLabel="Mapping workflow"
            emptyText="Upload a batch before mapping records."
            hasItems={Boolean(activeBatch)}
            status={mappingResult?.status ?? "PENDING"}
            title="Map"
          >
            <div className="master-data-action-bar">
              <Button
                disabled={isMutating || masterDataActionDisabled(activeBatch, "map_records", !activeBatch)}
                onClick={handleMapBatch}
                title={masterDataActionReason(activeBatch, "map_records")}
                variant="primary"
              >
                Map records
              </Button>
            </div>
            {mappingResult ? (
              <DetailList
                ariaLabel="Mapping summary"
                items={[
                  {
                    id: "mapping-result",
                    meta: summaryMeta(mappingResult.summary),
                    status: mappingResult.status,
                    title: mappingResult.status
                  }
                ]}
              />
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "output" ? (
          <OperationalPanel
            ariaLabel="Output and export workflow"
            emptyText="Upload a batch before generating output artifacts."
            hasItems={Boolean(activeBatch)}
            status={exportResult?.status ?? csvResult?.status ?? outputResult?.status ?? "PENDING"}
            title="Output"
          >
            <div className="master-data-action-bar master-data-output-actions">
              <Button
                disabled={isMutating || masterDataActionDisabled(activeBatch, "build_output", !activeBatch)}
                onClick={handleBuildOutput}
                title={masterDataActionReason(activeBatch, "build_output")}
                variant="primary"
              >
                Build output
              </Button>
              <Button
                disabled={isMutating || masterDataActionDisabled(activeBatch, "build_csv", !activeBatch)}
                onClick={handleBuildCsv}
                title={masterDataActionReason(activeBatch, "build_csv")}
                variant="secondary"
              >
                Build CSV
              </Button>
              <Button
                disabled={isMutating || masterDataActionDisabled(activeBatch, "export_csv_package", !activeBatch)}
                onClick={handleExportCsvPackage}
                title={masterDataActionReason(activeBatch, "export_csv_package")}
                variant="secondary"
              >
                Export package
              </Button>
              <Button
                disabled={
                  isMutating ||
                  masterDataActionDisabled(activeBatch, "register_load_plan_package", !canRegisterLoadPlanPackage)
                }
                onClick={handleRegisterLoadPlanPackage}
                title={masterDataActionReason(activeBatch, "register_load_plan_package")}
                variant="secondary"
              >
                Register for Load Plan
              </Button>
            </div>
            <DetailList
              ariaLabel="Output build summary"
              items={[
                outputResult
                  ? {
                      id: "output-result",
                      meta: summaryMeta(outputResult.summary),
                      status: outputResult.status,
                      title: outputResult.status
                    }
                  : null,
                csvResult
                  ? {
                      id: "csv-result",
                      meta: summaryMeta(csvResult.summary),
                      status: csvResult.status,
                      title: csvResult.status
                    }
                  : null
              ].filter((item): item is { id: string; meta: string[]; status: string; title: string } => Boolean(item))}
            />
            {exportResult ? (
              <DetailList
                ariaLabel="Export package summary"
                items={[
                  {
                    id: exportResult.artifact_id ?? "export-result",
                    meta: [
                      exportResult.artifact_id ?? "No artifact",
                      exportResult.manifest_id ?? "No manifest",
                      exportResult.file_name ?? "No file name"
                    ],
                    status: exportResult.status,
                    title: exportResult.status
                  }
                ]}
              />
            ) : null}
            {loadPlanPackage ? (
              <DetailList
                ariaLabel="Load Plan package registration"
                items={[
                  {
                    id: loadPlanPackage.id,
                    meta: [
                      loadPlanPackage.package_type,
                      loadPlanPackage.summary.catalog_macro_object_code ?? "No macro object",
                      `${loadPlanPackage.load_sequence.length} load step(s)`,
                      loadPlanPackage.evidence_id ?? "No evidence"
                    ],
                    status: loadPlanPackage.status,
                    title: loadPlanPackage.id
                  }
                ]}
              />
            ) : null}
            <div className="master-data-action-bar">
              <Button disabled={!loadPlanPackage || isMutating} onClick={handleCreateCutoverChecklist} variant="secondary">
                Create cutover checklist
              </Button>
            </div>
            {cutoverChecklist ? (
              <DetailList
                ariaLabel="Cutover checklist handoff"
                items={[
                  {
                    id: cutoverChecklist.id,
                    meta: [
                      cutoverChecklist.template_code ?? "No template",
                      cutoverChecklist.package_type,
                      `${cutoverChecklist.items.length} item(s)`,
                      cutoverChecklist.evidence_id ?? "No evidence"
                    ],
                    status: cutoverChecklist.status,
                    title: cutoverChecklist.id
                  }
                ]}
              />
            ) : null}
            <div className="master-data-action-bar">
              <Button
                disabled={!cutoverChecklist || isMutating}
                onClick={handleGenerateCutoverChecklistReadiness}
                variant="secondary"
              >
                Generate checklist readiness
              </Button>
            </div>
            {cutoverChecklistReadiness ? (
              <>
                <DetailList
                  ariaLabel="Cutover checklist readiness handoff"
                  items={[
                    {
                      id: cutoverChecklistReadiness.checklist_id,
                      meta: [
                        `${cutoverChecklistReadiness.summary.item_count} item(s)`,
                        `${cutoverChecklistReadiness.summary.blocker_count} blocker(s)`,
                        cutoverChecklistReadiness.evidence_id ?? "No evidence"
                      ],
                      status: cutoverChecklistReadiness.status,
                      title: cutoverChecklistReadiness.summary.ready ? "READY" : "REVIEW"
                    }
                  ]}
                />
                <BlockerPanel
                  emptyText="No readiness blockers returned by the backend."
                  items={cutoverChecklistReadiness.blockers.map((blocker, index) => ({
                    codes: [blocker.code, blocker.item_code ?? blocker.table_name ?? ""].filter(Boolean),
                    id: `${blocker.code}-${index}`,
                    message: blocker.message
                  }))}
                  title="Cutover checklist readiness blockers"
                />
              </>
            ) : null}
            <DetailList
              ariaLabel="Master Data output record preview"
              emptyText="Build output before previewing backend-owned OTM records."
              items={(outputRecords.data?.items ?? []).slice(0, 5).map((record) => ({
                id: record.id,
                meta: [
                  `#${record.record_index}`,
                  Object.keys(record.payload).join(", "),
                  JSON.stringify(record.payload).slice(0, 160)
                ],
                status: "OUTPUT",
                title: record.target_table
              }))}
            />
            <DetailList
              ariaLabel="Master Data CSV file preview"
              emptyText="Build CSV before previewing generated OTM CSV files."
              items={(csvFiles.data?.items ?? []).map((file) => ({
                id: file.id,
                meta: [`${file.row_count} row(s)`, `${file.line_count} line(s)`, file.content_preview],
                status: "CSV",
                title: file.file_name
              }))}
            />
            <div className="master-data-action-bar" aria-label="Master Data batch history filters">
              <label>
                Template filter
                <select
                  aria-label="Template filter"
                  onChange={(event) => {
                    setBatchTemplateFilter(event.target.value);
                    setBatchPage(1);
                  }}
                  value={batchTemplateFilter}
                >
                  <option value="">All templates</option>
                  {templateItems.map((template) => (
                    <option key={template.code} value={template.code}>
                      {template.code}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Batch status filter
                <select
                  aria-label="Batch status filter"
                  onChange={(event) => {
                    setBatchStatusFilter(event.target.value);
                    setBatchPage(1);
                  }}
                  value={batchStatusFilter}
                >
                  <option value="">All statuses</option>
                  <option value="PARSED">PARSED</option>
                  <option value="RELATIONSHIP_VALIDATED">RELATIONSHIP VALIDATED</option>
                  <option value="MAPPED">MAPPED</option>
                  <option value="OUTPUT_BUILT">OUTPUT BUILT</option>
                  <option value="CSV_BUILT">CSV BUILT</option>
                  <option value="EXPORTED">EXPORTED</option>
                </select>
              </label>
              <label>
                File name filter
                <input
                  aria-label="Batch file name filter"
                  onChange={(event) => {
                    setBatchFileNameFilter(event.target.value);
                    setBatchPage(1);
                  }}
                  value={batchFileNameFilter}
                />
              </label>
              <label>
                Minimum rows
                <input
                  aria-label="Batch minimum row count"
                  min="0"
                  onChange={(event) => {
                    setBatchMinRowCountFilter(event.target.value);
                    setBatchPage(1);
                  }}
                  type="number"
                  value={batchMinRowCountFilter}
                />
              </label>
              <label>
                Page size
                <select
                  aria-label="Batch page size"
                  onChange={(event) => {
                    setBatchPageSize(Number(event.target.value));
                    setBatchPage(1);
                  }}
                  value={batchPageSize}
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
              </label>
              <Button disabled={batchPage <= 1 || batches.isFetching} onClick={() => setBatchPage((page) => Math.max(1, page - 1))}>
                Previous
              </Button>
              <Button
                disabled={(batches.data?.total ?? 0) <= batchPage * batchPageSize || batches.isFetching}
                onClick={() => setBatchPage((page) => page + 1)}
              >
                Next
              </Button>
            </div>
            <MetricGrid
              ariaLabel="Master Data batch history metrics"
              items={[
                {
                  key: "batch-history-total",
                  label: "Matching batches",
                  status: booleanStatus(batchSummary.data?.total_batches ?? 0),
                  value: batchSummary.data?.total_batches ?? 0
                },
                {
                  key: "batch-history-rows",
                  label: "Matching rows",
                  status: booleanStatus(batchSummary.data?.total_rows ?? 0),
                  value: batchSummary.data?.total_rows ?? 0
                },
                {
                  key: "batch-history-issues",
                  label: "Issues",
                  status: batchSummary.data?.total_issues ? "REVIEW" : "OK",
                  value: batchSummary.data?.total_issues ?? 0
                },
                {
                  key: "batch-history-statuses",
                  label: "Statuses",
                  status: booleanStatus(batchSummary.data?.status_breakdown.length ?? 0),
                  value: batchSummary.data?.status_breakdown.length ?? 0
                }
              ]}
            />
            <DetailList
              ariaLabel="Durable Master Data batches"
              emptyText="No backend batches match the current filters."
              items={(batches.data?.items ?? []).map((batch) => ({
                id: batch.batch_id,
                meta: [
                  batch.template_code,
                  batch.file_name ?? "Uploaded workbook",
                  `${batch.row_count ?? 0} row(s)`,
                  `${batch.csv_file_count ?? 0} CSV file(s)`
                ],
                status: batch.status,
                title: batch.batch_id
              }))}
            />
            <section aria-label="Master Data export artifacts" className="master-data-generated-artifacts">
              <h3>Export artifacts</h3>
              {batchArtifacts.isLoading && activeBatch ? <p className="empty-text">Loading export artifacts...</p> : null}
              <ArtifactList
                items={(batchArtifacts.data?.items ?? []).map((artifact) => ({
                  action: artifact.download_url ? (
                    <Button
                      disabled={downloadingArtifactId === artifact.id}
                      onClick={() => void handleDownloadArtifact(artifact)}
                    >
                      {downloadingArtifactId === artifact.id ? "Downloading..." : "Download"}
                    </Button>
                  ) : undefined,
                  id: artifact.id,
                  meta: [artifact.content_type, `${artifact.size_bytes} bytes`, artifact.sha256],
                  status: artifact.availability_status ?? artifact.sensitivity_level,
                  subtitle: artifact.artifact_type,
                  title: artifact.file_name
                }))}
              />
            </section>
          </OperationalPanel>
        ) : null}

        {activeStage === "quality" ? (
          <OperationalPanel
            ariaLabel="Coordinate Quality workflow"
            emptyText="Use synthetic Location records to validate lat/lon quality before exporting a review package."
            hasItems
            status={coordinateExport ? "EXPORTED" : activeCoordinateBatch?.status ?? "READY"}
            title="Coordinate Quality"
          >
            <div className="master-data-author-grid">
              <label>
                Coordinate records JSON
                <textarea
                  aria-label="Coordinate records JSON"
                  onChange={(event) => setCoordinateRecordsJson(event.target.value)}
                  rows={10}
                  value={coordinateRecordsJson}
                />
              </label>
              <label>
                Fake geocoder candidates JSON
                <textarea
                  aria-label="Coordinate fake candidates JSON"
                  onChange={(event) => setCoordinateCandidatesJson(event.target.value)}
                  rows={10}
                  value={coordinateCandidatesJson}
                />
              </label>
            </div>
            <div className="master-data-action-bar master-data-output-actions">
              <Button disabled={isMutating} onClick={handlePreviewCoordinateQuality} variant="primary">
                Preview coordinates
              </Button>
              <Button disabled={isMutating} onClick={handleCreateCoordinateQualityBatch} variant="secondary">
                Create quality batch
              </Button>
              <Button disabled={isMutating || !activeCoordinateBatch} onClick={handleExportCoordinateQuality} variant="secondary">
                Export quality package
              </Button>
            </div>
            {coordinatePreview ? (
              <DetailList
                ariaLabel="Coordinate Quality preview summary"
                items={[
                  {
                    id: "coordinate-preview",
                    meta: summaryMeta(coordinatePreview.summary),
                    status: coordinatePreview.summary.failed_count ? "REVIEW" : "READY",
                    title: "Preview"
                  }
                ]}
              />
            ) : null}
            <DetailList
              ariaLabel="Coordinate Quality results"
              emptyText="No coordinate results available yet."
              items={(coordinateResults.data?.items ?? coordinatePreview?.results ?? []).map((result) => ({
                id: result.id ?? result.location_gid,
                meta: [
                  result.location_name ?? "No name",
                  `${result.lat_orig ?? "null"}, ${result.lon_orig ?? "null"}`,
                  `${result.lat_new ?? "null"}, ${result.lon_new ?? "null"}`,
                  result.source ?? "No source"
                ],
                status: result.status,
                title: result.location_gid
              }))}
            />
            <DetailList
              ariaLabel="Coordinate Quality batches"
              emptyText="No coordinate quality batches created yet."
              items={coordinateQualityBatchItems.map((batch) => ({
                id: batch.batch_id,
                meta: summaryMeta(batch.summary),
                status: batch.status,
                title: batch.batch_id
              }))}
            />
            {coordinateExport ? (
              <DetailList
                ariaLabel="Coordinate Quality export package"
                items={[
                  {
                    id: coordinateExport.artifact_id,
                    meta: [
                      coordinateExport.artifact_id,
                      coordinateExport.manifest_id,
                      coordinateExport.evidence_id,
                      `${coordinateExport.size_bytes} bytes`
                    ],
                    status: "EXPORTED",
                    title: coordinateExport.file_name
                  }
                ]}
              />
            ) : null}
          </OperationalPanel>
        ) : null}
      </ModuleWorkspaceLayout>
    </>
  );
}
