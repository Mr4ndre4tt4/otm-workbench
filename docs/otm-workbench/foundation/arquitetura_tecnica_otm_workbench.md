# OTM Project Workbench — Arquitetura Técnica

**Data de referência:** 2026-05-16  
**Objetivo:** definir a fundação técnica para reconstrução do OTM Project Workbench do zero, com foco em arquitetura, backend, stack, modularidade, escalabilidade, governança e preparação para colaboração futura.

---

## 1. Visão executiva

O OTM Project Workbench deve ser reconstruído como uma aplicação **local-first**, com backend robusto, modular e extensível. O foco inicial não é criar telas, mas sim construir uma fundação técnica que permita adicionar novos módulos de forma controlada, previsível e quase plugável.

A nova aplicação deve ser orientada por:

- **Backend como fonte da verdade** para navegação, permissões, módulos, capabilities, status e próximas ações.
- **Modular monolith** como arquitetura principal, evitando microserviços prematuros.
- **Persistência local simples e confiável**, com SQLite como banco principal local.
- **Execução pesada local**, usando workers e containers opcionais para serviços como geocoding, validação Lat/Lon e Oracle Lab.
- **Cloud opcional para colaboração**, com usuários, workspaces, evidências compartilhadas, manifests e sincronização.
- **Evidências client-safe**, sem expor payload técnico sensível.
- **Módulos funcionais isolados por contrato**, com manifesto, APIs, schemas, serviços, repositórios, eventos, artifacts, evidence producers e testes.

A decisão central é:

```text
Arquitetura alvo = Modular Monolith + Local-first + Cloud Sync opcional
```

---

## 2. Contexto do produto

O OTM Project Workbench é uma ferramenta interna para acelerar projetos Oracle Transportation Management. Ele não substitui o OTM; atua como bancada operacional para preparação de dados, validação, geração de arquivos de carga, tarifas, CSVUTIL, plano de carga, cutover, evidências e governança.

A aplicação atual já tem valor funcional, especialmente em:

- Dados Mestres.
- Validation & Rates.
- Plano de Carga / CSVUTIL.
- Cutover readiness.
- Reports & Evidence.
- Project Setup e Project Workflow.

A reconstrução deve preservar a lógica de domínio já validada, mas recriar a fundação com mais clareza arquitetural.

---

## 3. Princípios de arquitetura

### 3.1 Princípios gerais

1. **Local executa; cloud coordena.**
2. **Backend decide; frontend renderiza.**
3. **Módulo não importa outro módulo diretamente.**
4. **Integração entre módulos ocorre por eventos, contratos ou portas/interfaces.**
5. **Todo módulo tem manifesto.**
6. **Todo batch tem lifecycle.**
7. **Todo export tem manifest.**
8. **Todo artifact tem metadata, hash e origem.**
9. **Toda evidência deve ser client-safe.**
10. **Toda função pesada deve virar job.**
11. **Toda mudança crítica deve gerar audit log.**
12. **Todo endpoint público deve ter contrato e teste.**
13. **Ferramentas técnicas devem ficar atrás de capability, role ou feature flag.**
14. **Frontend nunca deve hardcodar permissão, menu ou status funcional.**
15. **Novos módulos não devem reinventar autenticação, jobs, artifacts, evidências ou permissões.**

### 3.2 Princípios funcionais

- Usuário comum não deve ver ações administrativas.
- Ferramentas técnicas não devem aparecer na navegação principal.
- O consultor deve ver fluxo guiado, próxima ação e bloqueios.
- O admin deve ver configuração, governança e permissões.
- O DBA/dev deve ver ferramentas técnicas somente quando autorizado.
- Cutover deve consumir Plano de Carga, não duplicar um asset manager paralelo.
- Reports & Evidence deve consumir manifestos e referências, não payload bruto sensível.

---

## 4. Decisão de arquitetura

### 4.1 Arquitetura escolhida

A arquitetura recomendada é um **modular monolith local-first**.

```text
Modular Monolith
+ Local-first execution
+ Optional cloud collaboration
+ Internal event bus
+ Module registry
+ Artifact/evidence platform
```

### 4.2 Por que não microserviços agora?

Microserviços não são recomendados para a primeira fase porque aumentariam complexidade sem necessidade imediata:

- Mais deploys.
- Mais observabilidade.
- Mais autenticação entre serviços.
- Mais problemas de rede.
- Mais dificuldade para rodar localmente.
- Mais acoplamento operacional para um produto ainda em reconstrução.

A aplicação precisa primeiro estabilizar domínio, contratos, lifecycle, evidências e estrutura de módulos.

### 4.3 Por que modular monolith?

O modular monolith permite:

- Uma única aplicação backend local.
- Uma única camada de autenticação e autorização.
- Um único banco local.
- Módulos separados por fronteira de domínio.
- Testes mais simples.
- Evolução posterior para microserviços, se necessário.
- Instalação local mais simples para consultores.

---

## 5. Stack recomendada

## 5.1 Stack principal

