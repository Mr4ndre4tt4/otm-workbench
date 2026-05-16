# Modelo de Dados e Contratos de API — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Documento:** modelo canônico de dados, entidades, lifecycles e contratos de API para a nova aplicação.  
**Objetivo:** garantir que frontend, backend e módulos usem a mesma linguagem de dados desde o início.

---

## 1. Princípios

```text
1. Contratos primeiro, tela depois.
2. Backend é fonte da verdade para estado, permissão e navegação.
3. Todo objeto operacional tem lifecycle.
4. Todo arquivo gerado vira Artifact.
5. Todo resultado auditável vira Evidence.
6. Todo módulo publica eventos quando altera estado relevante.
7. IDs são estáveis e não dependem de nomes visíveis.
8. Dados sensíveis são mascarados, criptografados ou referenciados.
```

---

## 2. Convenção de IDs

Usar prefixos semânticos ajuda na leitura de logs, eventos e evidências.

| Entidade | Prefixo | Exemplo |
|---|---|---|
| Workspace | `wrk_` | `wrk_01HXABC` |
| Project | `prj_` | `prj_01HXABC` |
| Profile | `pfl_` | `pfl_01HXABC` |
| Environment | `env_` | `env_01HXABC` |
| User | `usr_` | `usr_01HXABC` |
| Module | `mod_` ou ID natural | `master_data` |
| Batch | `bat_` | `bat_01HXABC` |
| Job | `job_` | `job_01HXABC` |
| Artifact | `art_` | `art_01HXABC` |
| Evidence | `evd_` | `evd_01HXABC` |
| Manifest | `man_` | `man_01HXABC` |
| Event | `evt_` | `evt_01HXABC` |
| Change Request | `chg_` | `chg_01HXABC` |
| Load Package | `lpkg_` | `lpkg_01HXABC` |
| Rate Batch | `rbat_` | `rbat_01HXABC` |

Recomendação técnica: usar UUIDv7, ULID ou NanoID ordenável. O importante é manter consistência e evitar IDs sequenciais previsíveis em cloud.

---

## 3. Entidades de plataforma

### 3.1 Workspace

Representa um espaço de colaboração.

Campos mínimos:

```text
id
name
mode: LOCAL | SHARED | HYBRID
created_by
created_at
updated_at
```

### 3.2 Project

Representa um projeto OTM.

```text
id
workspace_id
name
client_name
project_code
default_domain
status: ACTIVE | PAUSED | ARCHIVED
created_by
created_at
updated_at
```

### 3.3 Profile

Representa contexto operacional local por cliente/projeto/ambiente.

```text
id
workspace_id
project_id
name
domain_name
default_environment_id
local_storage_path
is_active
created_at
updated_at
```

### 3.4 Environment

Representa ambiente OTM ou contexto de execução.

```text
id
project_id
name
kind: DEV | TEST | UAT | PROD | SANDBOX | LOCAL
base_url
is_production
connection_status
last_connection_test_at
created_at
updated_at
```

### 3.5 User

```text
id
display_name
email
status: ACTIVE | DISABLED
local_only: boolean
created_at
updated_at
```

### 3.6 Role

Papéis recomendados:

```text
USER
ADMIN
DBA
MASTER
```

### 3.7 Capability

Permissão granular.

```text
id
key
module_id
resource
action
description
```

Exemplo:

```text
master_data.batch.validate
```

### 3.8 UserProjectRole

Vincula usuário a projeto/workspace.

```text
id
workspace_id
project_id
user_id
role
capabilities_override_json
created_at
updated_at
```

---

## 4. Entidades de módulo e plataforma operacional

### 4.1 Module

```text
id
name
version
enabled
public
admin_only
dev_only
manifest_json
created_at
updated_at
```

### 4.2 FeatureFlag

```text
id
key
scope: GLOBAL | WORKSPACE | PROJECT | PROFILE | USER
enabled
value_json
created_by
created_at
updated_at
```

### 4.3 Job

```text
id
workspace_id
project_id
profile_id
source_module
job_type
status: PENDING | RUNNING | SUCCEEDED | FAILED | CANCELLED
progress_percent
input_json
result_json
error_code
error_message
created_by
created_at
started_at
finished_at
```

### 4.4 Artifact

```text
id
workspace_id
project_id
profile_id
source_module
source_entity_type
source_entity_id
artifact_type
file_name
file_path
content_type
size_bytes
sha256
sensitivity_level: PUBLIC | INTERNAL | CONFIDENTIAL | SECRET
manifest_id
created_by
created_at
```

### 4.5 Manifest

```text
id
workspace_id
project_id
profile_id
source_module
source_entity_type
source_entity_id
manifest_type
status
summary_json
content_json
created_by
created_at
```

### 4.6 Evidence

```text
id
workspace_id
project_id
profile_id
source_module
source_entity_type
source_entity_id
evidence_type
status
client_safe
summary_json
manifest_id
artifact_id
created_by
created_at
```

### 4.7 DomainEvent

