# Guia de Desenvolvimento Modular — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Documento:** guia prático para criação de módulos, telas, rotas, eventos, artifacts e evidências na nova aplicação.  
**Objetivo:** garantir que qualquer nova funcionalidade seja adicionada de forma previsível, padronizada e sustentável.

---

## 1. Princípio central

A nova versão do OTM Project Workbench deve ser construída como uma plataforma modular, não como uma sequência de telas independentes.

Cada novo módulo deve entrar na aplicação como uma peça completa de produto, contendo:

```text
- Manifesto do módulo
- Rotas backend
- Schemas e contratos
- Serviços de domínio
- Repositórios
- Permissões/capabilities
- Eventos publicados/consumidos
- Jobs, quando necessário
- Artifacts gerados
- Evidências geradas
- Rotas/telas frontend
- Componentes reutilizáveis
- Testes mínimos
- Critérios de aceite
```

A regra principal é:

```text
Novo módulo não deve reinventar shell, autenticação, permissões, navegação, layout, jobs, artifacts, evidências ou auditoria.
```

---

## 2. O que é um módulo

Um módulo é uma unidade funcional com fronteira clara de negócio.

Exemplos:

```text
- master_data
- rates
- load_plan
- evidence
- dictionary
- latlon_quality
- otm_connector
- admin
```

Um módulo não é apenas uma tela. Ele pode ter várias telas, rotas, operações, eventos e artifacts.

### 2.1 Módulos públicos

São módulos usados pelo consultor no fluxo normal:

```text
- Home / Project Cockpit
- Project Readiness
- Data Factory / Dados Mestres
- Rates Studio
- Load Plan & Cutover
- Evidence Hub
```

### 2.2 Módulos administrativos

São módulos para gestão, configuração e governança:

```text
- Admin Console
- Users & Roles
- Project/Profile/Environment
- OTM Connections
- Feature Flags
- Audit Log
```

### 2.3 Módulos dev-only ou DBA-only

São capacidades técnicas que não devem aparecer na navegação principal:

```text
- OTM Explorer
- Environment Compare
- Oracle Lab
- Internal Diagnostics
- Raw Payload Viewer
```

Eles só podem aparecer quando houver capability e feature flag explícita.

---

## 3. Estrutura padrão de backend

Estrutura recomendada:

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
      projects/
      profiles/
      sync/

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
        jobs.py
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
        jobs.py
        artifacts.py
        evidence.py
        migrations/
        seeds/
        tests/

    shared/
      otm/
      excel/
      csv/
      xml/
      zip/
      hashing/
      security/
      file_system/
```

### 3.1 Responsabilidade dos arquivos

| Arquivo | Responsabilidade |
|---|---|
| `manifest.yaml` | Declara identidade, capabilities, menus, eventos e artifacts do módulo. |
| `api.py` | Define endpoints HTTP e validação de borda. Não deve conter regra pesada. |
| `schemas.py` | Define modelos Pydantic de request/response/evento. |
| `models.py` | Define modelos persistidos ou entidades de domínio. |
| `repository.py` | Acesso a banco, queries e persistência. |
| `service.py` | Casos de uso e orquestração funcional. |
| `policies.py` | Regras de autorização, elegibilidade e validação de decisão. |
| `events.py` | Tipos de eventos publicados e handlers consumidos. |
| `jobs.py` | Funções pesadas ou assíncronas. |
| `artifacts.py` | Geração e registro de arquivos. |
| `evidence.py` | Geração de evidência client-safe. |
| `migrations/` | Alterações de schema do módulo. |
| `seeds/` | Dados iniciais do módulo. |
| `tests/` | Testes unitários, contrato e regressão. |

---

## 4. Manifesto do módulo

Todo módulo deve ter um manifesto.

Exemplo:

```yaml
id: master_data
name: Data Factory
version: 0.1.0
description: Business load packs, intake, validation and OTM CSV export.

visibility:
  public: true
  admin_only: false
  dev_only: false

capabilities:
  - master_data.batch.create
  - master_data.batch.read
  - master_data.batch.validate
  - master_data.batch.convert
  - master_data.package.export
  - master_data.evidence.view

menus:
  - id: master_data
    label: Data Factory
    route: /data-factory
    icon: database
    order: 30
    required_capability: master_data.batch.read

routes:
  backend_prefix: /api/v1/modules/master-data
  frontend_base: /data-factory

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

evidence:
  - master_data_batch_summary
  - master_data_load_package
  - master_data_correction_report

feature_flags:
  - master_data.enabled
  - master_data.latlon_quality.enabled
