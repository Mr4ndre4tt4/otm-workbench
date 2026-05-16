# Glossário e Convenções — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Documento:** glossário de termos, nomes, status, rotas, arquivos e convenções para manter consistência entre backend, frontend e documentação.  
**Objetivo:** evitar ambiguidade e padronizar a linguagem da aplicação.

---

## 1. Glossário funcional

| Termo | Definição |
|---|---|
| Workbench | Bancada operacional para apoiar projetos OTM antes, durante e depois da carga. |
| Workspace | Espaço de colaboração que pode conter vários projetos. |
| Project | Projeto OTM específico, normalmente vinculado a um cliente/rollout. |
| Profile | Contexto operacional local, com domínio, ambiente, preferências e isolamento. |
| Environment | Ambiente de trabalho, como DEV, TEST, UAT, PROD ou SANDBOX. |
| Module | Unidade funcional da aplicação, como Data Factory, Rates ou Load Plan. |
| Capability | Permissão granular para executar uma ação. |
| Feature Flag | Chave de habilitação/desabilitação de funcionalidade. |
| Data Factory | Módulo de Dados Mestres, intake, validação, conversão e export OTM CSV. |
| Template Pack | Conjunto de templates orientados a um pack de negócio. |
| Batch | Lote importado/processado dentro de um módulo. |
| Validation Issue | Problema encontrado durante validação. |
| Load Package | Pacote de carga pronto ou parcialmente pronto para OTM. |
| Load Plan | Planejamento de carga, sequência, CSVUTIL, review e readiness. |
| Cutover Readiness | Status de preparação para execução/cutover. |
| Artifact | Arquivo importado, gerado ou exportado. |
| Manifest | Descrição estruturada de um artifact/pacote. |
| Evidence | Registro auditável e client-safe de uma ação/resultado. |
| Domain Event | Evento interno publicado quando algo relevante acontece. |
| Change Request | Solicitação governada para mudança crítica. |
| Data Dictionary | Referência de objetos/campos/dependências OTM. |
| FK Catalog | Catálogo de dependências entre objetos/tabelas. |
| Dev-only | Funcionalidade técnica escondida do usuário comum. |

---

## 2. Convenção de nomes de módulos

Usar snake_case no backend e kebab-case nas URLs.

| Nome funcional | Module ID | URL base |
|---|---|---|
| Data Factory | `master_data` | `/data-factory` |
| Rates Studio | `rates` | `/rates` |
| Load Plan & Cutover | `load_plan` | `/load-plan` |
| Evidence Hub | `evidence` | `/evidence` |
| Admin Console | `admin` | `/admin` |
| Dictionary | `dictionary` | `/dictionary` |
| Lat/Lon Quality | `latlon_quality` | `/data-factory/coordinate-quality` |
| OTM Connector | `otm_connector` | `/admin/otm-connection` |

---

## 3. Convenção de capabilities

Formato:

```text
{module}.{resource}.{action}
```

Exemplos:

```text
master_data.batch.read
master_data.batch.create
master_data.batch.validate
master_data.package.export
rates.batch.approve
load_plan.csvutil.generate
evidence.artifact.download
admin.user.manage
```

Ações recomendadas:

```text
read
create
update
delete
validate
convert
approve
reject
export
download
configure
execute
view_sensitive
```

---

## 4. Convenção de eventos

Formato:

```text
{module}.{aggregate}.{event}
```

Exemplos:

```text
master_data.batch.created
master_data.batch.validated
master_data.load_package.generated
rates.batch.approved
load_plan.readiness.generated
evidence.artifact.created
admin.change_request.approved
```

Eventos devem ser escritos no passado, porque representam algo já ocorrido.

---

## 5. Convenção de rotas API

Todas as rotas públicas devem usar:

```text
/api/v1/...
```

Rotas de plataforma:

```text
/api/v1/platform/...
```

Rotas de módulos:

```text
/api/v1/modules/{module-id}/...
```

Exemplo:

```text
/api/v1/modules/master-data/batches
/api/v1/modules/rates/batches
/api/v1/modules/load-plan/summary
```

---

## 6. Convenção de arquivos

### 6.1 Python

```text
api.py
schemas.py
models.py
repository.py
service.py
policies.py
events.py
jobs.py
artifacts.py
evidence.py
```

### 6.2 Frontend

```text
ModuleRoutes.tsx
ModulePage.tsx
ModuleListPage.tsx
ModuleDetailPage.tsx
module.api.ts
module.types.ts
module.manifest.ts
```

### 6.3 Markdown

```text
arquitetura_tecnica_otm_workbench.md
arquitetura_funcional_otm_workbench.md
arquitetura_uiux_frontend_otm_workbench.md
guia_desenvolvimento_modular_otm_workbench.md
modelo_dados_contratos_api_otm_workbench.md
```

---

## 7. Convenção de status

### 7.1 Batch

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

### 7.2 Job

```text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

### 7.3 Evidence

```text
DRAFT
GENERATED
PUBLISHED
ARCHIVED
```

### 7.4 Change Request

```text
DRAFT
SUBMITTED
APPROVED
REJECTED
APPLIED
ROLLED_BACK
```

### 7.5 Operational status de UI

```text
not_started
in_progress
attention
blocked
ready
completed
archived
```

---

## 8. Convenção de severidade

```text
ERROR
WARNING
INFO
```

Regras:

```text
ERROR bloqueia conversão/exportação.
WARNING permite seguir, mas deve ser mostrado.
INFO é informativo e não bloqueia.
```

---

## 9. Convenção de sensitivity_level

```text
PUBLIC
INTERNAL
CONFIDENTIAL
SECRET
```

Regras:

```text
PUBLIC pode ser exibido.
INTERNAL pode ser usado internamente.
CONFIDENTIAL exige controle de acesso.
SECRET nunca deve ser exibido ou sincronizado sem proteção.
```

---

## 10. Convenção de nomes de artifacts

Formato recomendado:

```text
{module}_{entity}_{id}_{artifact_type}_{timestamp}.{ext}
```

Exemplos:

```text
master_data_batch_bat_001_otm_csv_zip_20260516.zip
rates_batch_rbat_001_rate_xml_20260516.xml
load_plan_lp_001_readiness_manifest_20260516.json
evidence_project_prj_001_archive_20260516.zip
```

---

## 11. Convenção de actions na UI

Ação primária por estado:

| Estado | Ação primária |
|---|---|
| `DRAFT` | Upload / Continue setup |
| `UPLOADED` | Validate |
| `BLOCKED` | Review issues |
| `READY_TO_CONVERT` | Convert |
| `CONVERTED` | Export package |
| `EXPORTED` | View evidence |
| `EVIDENCE_GENERATED` | Download / Archive |

---

## 12. Termos que devem ser evitados

Evitar nomes genéricos:

```text
- data
- stuff
- misc
- helper
- temp
- util2
- new_module
- test_final
```

Preferir nomes de domínio:

```text
- load_package
- validation_issue
- cutover_readiness
- artifact_manifest
- evidence_record
- template_pack
```

---

## 13. Convenção para documentação

Cada documento deve conter:

```text
- Data de referência.
- Objetivo.
- Escopo.
- Decisões.
- Critérios de aceite.
- Checklist ou exemplos quando aplicável.
```

Cada módulo deve ter documentação mínima:

```text
- Objetivo funcional.
- Entidades.
- APIs.
- Capabilities.
- Eventos.
- Artifacts/evidências.
- Testes.
```
