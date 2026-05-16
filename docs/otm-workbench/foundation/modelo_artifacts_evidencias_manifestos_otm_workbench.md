# Modelo de Artifacts, Evidências e Manifestos — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Documento:** padrão para arquivos gerados, evidências auditáveis, manifestos e pacotes de arquivo.  
**Objetivo:** garantir rastreabilidade, segurança e consistência em todos os módulos que geram outputs.

---

## 1. Conceitos

### 1.1 Artifact

Artifact é qualquer arquivo gerado, importado ou exportado pela aplicação.

Exemplos:

```text
- Planilha importada pelo cliente.
- Template Excel gerado.
- CSV OTM.
- ZIP de carga.
- XML de tarifa.
- Correction report.
- Archive package.
- MANIFEST.json.
```

### 1.2 Manifest

Manifest é um documento estruturado que descreve um artifact ou pacote.

Ele responde:

```text
- O que foi gerado?
- Por qual módulo?
- Para qual projeto/perfil/ambiente?
- Com quais arquivos?
- Em qual ordem?
- Com quais hashes?
- Com qual status?
- Quais validações foram aplicadas?
```

### 1.3 Evidence

Evidence é um registro auditável e client-safe de um resultado.

Ela responde:

```text
- Qual ação ocorreu?
- Quem executou?
- Quando executou?
- Qual foi o resultado?
- Qual artifact/manifest está relacionado?
- Existem blockers/issues?
- Pode ser mostrado ao cliente/usuário comum?
```

---

## 2. Regra central

```text
Artifact contém arquivo.
Manifest descreve arquivo/pacote.
Evidence resume resultado de forma segura.
```

Nunca usar evidence como depósito de payload bruto.

---

## 3. Estrutura local de arquivos

```text
~/.otm-workbench/
  workspaces/
    {workspace_id}/
      projects/
        {project_id}/
          artifacts/
            master_data/
              {batch_id}/
            rates/
              {batch_id}/
            load_plan/
              {load_plan_id}/
            evidence/
              {evidence_id}/
          manifests/
          archive/
          cache/
          temp/
```

---

## 4. Modelo Artifact

```json
{
  "id": "art_001",
  "workspace_id": "wrk_001",
  "project_id": "prj_001",
  "profile_id": "pfl_001",
  "source_module": "master_data",
  "source_entity_type": "batch",
  "source_entity_id": "bat_001",
  "artifact_type": "otm_csv_zip",
  "file_name": "master_data_regions_bat_001.zip",
  "file_path": "artifacts/master_data/bat_001/master_data_regions_bat_001.zip",
  "content_type": "application/zip",
  "size_bytes": 102400,
  "sha256": "...",
  "sensitivity_level": "CONFIDENTIAL",
  "manifest_id": "man_001",
  "created_by": "usr_001",
  "created_at": "2026-05-16T12:00:00Z"
}
```

---

## 5. Tipos de artifact

| Tipo | Descrição | Sensibilidade padrão |
|---|---|---|
| `template_excel` | Template para preenchimento | INTERNAL |
| `source_workbook` | Planilha recebida do cliente | CONFIDENTIAL |
| `source_csv` | CSV recebido do cliente | CONFIDENTIAL |
| `otm_csv` | CSV individual para OTM | CONFIDENTIAL |
| `otm_csv_zip` | ZIP com CSVs em ordem de carga | CONFIDENTIAL |
| `rate_xml` | XML de tarifa | CONFIDENTIAL |
| `csvutil_ctl` | Arquivo CTL | INTERNAL |
| `csvutil_cl` | Arquivo CL | INTERNAL |
| `manifest_json` | Manifesto do pacote | INTERNAL |
| `correction_report` | Relatório de correção | INTERNAL/CONFIDENTIAL |
| `evidence_archive` | Pacote consolidado de evidências | INTERNAL |
| `diagnostic_log` | Log técnico | CONFIDENTIAL |

---

## 6. Modelo Manifest

### 6.1 Estrutura padrão

```json
{
  "schema_version": "1.0",
  "manifest_id": "man_001",
  "manifest_type": "load_package",
  "source_module": "master_data",
  "source_entity_type": "batch",
  "source_entity_id": "bat_001",
  "workspace": {
    "id": "wrk_001",
    "name": "LATAM Projects"
  },
  "project": {
    "id": "prj_001",
    "name": "Ajinomoto OTM Rollout"
  },
  "profile": {
    "id": "pfl_001",
    "domain": "ABR"
  },
  "environment": {
    "id": "env_001",
    "name": "UAT",
    "is_production": false
  },
  "status": "READY",
  "generated_by": "usr_001",
  "generated_at": "2026-05-16T12:00:00Z",
  "validation_summary": {
    "errors": 0,
    "warnings": 2,
    "infos": 4
  },
  "files": [
    {
      "sequence": 10,
      "file_name": "REGION.csv",
      "object_code": "REGION",
      "row_count": 24,
      "sha256": "..."
    },
    {
      "sequence": 20,
      "file_name": "REGION_DETAIL.csv",
      "object_code": "REGION_DETAIL",
      "row_count": 120,
      "sha256": "..."
    }
  ],
  "artifacts": [
    {
      "artifact_id": "art_001",
      "artifact_type": "otm_csv_zip",
      "file_name": "master_data_regions_bat_001.zip",
      "sha256": "..."
    }
  ],
  "blockers": [],
  "warnings": [
    {
      "code": "LATLON_MISSING_OPTIONAL",
      "message": "Some locations do not have optional coordinates."
    }
  ]
}
```