| Camada | Stack recomendada | Papel |
|---|---|---|
| Backend | Python 3.12+ | Linguagem principal da aplicação |
| API | FastAPI | Rotas HTTP, composição de app e contratos |
| Validação/contratos | Pydantic | Schemas, payloads, DTOs e validações |
| ORM | SQLAlchemy 2.x | Acesso ao banco com menor acoplamento |
| Migrations | Alembic | Versionamento do schema local/cloud |
| Banco local | SQLite | Estado transacional local da aplicação |
| Banco analítico opcional | DuckDB | Análise pesada de arquivos, CSV, Parquet e massas |
| Banco cloud | PostgreSQL | Colaboração, workspaces, usuários, manifests e sync |
| Cloud/BaaS opcional | Supabase | Auth, Postgres, Storage e Realtime se fizer sentido |
| UI futura | React + TypeScript + Vite | Frontend moderno após contratos estabilizados |
| Desktop wrapper | Tauri | Aplicação instalável e leve |
| Jobs locais | Worker interno inicial | Processamento assíncrono local |
| Containers locais | Docker Compose | Pelias, Oracle Lab, workers e serviços auxiliares |
| Testes | Pytest + httpx | Testes de unidade, API e contrato |
| Segurança | cryptography | Proteção de credenciais e campos sensíveis |

---

## 5.2 Stack backend inicial

A primeira fundação deve começar com:

```text
Python 3.12+
FastAPI
Pydantic
SQLAlchemy
Alembic
SQLite
Pytest
httpx
cryptography
openpyxl
lxml ou ElementTree
python-dotenv ou Pydantic Settings
```

Bibliotecas úteis por domínio:

```text
Excel/CSV:
- openpyxl
- pandas opcional, com cautela
- csv stdlib

XML/ZIP:
- lxml ou xml.etree.ElementTree
- zipfile stdlib

HTTP/integração:
- httpx

Segurança:
- cryptography
- passlib ou equivalente para hash de senha

Testes:
- pytest
- pytest-asyncio se necessário
- httpx TestClient/AsyncClient
```

---

## 5.3 Stack frontend

O frontend não deve ser o foco da primeira fase. A fundação deve começar pelo backend e contratos.

Recomendação:

```text
Fase 1:
- UI mínima ou Swagger/OpenAPI + endpoints testáveis.
- Pode usar frontend simples apenas para validar navegação e health.

Fase 2:
- React + TypeScript + Vite.
- Componentes por módulo.
- Navigation contract vindo do backend.

Fase 3:
- Tauri para empacotar app desktop.
```

A regra é: **não construir UI antes de estabilizar contratos de módulo, permissões, jobs, artifacts e evidências**.

---

## 6. Banco local: SQLite, DuckDB e Oracle

## 6.1 SQLite como banco principal local

SQLite deve ser o banco local principal da aplicação.

Usar SQLite para:

- Usuários locais.
- Sessões locais.
- Workspaces.
- Projetos.
- Perfis.
- Ambientes.
- Configurações.
- Feature flags.
- Module registry.
- Capabilities.
- Batches.
- Validation issues.
- Jobs.
- Artifacts metadata.
- Evidence metadata.
- Audit log.
- Domain events.
- Sync state.

Motivos:

- Simples de instalar.
- Não exige servidor.
- Combina com local-first.
- Reduz atrito para consultores.
- Permite backup simples.
- É suficiente para estado transacional local.

---

## 6.2 DuckDB como banco analítico opcional

DuckDB pode ser usado como motor analítico local opcional.

Usar DuckDB para:

- Ler CSVs grandes.
- Comparar massas de dados.
- Analisar ZIPs/arquivos.
- Gerar relatórios analíticos temporários.
- Fazer staging de grandes datasets.
- Consultar Parquet/CSV/JSON de forma eficiente.

Não usar DuckDB para:

- Sessão.
- RBAC.
- Lifecycle de batch.
- Jobs.
- Audit log.
- Estado transacional crítico.

---

## 6.3 Oracle local

Oracle local não deve ser usado como banco principal da aplicação.

Ele pode existir como módulo opcional:

```text
Oracle Lab / Oracle Compatibility Sandbox
```

Usar Oracle local para:

- Testar SQL Oracle específico.
- Simular comportamento Oracle em laboratório.
- Validar queries técnicas.
- Testar scripts e compatibilidade.
- Treinar cenários DBA/dev.
- Criar um ambiente técnico opcional.

Não usar Oracle local para:

- Estado principal da aplicação.
- Banco obrigatório para consultores.
- Sync colaborativo.
- Armazenamento principal de jobs/evidências.
- Setup padrão de instalação.

Motivo: Oracle local aumenta peso, complexidade, dependência de container/instalação, onboarding e manutenção. Para a aplicação principal, SQLite resolve melhor.

---

## 6.4 PostgreSQL cloud

PostgreSQL deve ser o banco recomendado para colaboração cloud.

Usar PostgreSQL cloud para:

- Workspaces compartilhados.
- Usuários do time.
- Permissões centralizadas.
- Projetos compartilhados.
- Evidence index.
- Artifact references.
- Manifestos compartilhados.
- Sync state.
- Auditoria colaborativa.

A nuvem não deve executar tudo. Ela deve coordenar e compartilhar o que faz sentido.

---

## 7. Arquitetura de alto nível