```text
id
event_type
source_module
workspace_id
project_id
profile_id
aggregate_type
aggregate_id
payload_json
status: NEW | PROCESSING | PROCESSED | FAILED
created_at
processed_at
```

### 4.8 AuditLog

```text
id
workspace_id
project_id
profile_id
actor_user_id
action
resource_type
resource_id
before_json
after_json
metadata_json
sensitivity_level
created_at
```

---

## 5. Entidades funcionais principais

### 5.1 TemplatePack

```text
id
module_id
pack_key
name
description
object_codes_json
required_dictionary_version
enabled
metadata_json
created_at
updated_at
```

Exemplos:

```text
regions
items_packaging
locations
```

### 5.2 Batch

```text
id
workspace_id
project_id
profile_id
module_id
batch_type
name
status
source_file_artifact_id
validation_summary_json
created_by
created_at
updated_at
```

### 5.3 ValidationIssue

```text
id
batch_id
module_id
severity: ERROR | WARNING | INFO
code
message
object_type
field_name
row_number
source_reference
suggested_fix
status: OPEN | RESOLVED | WAIVED
created_at
updated_at
```

### 5.4 LoadPackage

```text
id
workspace_id
project_id
profile_id
source_module
source_batch_id
status
manifest_id
zip_artifact_id
load_sequence_json
created_by
created_at
```

### 5.5 RateBatch

```text
id
workspace_id
project_id
profile_id
name
status
source_workbook_artifact_id
validation_summary_json
approval_status
approved_by
approved_at
created_at
updated_at
```

### 5.6 LoadPlan

```text
id
workspace_id
project_id
profile_id
name
status
summary_json
readiness_manifest_id
created_by
created_at
updated_at
```

### 5.7 CutoverReadiness

```text
id
load_plan_id
status: NOT_READY | READY_WITH_WARNINGS | READY | EXECUTED
blockers_json
required_evidence_json
manifest_id
created_at
updated_at
```

### 5.8 ChangeRequest

```text
id
workspace_id
project_id
profile_id
source_module
change_type
status: DRAFT | SUBMITTED | APPROVED | REJECTED | APPLIED | ROLLED_BACK
requested_by
approved_by
request_json
decision_json
rollback_json
created_at
updated_at
```

---

## 6. Lifecycles

### 6.1 Batch lifecycle

```text
DRAFT
UPLOADED
STRUCTURE_VALIDATED
DATA_VALIDATED
BLOCKED
READY_TO_CONVERT
CONVERTED
EXPORTED
EVIDENCE_GENERATED
ARCHIVED
```

Regras:

```text
- BLOCKED exige issues abertas do tipo ERROR.
- READY_TO_CONVERT exige validação estrutural e de dados sem erro bloqueante.
- CONVERTED exige load package ou output intermediário.
- EXPORTED exige Artifact e Manifest.
- EVIDENCE_GENERATED exige Evidence client-safe.
```

### 6.2 Job lifecycle

```text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

### 6.3 Artifact lifecycle

```text
CREATED
AVAILABLE
QUARANTINED
DELETED
ARCHIVED
```

### 6.4 Evidence lifecycle

```text
DRAFT
GENERATED
PUBLISHED
ARCHIVED
```

### 6.5 Change Request lifecycle

```text
DRAFT
SUBMITTED
APPROVED
REJECTED
APPLIED
ROLLED_BACK
```

---

## 7. Convenções de API

### 7.1 Versionamento

Todas as APIs públicas devem usar:

```text
/api/v1/...
```

### 7.2 Resposta paginada

```json
{
  "items": [],
  "page": 1,
  "page_size": 50,
  "total": 0,
  "has_next": false
}
```

### 7.3 Erro padrão

```json
{
  "error": {
    "code": "MASTER_DATA_VALIDATION_FAILED",
    "message": "Batch contains unresolved dependencies.",
    "details": {
      "batch_id": "bat_001",
      "issue_count": 14
    }
  }
}
```

### 7.4 Status operacional

```json
{
  "status": "BLOCKED",
  "next_action": "Review validation issues",
  "blockers": [
    {
      "code": "MISSING_REGION_DETAIL",
      "message": "Region has no region detail rows."
    }
  ]
}
```

---

## 8. APIs de plataforma

### 8.1 Sessão e usuário

```text
GET    /api/v1/platform/me
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
```

### 8.2 Workspaces e projetos

```text
GET    /api/v1/platform/workspaces
POST   /api/v1/platform/workspaces
GET    /api/v1/platform/projects
POST   /api/v1/platform/projects
GET    /api/v1/platform/projects/{project_id}
PATCH  /api/v1/platform/projects/{project_id}
```

### 8.3 Perfis e ambientes

```text
GET    /api/v1/platform/profiles
POST   /api/v1/platform/profiles
POST   /api/v1/platform/profiles/{profile_id}/activate
GET    /api/v1/platform/environments
POST   /api/v1/platform/environments
POST   /api/v1/platform/environments/{environment_id}/test-connection
```

### 8.4 Módulos e navegação

```text
GET    /api/v1/platform/modules
GET    /api/v1/platform/navigation
GET    /api/v1/platform/capabilities
GET    /api/v1/platform/project-status
```

### 8.5 Jobs, artifacts e evidence

```text
GET    /api/v1/platform/jobs
GET    /api/v1/platform/jobs/{job_id}
POST   /api/v1/platform/jobs/{job_id}/cancel