```

### 4.1 Regras do manifesto

```text
1. O manifesto deve ser a primeira fonte de descoberta do módulo.
2. Menus devem nascer do manifesto + capabilities + feature flags.
3. Capabilities devem ser explícitas e granulares.
4. Eventos publicados e consumidos devem ser declarados.
5. Artifacts e evidências gerados pelo módulo devem ser declarados.
6. Dependências devem ser poucas e voltadas à plataforma, não a outro módulo específico.
```

---

## 5. Regras de acoplamento

### 5.1 Regra principal

```text
Módulo não importa outro módulo diretamente.
```

Errado:

```python
from app.modules.load_plan.service import create_handoff
```

Correto:

```python
publish_event('master_data.load_package.generated', payload)
```

Depois:

```python
# Load Plan consome o evento
handle_master_data_load_package_generated(event)
```

### 5.2 Como módulos conversam

Módulos podem se integrar por:

```text
- Domain events
- Contratos de API
- Registry de capabilities
- Portas/interfaces compartilhadas
- Artifact/evidence references
```

### 5.3 O que evitar

```text
- Import circular entre módulos
- Query direta na tabela de outro módulo
- Chamada direta para service de outro módulo
- Reuso de model interno de outro módulo
- Salvar payload bruto de outro módulo em evidence
- Frontend chamar endpoint de outro módulo para simular estado do módulo atual sem contrato
```

---

## 6. Padrão de capabilities

Formato:

```text
{module}.{resource}.{action}
```

Exemplos:

```text
master_data.batch.create
master_data.batch.validate
master_data.package.export
rates.batch.approve
load_plan.csvutil.generate
load_plan.cutover.readiness.export
evidence.artifact.download
admin.user.manage
otm.connection.configure
dev.otm_explorer.access
```

### 6.1 Ações recomendadas

```text
read
create
update
delete
validate
approve
reject
convert
export
download
configure
execute
view_sensitive
```

### 6.2 Regras

```text
1. A UI nunca deve inferir permissão sozinha.
2. O backend deve retornar capabilities efetivas do usuário.
3. O backend deve validar capability em todo endpoint sensível.
4. O menu deve ser filtrado por capability.
5. Botões e ações devem ser filtrados por capability e estado do objeto.
```

---

## 7. Padrão de eventos

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
rates.export.generated
load_plan.readiness.generated
evidence.artifact.created
admin.change_request.approved
```

### 7.1 Payload mínimo de evento

```json
{
  "event_id": "evt_01HX...",
  "event_type": "master_data.load_package.generated",
  "source_module": "master_data",
  "workspace_id": "wrk_001",
  "project_id": "prj_001",
  "profile_id": "pfl_001",
  "aggregate_type": "load_package",
  "aggregate_id": "lpkg_001",
  "occurred_at": "2026-05-16T12:00:00Z",
  "payload": {
    "package_id": "lpkg_001",
    "artifact_id": "art_001",
    "manifest_id": "man_001"
  }
}
```

### 7.2 Regras de evento

```text
1. Evento deve descrever algo que já aconteceu.
2. Evento não deve conter payload sensível bruto.
3. Evento deve conter referência para artifact/manifest/evidence quando aplicável.
4. Evento deve ser persistido antes de ser processado por handlers críticos.
5. Handler deve ser idempotente.
```

---

## 8. Padrão de rotas backend

Formato base:

```text
/api/v1/modules/{module-id}/...
```

Exemplo para Dados Mestres:

```text
GET    /api/v1/modules/master-data/packs
POST   /api/v1/modules/master-data/batches
GET    /api/v1/modules/master-data/batches/{batch_id}
POST   /api/v1/modules/master-data/batches/{batch_id}/validate
POST   /api/v1/modules/master-data/batches/{batch_id}/convert
POST   /api/v1/modules/master-data/batches/{batch_id}/export
GET    /api/v1/modules/master-data/batches/{batch_id}/issues
GET    /api/v1/modules/master-data/batches/{batch_id}/evidence
```

### 8.1 Endpoints de plataforma

```text
/api/v1/platform/me
/api/v1/platform/workspaces
/api/v1/platform/projects
/api/v1/platform/profiles
/api/v1/platform/environments
/api/v1/platform/modules
/api/v1/platform/navigation
/api/v1/platform/capabilities
/api/v1/platform/jobs
/api/v1/platform/artifacts
/api/v1/platform/evidence
/api/v1/platform/audit
```

---

## 9. Padrão de rotas frontend

Formato base:

```text
/{module-route}/{subview?}
```

Exemplo:

```text
/data-factory
/data-factory/packs
/data-factory/batches
/data-factory/batches/:batchId
/data-factory/validation
/data-factory/conversion
/data-factory/evidence
```