```text
┌─────────────────────────────────────────────────────────────┐
│                     OTM Workbench UI                        │
│        React/TypeScript no futuro ou UI mínima inicial       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP/API
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Local Backend API                         │
│                 Python + FastAPI + Pydantic                 │
├─────────────────────────────────────────────────────────────┤
│ Platform Core                                               │
│ - Auth / Session / RBAC                                     │
│ - Workspace / Project / Profile / Environment               │
│ - Module Registry                                           │
│ - Capability Registry                                       │
│ - Feature Flags                                             │
│ - Jobs / Workers                                            │
│ - Artifact Store                                            │
│ - Evidence Store                                            │
│ - Audit Log                                                 │
│ - Event Bus / Domain Events                                 │
│ - Sync Engine opcional                                      │
├─────────────────────────────────────────────────────────────┤
│ Business Modules                                            │
│ - Master Data                                               │
│ - Template & Mapping                                        │
│ - Rates                                                     │
│ - Load Plan / CSVUTIL                                       │
│ - Cutover Readiness                                         │
│ - Reports & Evidence                                        │
│ - OTM Connector                                             │
│ - Data Dictionary / FK Catalog                              │
│ - Lat/Lon Quality                                           │
│ - Oracle Lab opcional                                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌──────────────┐       ┌────────────────┐       ┌────────────────┐
│ SQLite local │       │ Local artifacts│       │ Local services │
│ app state    │       │ CSV/XML/ZIP    │       │ Pelias/Oracle  │
└──────────────┘       └────────────────┘       └────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Cloud Collaboration opcional                │
│        PostgreSQL/Supabase ou backend próprio                │
│ - Workspaces                                                 │
│ - Users/Roles                                                │
│ - Shared Projects                                            │
│ - Evidence manifests                                         │
│ - Artifact references                                        │
│ - Sync state                                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Platform Core

Antes de implementar módulos funcionais, a aplicação deve ter um núcleo de plataforma.

## 8.1 Componentes obrigatórios do Platform Core

```text
platform/
- config
- database
- migrations
- auth
- session
- rbac
- capabilities
- workspaces
- projects
- profiles
- environments
- module_registry
- feature_flags
- domain_events
- jobs
- artifacts
- evidence
- audit
- health
- sync opcional
```

---

## 8.2 Auth e sessão

Responsabilidades:

- Criar usuário inicial.
- Login/logout.
- Sessão local por cookie/token.
- Hash seguro de senha.
- Rate limit de login.
- Bootstrap inicial.
- Dependências de rota como `require_user`, `require_admin`, `require_capability`.

Papéis mínimos:

```text
USER
ADMIN
DBA
MASTER
```

---

## 8.3 RBAC e capabilities

A autorização deve ser baseada em capabilities, não apenas em role.

Exemplos:

```text
master_data.batch.create
master_data.batch.validate
master_data.package.export
rates.batch.upload
rates.batch.approve
rates.export.generate
load_plan.csvutil.generate
load_plan.readiness.view
evidence.artifact.download
admin.user.manage
admin.otm_connection.configure
dev.otm_explorer.access
dev.oracle_lab.access
```

Role define um conjunto de capabilities, mas o sistema deve permitir ajustes por perfil, projeto ou ambiente.

---

## 8.4 Workspace, Project, Profile e Environment

Modelo conceitual:

```text
Workspace
└── Project
    ├── Profile
    ├── Environment
    ├── OTMConnection
    ├── Modules
    ├── Batches
    ├── Jobs
    ├── Artifacts
    └── Evidence
```

Definições:

- **Workspace:** espaço colaborativo ou local.
- **Project:** projeto OTM específico.
- **Profile:** contexto de cliente/domínio/configuração.
- **Environment:** DEV, TEST, UAT, PROD ou ambiente customizado.
- **OTMConnection:** conexão OTM, admin-only, criptografada.

Todo registro relevante deve carregar:

```text
workspace_id
project_id
profile_id
environment_id
created_by
created_at
updated_at
source_module
```

---

## 8.5 Module Registry

O Module Registry é uma das peças mais importantes da fundação.

Ele deve responder:

```http
GET /api/v1/platform/modules
GET /api/v1/platform/navigation
GET /api/v1/platform/capabilities
GET /api/v1/platform/project-status
GET /api/v1/platform/health
```

O frontend não deve montar menu sozinho. O backend entrega algo como:

```json
{
  "module_id": "master_data",
  "label": "Dados Mestres",
  "enabled": true,
  "visible": true,
  "status": "attention",
  "next_action": "Validate imported batch",
  "route": "/master-data/batches",
  "required_capabilities": ["master_data.batch.create"]
}
```

---

## 8.6 Feature Flags

Feature flags devem controlar:

- Módulos em construção.
- Dev tools.
- OTM Explorer.
- Oracle Lab.
- Environment Compare.
- Cloud sync.
- Pelias/geocoding.
- Funcionalidades experimentais.

Exemplo:

```text
master_data.enabled
master_data.latlon_quality.enabled
rates.enabled
load_plan.enabled
cloud_sync.enabled
dev_tools.enabled
dev.otm_explorer.enabled
dev.oracle_lab.enabled
```

---

## 8.7 Domain Events

A comunicação entre módulos deve usar eventos internos.

Tabela sugerida:

```text
domain_events
- id
- event_type
- source_module
- project_id
- aggregate_type
- aggregate_id
- payload_json
- status
- created_at
- processed_at
- error_message
```

Status:

```text
PENDING
PROCESSING
PROCESSED
FAILED
IGNORED
```

Exemplos de eventos:

```text
master_data.batch.created
master_data.batch.validated
master_data.load_package.generated
rates.batch.uploaded
rates.batch.approved
rates.export.generated
load_plan.package.registered
load_plan.readiness.generated
evidence.artifact.created
cutover.package.exported
```

Regra de arquitetura:

```text
Módulo publica evento.
Outro módulo consome evento.
Módulo não chama diretamente service interno de outro módulo.
```

---

## 8.8 Job Engine

Toda tarefa pesada deve ser executada como job.

Tabela sugerida:

```text
jobs
- id
- job_type
- source_module
- project_id
- profile_id
- environment_id
- status
- progress
- input_json
- result_json
- error_message
- created_by
- created_at
- started_at
- finished_at
```

Status:

```text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