---

## 7. Modelo Evidence

```json
{
  "id": "evd_001",
  "workspace_id": "wrk_001",
  "project_id": "prj_001",
  "profile_id": "pfl_001",
  "source_module": "master_data",
  "source_entity_type": "batch",
  "source_entity_id": "bat_001",
  "evidence_type": "master_data_load_package",
  "status": "GENERATED",
  "client_safe": true,
  "summary": {
    "title": "Master Data Load Package generated",
    "batch_status": "EXPORTED",
    "errors": 0,
    "warnings": 2,
    "artifact_count": 1,
    "manifest_id": "man_001"
  },
  "manifest_id": "man_001",
  "artifact_id": "art_001",
  "created_by": "usr_001",
  "created_at": "2026-05-16T12:00:00Z"
}
```

---

## 8. Regras client-safe

Evidence pode conter:

```text
- Status.
- Contagem de registros.
- Contagem de erros/warnings.
- Nome do módulo.
- Nome do artifact.
- Hash.
- ID do manifest.
- Mensagens de blocker sanitizadas.
```

Evidence não deve conter:

```text
- Senhas.
- Tokens.
- Headers de autenticação.
- Payload bruto OTM.
- Planilha inteira.
- CSV inteiro.
- XML inteiro.
- Dados confidenciais desnecessários.
```

---

## 9. Padrão de ZIP OTM

ZIP de carga deve conter:

```text
MANIFEST.json
files/
  010_REGION.csv
  020_REGION_DETAIL.csv
```

Ou, para packs maiores:

```text
MANIFEST.json
files/
  010_ITEM.csv
  020_SHIP_UNIT_SPEC.csv
  030_PACKAGED_ITEM.csv
  040_TI_HI.csv
reports/
  correction_report.json
```

Regras:

```text
- Ordem numérica explícita.
- MANIFEST.json na raiz.
- Hash de cada arquivo no manifest.
- Row count de cada arquivo.
- Object code de cada arquivo.
- Nenhum arquivo temporário.
```

---

## 10. Correction report

Correction report deve ajudar cliente/consultor a corrigir dados.

Campos mínimos:

```json
{
  "report_id": "corr_001",
  "batch_id": "bat_001",
  "generated_at": "2026-05-16T12:00:00Z",
  "summary": {
    "errors": 3,
    "warnings": 5
  },
  "issues": [
    {
      "severity": "ERROR",
      "code": "MISSING_REQUIRED_FIELD",
      "object_type": "REGION",
      "row_number": 12,
      "field_name": "REGION_GID",
      "message": "Required field is missing.",
      "suggested_fix": "Fill REGION_GID using the project domain prefix."
    }
  ]
}
```

---

## 11. Archive package

Evidence Hub pode gerar pacote consolidado.

Estrutura:

```text
evidence_archive_{project}_{timestamp}.zip
  ARCHIVE_MANIFEST.json
  evidence/
    evd_001.json
    evd_002.json
  manifests/
    man_001.json
    man_002.json
  artifacts/
    allowed_artifacts_only/
  reports/
    summary.html ou summary.md
```

Regras:

```text
- Incluir apenas artifacts permitidos.
- Excluir SECRET.
- CONFIDENTIAL só entra se política permitir.
- Registrar audit log de geração/download.
```

---

## 12. Relação entre módulos e artifacts

| Módulo | Artifacts esperados | Evidence esperada |
|---|---|---|
| Data Factory | templates, source workbook, CSVs, ZIP, manifest, correction report | batch summary, load package evidence |
| Rates Studio | template, workbook, XML, CSV, CRP package, correction report | rate validation/export evidence |
| Load Plan | CTL, CL, ZIP analysis, readiness manifest | load plan readiness evidence |
| Cutover | checklist, package, execution report | cutover execution evidence |
| Evidence Hub | archive package | archive evidence |

---

## 13. Validações obrigatórias

Todo artifact deve ter:

```text
[ ] source_module
[ ] source_entity_type
[ ] source_entity_id
[ ] artifact_type
[ ] file_name
[ ] file_path
[ ] content_type
[ ] size_bytes
[ ] sha256
[ ] sensitivity_level
[ ] created_by
[ ] created_at
```

Todo manifest deve ter:

```text
[ ] schema_version
[ ] manifest_id
[ ] manifest_type
[ ] source_module
[ ] project/profile/environment
[ ] status
[ ] generated_by
[ ] generated_at
[ ] files/artifacts
[ ] validation_summary
```

Toda evidence deve ter:

```text
[ ] source_module
[ ] source_entity_type
[ ] source_entity_id
[ ] evidence_type
[ ] status
[ ] client_safe
[ ] summary
[ ] manifest_id ou justification
[ ] created_by
[ ] created_at
```

---

## 14. Anti-patterns

```text
- ZIP sem MANIFEST.json.
- Evidence contendo CSV/XML completo.
- Artifact sem hash.
- Artifact sem sensitivity_level.
- Download sem audit log.
- Arquivo grande salvo no banco.
- Manifest sem origem do módulo.
- Correction report sem suggested_fix.
- Archive package incluindo SECRET.
```