### 9.1 Tela nova deve usar templates existentes

Uma nova tela deve partir de um destes templates:

```text
- DashboardPage
- ListPage
- DetailPage
- WizardPage
- UploadValidationPage
- EvidencePage
- AdminSettingsPage
- ReviewQueuePage
```

Não deve começar com layout livre.

---

## 10. Checklist para criar novo módulo

```text
[ ] Definir objetivo funcional do módulo.
[ ] Definir se é público, admin-only ou dev-only.
[ ] Criar manifest.yaml.
[ ] Definir capabilities.
[ ] Definir entidades principais.
[ ] Definir lifecycle dos objetos.
[ ] Criar schemas Pydantic.
[ ] Criar migrations.
[ ] Criar repositories.
[ ] Criar services/use cases.
[ ] Criar policies de autorização e elegibilidade.
[ ] Criar API router.
[ ] Registrar módulo no Module Registry.
[ ] Registrar menus/rotas.
[ ] Registrar eventos publicados/consumidos.
[ ] Registrar artifacts gerados.
[ ] Registrar evidências geradas.
[ ] Criar tela usando template padrão.
[ ] Criar testes unitários.
[ ] Criar testes de API.
[ ] Criar testes de permissão.
[ ] Criar testes de evidence/artifact se aplicável.
[ ] Atualizar documentação.
```

---

## 11. Checklist para criar nova tela

```text
[ ] Tela pertence a um módulo existente?
[ ] Rota está declarada no manifesto?
[ ] Capability requerida está definida?
[ ] Backend retorna o estado necessário?
[ ] Tela usa template padrão?
[ ] Tela usa componentes do Workbench UI Kit?
[ ] Não há CSS local desnecessário?
[ ] Não há endpoint hardcoded fora do API client?
[ ] Não há lógica de permissão no frontend sem respaldo do backend?
[ ] Empty state está definido?
[ ] Loading state está definido?
[ ] Error state está definido?
[ ] Ação primária por estado está clara?
[ ] A tela tem teste de renderização/smoke?
```

---

## 12. O que é proibido

```text
- Criar botão administrativo visível para USER.
- Criar menu direto no frontend sem contrato backend-owned.
- Criar tela com CSS totalmente novo sem passar por Design System.
- Criar endpoint que retorna payload sensível sem mascaramento.
- Salvar arquivo grande no banco.
- Salvar senha/token OTM em texto claro.
- Criar módulo que importa service de outro módulo.
- Criar batch sem lifecycle.
- Criar export sem manifest.
- Criar evidence com payload técnico bruto.
- Criar feature dev-only sem feature flag.
- Criar módulo sem testes mínimos.
```

---

## 13. Definition of Done de módulo

Um módulo só é considerado pronto quando:

```text
[ ] Possui manifesto válido.
[ ] Possui capabilities registradas.
[ ] Possui rotas backend versionadas.
[ ] Possui schemas request/response.
[ ] Possui testes de contrato.
[ ] Possui tratamento de erro padrão.
[ ] Possui autorização no backend.
[ ] Possui tela usando UI Kit.
[ ] Possui estado de loading/error/empty.
[ ] Possui audit quando altera estado crítico.
[ ] Gera artifacts/evidence de forma padronizada, se aplicável.
[ ] Não expõe dados sensíveis.
[ ] Está documentado.
```

---

## 14. Prompt base para Codex

```text
Você está trabalhando na nova versão do OTM Project Workbench.

Antes de implementar qualquer funcionalidade, leia:
- arquitetura_tecnica_otm_workbench.md
- arquitetura_funcional_otm_workbench.md
- arquitetura_uiux_frontend_otm_workbench.md
- guia_desenvolvimento_modular_otm_workbench.md
- modelo_dados_contratos_api_otm_workbench.md
- seguranca_permissoes_governanca_otm_workbench.md

Tarefa:
Criar ou alterar um módulo seguindo estritamente o padrão modular.

Regras obrigatórias:
1. Não criar menus hardcoded no frontend.
2. Não criar permissões somente no frontend.
3. Não acoplar módulo diretamente a outro módulo.
4. Usar manifest.yaml para declarar capability, menu, eventos e artifacts.
5. Usar schemas Pydantic para contratos.
6. Usar service/repository/policies separados.
7. Registrar artifacts/evidence quando houver exportação ou resultado auditável.
8. Criar testes mínimos.
9. Não expor payload sensível.
10. Atualizar documentação se alterar contrato público.

Entregue:
- Arquivos alterados.
- Resumo das decisões.
- Testes executados.
- Riscos pendentes.
```