Exemplos de jobs:

```text
master_data.validate_batch
master_data.generate_load_package
rates.normalize_workbook
rates.validate_batch
rates.generate_xml
rates.generate_csv
latlon.validate_coordinates
load_plan.analyze_zip
load_plan.generate_csvutil
cutover.generate_readiness
reports.generate_archive
```

Na primeira versão, o worker pode ser interno. Depois, se necessário, pode evoluir para fila dedicada.

---

## 8.9 Artifact Store

Arquivos grandes não devem ser salvos diretamente no banco.

Banco salva metadata; filesystem salva arquivo.

Tabela sugerida:

```text
artifacts
- id
- project_id
- source_module
- source_entity_type
- source_entity_id
- artifact_type
- file_path
- file_name
- content_type
- sha256
- size_bytes
- manifest_id
- sensitivity_level
- created_by
- created_at
```

Tipos de artifacts:

```text
otm_csv_zip
manifest_json
rate_xml
rate_csv_zip
correction_report
crp_package
csvutil_ctl
csvutil_cl
cutover_package
evidence_archive
```

Estrutura local sugerida:

```text
~/.otm-workbench/
  workspaces/
    {workspace_id}/
      projects/
        {project_id}/
          artifacts/
            master_data/
            rates/
            load_plan/
            cutover/
            evidence/
          cache/
          temp/
          logs/
```

---

## 8.10 Evidence Store

Evidence Store deve ser transversal e client-safe.

Tabela sugerida:

```text
evidence_records
- id
- project_id
- source_module
- source_entity_type
- source_entity_id
- evidence_type
- status
- summary_json
- manifest_id
- artifact_id
- client_safe
- sensitivity_level
- created_by
- created_at
```

A evidência não deve conter payload técnico sensível cru.

Ela deve conter:

- Resumo seguro.
- Origem.
- Status.
- Referência ao artifact.
- Referência ao manifest.
- Hash.
- Usuário responsável.
- Timestamp.

---

## 8.11 Audit Log

Audit log deve registrar:

- Login/logout.
- Criação/alteração de usuários.
- Alteração de permissões.
- Configuração OTM.
- Mudança de feature flag.
- Geração de artifacts.
- Download de evidências.
- Aprovação de tarifas.
- Decisão de review queue.
- Mudança de catálogo.
- Rollback.

Tabela sugerida:

```text
audit_logs
- id
- actor_user_id
- action
- entity_type
- entity_id
- project_id
- before_json
- after_json
- metadata_json
- sensitivity_level
- created_at
```

Dados sensíveis devem ser mascarados antes de persistir.

---

## 9. Arquitetura modular

## 9.1 Contrato de módulo

Cada módulo funcional deve possuir:

```text
1. Manifesto do módulo
2. API router
3. Schemas Pydantic
4. Models SQLAlchemy
5. Repository
6. Services / use cases
7. Policies / rules
8. Events publicados
9. Event handlers consumidos
10. Artifact producers
11. Evidence producers
12. Capabilities
13. Migrations
14. Seeds
15. Tests
```

---

## 9.2 Estrutura de diretórios sugerida

```text
backend/
  app/
    main.py

    platform/
      auth/
      audit/
      config/
      database/
      events/
      jobs/
      artifacts/
      evidence/
      modules/
      permissions/
      workspaces/
      projects/
      profiles/
      environments/
      sync/
      health/

    modules/
      master_data/
        manifest.yaml
        api.py
        schemas.py
        models.py
        repository.py
        service.py
        policies.py
        events.py
        artifacts.py
        evidence.py
        migrations/
        seeds/
        tests/

      rates/
        manifest.yaml
        api.py
        schemas.py
        models.py
        repository.py
        service.py
        policies.py
        events.py
        artifacts.py
        evidence.py
        migrations/
        seeds/
        tests/

      load_plan/
        manifest.yaml
        api.py
        schemas.py
        models.py
        repository.py
        service.py
        policies.py
        events.py
        artifacts.py
        evidence.py
        migrations/
        seeds/
        tests/

      dictionary/
      latlon/
      otm_connector/
      reports/
      cutover/
      oracle_lab/

    shared/
      otm/
      excel/
      csv/
      xml/
      zip/
      hashing/
      security/
      file_system/
      errors/
      pagination/
      datetime/
```