GET    /api/v1/platform/artifacts
GET    /api/v1/platform/artifacts/{artifact_id}
GET    /api/v1/platform/artifacts/{artifact_id}/download

GET    /api/v1/platform/evidence
GET    /api/v1/platform/evidence/{evidence_id}
GET    /api/v1/platform/evidence/{evidence_id}/download
```

---

## 9. Contrato de navegação

```json
{
  "active_project": {
    "id": "prj_001",
    "name": "Ajinomoto OTM Rollout",
    "domain": "ABR",
    "environment": "UAT"
  },
  "role": "USER",
  "capabilities": [
    "master_data.batch.read",
    "master_data.batch.create"
  ],
  "modules": [
    {
      "id": "master_data",
      "label": "Data Factory",
      "enabled": true,
      "visible": true,
      "status": "attention",
      "next_action": "Validate imported batch",
      "route": "/data-factory/batches",
      "required_capabilities": ["master_data.batch.read"]
    }
  ]
}
```

Regras:

```text
- A UI renderiza o que o backend retorna.
- Módulo disabled não aparece para usuário comum.
- Dev-only só aparece com feature flag e capability.
- Status e next_action vêm do backend.
```

---

## 10. Contratos por módulo

### 10.1 Data Factory / Dados Mestres

```text
GET    /api/v1/modules/master-data/packs
GET    /api/v1/modules/master-data/packs/{pack_id}
POST   /api/v1/modules/master-data/batches
GET    /api/v1/modules/master-data/batches
GET    /api/v1/modules/master-data/batches/{batch_id}
POST   /api/v1/modules/master-data/batches/{batch_id}/validate
POST   /api/v1/modules/master-data/batches/{batch_id}/convert
POST   /api/v1/modules/master-data/batches/{batch_id}/export
GET    /api/v1/modules/master-data/batches/{batch_id}/issues
GET    /api/v1/modules/master-data/batches/{batch_id}/artifacts
GET    /api/v1/modules/master-data/batches/{batch_id}/evidence
```

### 10.2 Rates Studio

```text
GET    /api/v1/modules/rates/templates
POST   /api/v1/modules/rates/batches
GET    /api/v1/modules/rates/batches
GET    /api/v1/modules/rates/batches/{batch_id}
POST   /api/v1/modules/rates/batches/{batch_id}/validate
POST   /api/v1/modules/rates/batches/{batch_id}/approve
POST   /api/v1/modules/rates/batches/{batch_id}/export-xml
POST   /api/v1/modules/rates/batches/{batch_id}/export-csv
GET    /api/v1/modules/rates/batches/{batch_id}/issues
GET    /api/v1/modules/rates/batches/{batch_id}/evidence
```

### 10.3 Load Plan & Cutover

```text
GET    /api/v1/modules/load-plan/summary
GET    /api/v1/modules/load-plan/packages
POST   /api/v1/modules/load-plan/csvutil/build
POST   /api/v1/modules/load-plan/zip-analysis
GET    /api/v1/modules/load-plan/review-queue
POST   /api/v1/modules/load-plan/review-queue/{item_id}/decide
GET    /api/v1/modules/load-plan/sequence
GET    /api/v1/modules/load-plan/cutover-readiness
POST   /api/v1/modules/load-plan/cutover-readiness/export
GET    /api/v1/modules/load-plan/evidence
```

### 10.4 Evidence Hub

```text
GET    /api/v1/modules/evidence/dashboard
GET    /api/v1/modules/evidence/records
GET    /api/v1/modules/evidence/records/{evidence_id}
POST   /api/v1/modules/evidence/archive-package
GET    /api/v1/modules/evidence/archive-package/{package_id}/download
```

---

## 11. Modelo Pydantic base

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Literal

class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

class ApiErrorResponse(BaseModel):
    error: ApiError

class OperationalStatus(BaseModel):
    status: str
    next_action: str | None = None
    blockers: list[dict[str, Any]] = Field(default_factory=list)

class ArtifactRef(BaseModel):
    id: str
    artifact_type: str
    file_name: str
    sha256: str
    sensitivity_level: Literal['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'SECRET']

class EvidenceRef(BaseModel):
    id: str
    evidence_type: str
    status: str
    client_safe: bool
    created_at: datetime
```

---

## 12. Critérios de aceite dos contratos

```text
[ ] Toda API pública está em /api/v1.
[ ] Toda API tem request/response schema.
[ ] Todo erro usa o modelo padrão.
[ ] Toda lista usa paginação ou limite explícito.
[ ] Toda operação sensível valida capability no backend.
[ ] Todo batch expõe status e next_action.
[ ] Todo export retorna artifact_id e manifest_id.
[ ] Toda evidência retorna client_safe=true ou explica bloqueio.
[ ] Toda API de módulo tem teste de contrato.
```