---

## 9.3 Manifesto de módulo

Cada módulo deve ter um `manifest.yaml`.

Exemplo:

```yaml
id: master_data
name: Master Data
version: 0.1.0
description: Business load packs, intake, validation and OTM CSV export.

capabilities:
  - master_data.batch.create
  - master_data.batch.validate
  - master_data.batch.convert
  - master_data.package.export
  - master_data.evidence.view

menus:
  - id: master_data
    label: Dados Mestres
    route: /master-data
    required_capability: master_data.batch.create

depends_on:
  - platform.projects
  - platform.artifacts
  - platform.evidence
  - dictionary

events_published:
  - master_data.batch.created
  - master_data.batch.validated
  - master_data.load_package.generated
  - master_data.evidence.generated

events_consumed:
  - dictionary.version.changed

artifacts:
  - otm_csv_zip
  - manifest_json
  - correction_report

feature_flags:
  - master_data.enabled
  - master_data.latlon_quality.enabled
```

---

## 9.4 Interface de módulo

Exemplo conceitual em Python:

```python
from typing import Protocol
from fastapi import FastAPI

class WorkbenchModule(Protocol):
    module_id: str
    version: str

    def register_api(self, app: FastAPI) -> None:
        ...

    def get_capabilities(self) -> list[str]:
        ...

    def get_navigation(self, context) -> list[dict]:
        ...

    def get_health(self, context) -> dict:
        ...

    def get_event_handlers(self) -> dict:
        ...
```

Registry inicial explícito:

```python
REGISTERED_MODULES = [
    MasterDataModule(),
    RatesModule(),
    LoadPlanModule(),
    EvidenceModule(),
    DictionaryModule(),
]
```

Na primeira fase, o registry deve ser explícito. Descoberta automática de plugins pode vir depois.

---

## 10. Módulos funcionais da nova aplicação

## 10.1 Home / Project Cockpit

Responsabilidade:

- Mostrar projeto ativo.
- Mostrar status das jornadas.
- Mostrar próxima ação.
- Mostrar blockers.
- Direcionar o consultor para o próximo passo.

Fonte dos dados:

- Backend navigation contract.
- Project status.
- Module registry.
- Jobs.
- Evidence summary.
- Load plan readiness.

Não deve conter cards hardcoded.

---

## 10.2 Project Readiness

Responsabilidade:

- Validar pré-requisitos mínimos do projeto.
- Confirmar perfil ativo.
- Confirmar domínio.
- Confirmar ambiente.
- Confirmar conexão OTM quando aplicável.
- Confirmar módulos habilitados.
- Exibir bloqueios e próxima ação.

Não deve duplicar Admin Console.

---

## 10.3 Data Factory / Master Data

Responsabilidade:

- Template packs de negócio.
- Upload de templates preenchidos.
- Batch persistente.
- Validação estrutural.
- Validação de dependências.
- Conversão.
- ZIP OTM ordenado.
- `MANIFEST.json`.
- Correction report.
- Evidência.

Packs prioritários:

```text
Regions:
- REGION
- REGION_DETAIL

Items & Packaging:
- ITEM
- SHIP_UNIT_SPEC
- PACKAGED_ITEM
- TI_HI

Location:
- LOCATION
- Location-related references
- Lat/Lon quality
```

Subviews:

```text
Overview
Template Packs
Imported Batches
Validation
Conversion & OTM CSV
Coordinate Quality
Evidence
```

---

## 10.4 Template & Mapping Studio

Responsabilidade:

- Mostrar templates amigáveis ao cliente.
- Mostrar mapeamento para campos técnicos OTM.
- Validar regras, defaults e transformações.
- Exibir preview.
- Versionar mapeamentos.

Fase inicial:

```text
Read-only preview dentro de Data Factory.
```

Não deve virar editor livre antes de governança, versionamento e contratos.

---

## 10.5 Rates Studio

Responsabilidade:

- Download de template de tarifas.
- Upload de workbook.
- Normalização.
- Validação de offering, geo, lane, custos, condições e acessórios.
- Lista de batches.
- Issues.
- Aprovação.
- XML.
- CSV OTM quando aplicável.
- Correction report.
- CRP package.
- Evidence.

Regra importante:

```text
Não declarar sucesso real de sandbox OTM sem evidência real de execução.
```

---

## 10.6 Load Plan & CSVUTIL

Responsabilidade:

- Centro operacional de carga.
- Geração CSVUTIL.
- Análise de ZIP.
- Histórico de cargas.
- Review queue.
- Classificação de itens.
- Sequenciamento.
- Dependências.
- Handoff para cutover.
- Readiness.
- Evidence.

Subviews:

```text
Overview
Load Packages
CSVUTIL Builder
ZIP Analysis
Setup Review
Load Sequence
Cutover Readiness
Execution Evidence
```

---

## 10.7 Cutover Readiness

Cutover não deve ser módulo top-level separado na primeira versão.

Ele deve ser subfluxo de Load Plan.

Responsabilidade:

- Checklist.
- Blockers.
- Pacotes prontos.
- Evidências obrigatórias.
- Export de pacote/checklist.
- Registro de execução.

---

## 10.8 Reports & Evidence

Responsabilidade:

- Hub canônico de artefatos e evidências.
- Listar evidências por origem.
- Exibir detalhes seguros.
- Permitir download.
- Gerar archive package.
- Linkar evidência ao módulo fonte.

Não deve ler payload técnico sensível diretamente.

---

## 10.9 Admin Console

Responsabilidade:

- Usuários.
- Roles/capabilities.
- Perfis.
- Ambientes.
- Conexão OTM.
- Feature flags.
- Module enablement.
- Audit log.
- Configurações técnicas.

Apenas ADMIN/DBA/MASTER.

---

## 10.10 Dev Tools / DBA Tools

Dev tools devem ficar ocultas por padrão.

Possíveis capacidades:

- OTM Explorer.
- Environment Compare.
- Oracle Lab.
- Data Dictionary Explorer.
- FK Catalog Explorer.
- Technical object cache.

Dev tools devem depender de:

```text
role DBA/MASTER
+ capability específica
+ feature flag habilitada
```

---

## 11. Lifecycle canônico

## 11.1 Lifecycle de batch

Todo batch deve seguir um lifecycle padronizado.

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

Exemplo de status com próxima ação:

```json
{
  "batch_id": "bat_123",
  "status": "BLOCKED",
  "next_action": "Review validation issues",
  "blockers": [
    {
      "code": "MISSING_REGION_DETAIL",
      "message": "Region has no REGION_DETAIL rows."
    }
  ]
}
```

---

## 11.2 Lifecycle de job

```text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

---

## 11.3 Lifecycle de artifact

```text
CREATED
VALIDATED
PUBLISHED
DOWNLOADED
ARCHIVED
DELETED
```

---

## 11.4 Lifecycle de evidence

```text
GENERATED
AVAILABLE
DOWNLOADED
ARCHIVED
INVALIDATED
```

---

## 12. Modelo de dados conceitual

## 12.1 Tabelas de plataforma

```text
users
sessions
roles
capabilities
role_capabilities
workspaces
workspace_members
projects
profiles
environments
otm_connections
feature_flags
module_registry
module_capabilities
module_navigation
settings
audit_logs
```

---

## 12.2 Tabelas transversais

```text
domain_events
jobs
artifacts
artifact_manifests
evidence_records
sync_state
```

---

## 12.3 Tabelas de Master Data

```text
master_data_packs
master_data_pack_objects
master_data_batches
master_data_batch_files
master_data_validation_issues
master_data_conversions
master_data_load_packages
```

---

## 12.4 Tabelas de Rates

```text
rate_batches
rate_workbooks
rate_offerings
rate_geos
rate_lanes
rate_costs
rate_conditions
rate_validation_issues
rate_exports
```

---

## 12.5 Tabelas de Load Plan

```text
load_plans
load_plan_packages
load_plan_items
load_plan_dependencies
csvutil_jobs
csvutil_outputs
review_queue_items
review_decisions
cutover_readiness
cutover_blockers
```

---

## 12.6 Tabelas de Dictionary

```text
dictionary_versions
dictionary_objects
dictionary_fields
dictionary_relationships
fk_catalog
object_graphs
```

---

## 13. API design

## 13.1 Prefixos principais

```text
/api/v1/auth/*
/api/v1/platform/me
/api/v1/platform/workspaces
/api/v1/platform/projects
/api/v1/platform/profiles
/api/v1/platform/environments
/api/v1/platform/modules
/api/v1/platform/navigation
/api/v1/platform/jobs
/api/v1/platform/artifacts
/api/v1/platform/evidence
/api/v1/platform/audit

/api/v1/modules/master-data/*
/api/v1/modules/rates/*
/api/v1/modules/load-plan/*
/api/v1/modules/dictionary/*
/api/v1/modules/latlon/*
/api/v1/modules/otm/*
/api/v1/modules/reports/*
/api/v1/modules/oracle-lab/*
```

---

## 13.2 Padrão de erro

```json
{
  "error": {
    "code": "MASTER_DATA_VALIDATION_FAILED",
    "message": "Batch contains unresolved dependencies.",
    "details": {
      "batch_id": "bat_123",
      "issue_count": 14
    }
  }
}
```

---

## 13.3 Padrão de paginação

```json
{
  "items": [],
  "page": 1,
  "page_size": 50,
  "total": 0,
  "has_next": false
}
```

---

## 13.4 Padrão de status

```json
{
  "status": "ATTENTION",
  "next_action": "Validate imported batch",
  "blockers": [],
  "warnings": [],
  "updated_at": "2026-05-16T10:00:00Z"
}
```

---

## 14. Segurança

## 14.1 Regras de segurança

- Senhas nunca em texto puro.
- Credenciais OTM devem ser criptografadas.
- Evidence não deve conter payload técnico sensível cru.
- Downloads devem verificar permissão.
- Admin endpoints devem exigir capability específica.
- Dev tools devem exigir role e feature flag.
- Audit log deve mascarar dados sensíveis.
- Arquivos temporários devem ser limpos.
- Caminhos de arquivo devem ser normalizados para evitar path traversal.

---

## 14.2 Níveis de sensibilidade

```text
PUBLIC
INTERNAL
CLIENT_SAFE
SENSITIVE
SECRET
```

Artifacts e evidências devem ter `sensitivity_level`.

---

## 15. Sincronização cloud opcional

A cloud deve ser opcional no início.

## 15.1 O que sincronizar

Sincronizar:

- Workspace.
- Projeto.
- Usuários e permissões.
- Module enablement.
- Manifests.
- Evidence summaries.
- Artifact references.
- Status de jobs concluídos.
- Audit selecionado.

Não sincronizar por padrão:

- Payload sensível.
- Credenciais OTM.
- Arquivos temporários.
- Cache técnico.
- Dumps brutos.
- Dados locais não marcados como compartilháveis.

---

## 15.2 Estratégia de sync

Modelo recomendado:

```text
Local event log
→ sync queue
→ cloud API/Postgres
→ conflict policy
→ sync state
```

Tabela local:

```text
sync_state
- id
- entity_type
- entity_id
- local_version
- remote_version
- sync_status
- last_synced_at
- conflict_status
```

Status:

```text
LOCAL_ONLY
PENDING_UPLOAD
SYNCED
CONFLICT
REMOTE_UPDATED
FAILED
```

---

## 16. Serviços locais e Docker

## 16.1 Docker Compose opcional

Serviços opcionais:

```text
pelias
oracle-free
local-worker
redis opcional
postgres-dev opcional
```

Exemplo conceitual:

```yaml
services:
  pelias:
    image: pelias/local
    profiles: ["geocoding"]

  oracle-lab:
    image: container-registry.oracle.com/database/free:latest
    profiles: ["oracle-lab"]

  postgres-dev:
    image: postgres:16
    profiles: ["cloud-dev"]

  redis:
    image: redis:7
    profiles: ["queue"]
```

Os serviços pesados devem ser opt-in, não obrigatórios para abrir a aplicação.

---

## 17. Plano de implementação da fundação

## 17.1 Fase 0 — Baseline e congelamento

Objetivo: preservar versão atual e evitar perda de conhecimento.

Entregáveis:

```text
- branch legacy-current
- tag v0-legacy-baseline
- backup dos documentos funcionais/técnicos
- inventário de módulos atuais
- lista de capacidades a reaproveitar
- lista de telas/legados a não migrar como estão
```

---

## 17.2 Fase 1 — Platform Core

Entregáveis:

```text
- Estrutura FastAPI modular
- Config management
- SQLAlchemy
- Alembic
- SQLite
- Auth básico
- Session
- RBAC/capabilities
- Workspace/Project/Profile/Environment
- Module Registry
- Feature Flags
- Health Check
- Audit Log básico
```

Critérios de aceite:

```text
- Criar usuário inicial
- Fazer login/logout
- Criar workspace
- Criar projeto
- Criar profile
- Criar environment
- Listar módulos registrados
- Gerar navigation contract pelo backend
- Ver health da aplicação
- Rodar migrations
- Rodar testes
```

---

## 17.3 Fase 2 — Contracts Core

Entregáveis:

```text
- Padrão de erro
- Padrão de paginação
- Padrão de status
- Base de schemas Pydantic
- Base de APIs versionadas
- require_capability
- contract tests
```

---

## 17.4 Fase 3 — Jobs, Artifacts e Evidence

Entregáveis:

```text
- Job Engine
- Artifact Store
- Manifest Store
- Evidence Store
- Download seguro
- Hash SHA256
- Client-safe summaries
- Audit de geração/download
```

Critérios de aceite:

```text
- Criar job
- Executar job simples
- Registrar artifact metadata
- Gerar manifest
- Registrar evidence client-safe
- Baixar artifact autorizado
- Bloquear download sem permissão
```

---

## 17.5 Fase 4 — Data Dictionary Core

Entregáveis:

```text
- Import/cache de Data Dictionary
- Versão de dictionary
- Objetos
- Campos
- Relacionamentos
- FK catalog
- Object graph
- Dependency graph
```

---

## 17.6 Fase 5 — Primeiro módulo funcional: Master Data

Entregáveis:

```text
- master_data manifest
- APIs de pack
- APIs de batch
- Upload
- Validação estrutural
- Validation issues
- Conversão básica
- Load package
- MANIFEST.json
- Evidence
```

---

## 18. Critérios de aceite da fundação técnica

A fundação só deve ser considerada pronta quando:

```text
1. Consigo criar usuário.
2. Consigo autenticar.
3. Consigo criar projeto.
4. Consigo criar profile e environment.
5. Consigo registrar/listar módulos.
6. Consigo gerar navegação via backend.
7. Consigo habilitar/desabilitar módulo por feature flag.
8. Consigo validar permissões por capability.
9. Consigo registrar job.
10. Consigo registrar domain event.
11. Consigo registrar artifact metadata.
12. Consigo gerar manifest.
13. Consigo registrar evidence client-safe.
14. Consigo consultar audit log.
15. Consigo rodar migrations.
16. Consigo rodar testes de contrato.
17. Consigo adicionar um módulo demo sem alterar core indevidamente.
```

---

## 19. Regras para adicionar novo módulo

Para adicionar um novo módulo:

```text
1. Criar pasta app/modules/{module_id}
2. Criar manifest.yaml
3. Criar schemas.py
4. Criar models.py
5. Criar repository.py
6. Criar service.py
7. Criar api.py
8. Criar policies.py
9. Criar events.py
10. Criar artifacts.py se gerar arquivos
11. Criar evidence.py se gerar evidências
12. Criar migrations
13. Criar seeds se necessário
14. Registrar no Module Registry
15. Criar capabilities
16. Criar testes unitários
17. Criar testes de API
18. Criar testes de contrato
19. Validar health do módulo
```

O módulo não deve alterar Platform Core sem necessidade clara.

---

## 20. O que não fazer na reconstrução

Evitar:

- Começar pela UI.
- Criar telas sem contrato backend.
- Criar microserviços no início.
- Usar Oracle local como banco principal.
- Salvar ZIP/XML/CSV grande no banco.
- Misturar admin com fluxo de consultor.
- Expor payload sensível em evidências.
- Hardcodar menu no frontend.
- Criar módulo que chama outro módulo diretamente.
- Criar plugin dinâmico complexo antes de estabilizar registry simples.
- Migrar tela legada apenas porque existe.
- Declarar validação sandbox OTM sem evidência real.

---

## 21. Prompt recomendado para iniciar no Codex

```text
Você é um arquiteto de software sênior e deverá criar a fundação backend do OTM Project Workbench do zero.

Contexto:
O OTM Project Workbench será uma aplicação local-first para apoiar projetos Oracle Transportation Management, com foco em dados mestres, tarifas, plano de carga, CSVUTIL, cutover e evidências. Nesta primeira etapa, não implemente módulos funcionais completos. O objetivo é criar uma fundação técnica sólida, modular e escalável.

Arquitetura desejada:
- Modular monolith.
- Python 3.12+.
- FastAPI.
- Pydantic.
- SQLAlchemy 2.x.
- Alembic.
- SQLite local.
- Module Registry.
- RBAC/capabilities.
- Feature flags.
- Domain Events.
- Job Engine.
- Artifact Store.
- Evidence Store client-safe.
- Audit Log.
- Health Check.

Entregue:
1. Estrutura de pastas backend/app organizada em platform, modules e shared.
2. app/main.py com FastAPI e roteadores principais.
3. Config management.
4. Database session e migrations Alembic.
5. Auth básico com usuário inicial, login e logout.
6. RBAC com roles USER, ADMIN, DBA e MASTER.
7. Capabilities por módulo.
8. Workspace, Project, Profile e Environment.
9. Module Registry com manifest.yaml por módulo.
10. Feature Flags.
11. Domain Events persistidos.
12. Job Engine básico.
13. Artifact Store com metadata e hash.
14. Evidence Store client-safe.
15. Audit Log com mascaramento de dados sensíveis.
16. APIs versionadas em /api/v1.
17. Padrão de erro, paginação e status.
18. Um módulo demo chamado master_data, com manifest, router, schemas, health e capabilities, mas sem lógica funcional completa.
19. Testes unitários e testes de contrato.
20. README com instruções de instalação, execução e testes.

Critérios de aceite:
- Criar usuário inicial.
- Fazer login/logout.
- Criar workspace, projeto, profile e environment.
- Listar módulos registrados.
- Gerar navigation contract pelo backend.
- Habilitar/desabilitar módulo por feature flag.
- Validar capability por endpoint.
- Criar domain event.
- Criar job.
- Registrar artifact metadata.
- Registrar evidence client-safe.
- Consultar audit log.
- Rodar migrations.
- Rodar testes com pytest.
- O módulo demo master_data deve ser registrado sem acoplar indevidamente no core.

Restrições:
- Não criar frontend completo agora.
- Não usar Oracle como banco principal.
- Não implementar microserviços.
- Não salvar arquivos grandes no banco.
- Não hardcodar menu no frontend.
- Não expor payload sensível em evidence ou audit.
```

---

## 22. Decisão final

A nova fundação do OTM Project Workbench deve nascer como:

```text
Backend-first
Modular monolith
Local-first
SQLite-first
Cloud-optional
Evidence-safe
Event-driven internally
Module-registry based
Capability-driven
Artifact-aware
Job-oriented
```

Stack final recomendada:

```text
Backend:
- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- SQLite
- Pytest
- httpx
- cryptography
- openpyxl
- lxml ou ElementTree

Banco analítico opcional:
- DuckDB

Oracle opcional:
- Oracle Free via Docker apenas como Oracle Lab

Cloud opcional:
- PostgreSQL
- Supabase ou backend próprio

Frontend futuro:
- React
- TypeScript
- Vite

Desktop futuro:
- Tauri

Infra local opcional:
- Docker Compose
- Pelias
- Oracle Lab
- Workers
```

A primeira entrega não deve ser uma tela bonita. A primeira entrega deve ser uma fundação onde qualquer novo módulo possa ser adicionado com previsibilidade, controle, permissões, eventos, artifacts, evidências e testes.

