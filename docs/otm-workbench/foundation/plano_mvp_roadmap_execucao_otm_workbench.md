# Plano MVP e Roadmap de Execução — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Documento:** plano de execução para reconstrução do OTM Project Workbench do zero.  
**Objetivo:** transformar arquitetura, funcionalidade e UI/UX em uma sequência prática de entregas.

---

## 1. Estratégia geral

A reconstrução deve começar pela fundação, não pelas telas.

Ordem recomendada:

```text
MVP 0 — Fundação técnica
MVP 1 — Shell, projeto, perfil, navegação e RBAC
MVP 2 — Data Factory / Dados Mestres
MVP 3 — Evidence Hub
MVP 4 — Rates Studio
MVP 5 — Load Plan & Cutover
MVP 6 — Cloud Collaboration
MVP 7 — Dev/DBA Tools controlados
```

---

## 2. MVP 0 — Fundação técnica

### Objetivo

Criar o backend modular, banco local, contracts e mecanismos transversais.

### Escopo

```text
- FastAPI base.
- Config management.
- SQLAlchemy + Alembic.
- SQLite local.
- Estrutura modular.
- Module Registry.
- Capabilities/RBAC.
- Feature Flags.
- Domain Events.
- Job Engine.
- Artifact Store.
- Evidence Store.
- Audit Log.
- Health Check.
- Error model padrão.
- Testes mínimos.
```

### Fora do escopo

```text
- Data Factory completo.
- Rates completo.
- Load Plan completo.
- Cloud sync.
- UI final.
```

### Critérios de aceite

```text
[ ] App sobe localmente.
[ ] Banco inicializa com migrations.
[ ] Usuário bootstrap é criado.
[ ] Login funciona.
[ ] Projeto/perfil/ambiente podem ser criados.
[ ] Módulos registrados aparecem em /platform/modules.
[ ] Navegação vem do backend.
[ ] Capability bloqueia endpoint.
[ ] Job pode ser criado/consultado.
[ ] Artifact metadata pode ser registrado.
[ ] Evidence client-safe pode ser registrada.
[ ] Audit log registra ação crítica.
[ ] Testes passam.
```

---

## 3. MVP 1 — Application Shell e contexto operacional

### Objetivo

Criar a experiência mínima navegável, ainda sem módulos funcionais completos.

### Escopo

```text
- Login UI.
- Seleção/criação de projeto.
- Seleção/criação de perfil.
- Seleção de ambiente.
- Home / Project Cockpit.
- Navigation backend-owned.
- Admin Console básico.
- Feature flag visibility.
- User menu/sessão.
```

### Critérios de aceite

```text
[ ] USER vê apenas módulos públicos habilitados.
[ ] ADMIN vê Admin Console.
[ ] Dev-only não aparece sem flag/capability.
[ ] Home mostra projeto ativo e próximas ações.
[ ] Navigation contract controla menu.
[ ] Project Readiness mostra status básico.
```

---

## 4. MVP 2 — Data Factory / Dados Mestres

### Objetivo

Entregar primeiro módulo funcional real, com packs, batches, validação, conversão e exportação.

### Escopo

```text
- Template Packs.
- Regions pack.
- Items & Packaging pack.
- Location pack inicial, se viável.
- Upload de workbook/template.
- Batch persistente.
- Lifecycle do batch.
- Validação estrutural.
- Validação same-batch FK.
- Issues com suggested_fix.
- Conversão.
- ZIP OTM ordenado.
- MANIFEST.json.
- Correction report.
- Evidence básica.
```

### Critérios de aceite

```text
[ ] Usuário baixa template por pack.
[ ] Usuário cria batch por upload.
[ ] Batch aparece no histórico.
[ ] Batch bloqueado mostra motivo e correção.
[ ] Batch válido converte.
[ ] Export gera ZIP + MANIFEST.json.
[ ] Evidence é criada sem payload bruto.
[ ] Usuário consegue retornar ao batch.
```

---

## 5. MVP 3 — Evidence Hub

### Objetivo

Centralizar evidências e artifacts antes de escalar novos módulos.

### Escopo

```text
- Evidence dashboard.
- Lista de evidências por projeto.
- Filtro por módulo/status/tipo.
- Detalhe client-safe.
- Download seguro de artifacts.
- Archive package básico.
- Audit de download.
```

### Critérios de aceite

```text
[ ] Evidence lista origem, status e artifact relacionado.
[ ] Detalhe não expõe payload sensível.
[ ] Download respeita capability.
[ ] Archive package inclui apenas artifacts permitidos.
```

---

## 6. MVP 4 — Rates Studio

### Objetivo

Adicionar fluxo de tarifas com validação, aprovação e exportação.

### Escopo

```text
- Template de tarifas.
- Upload workbook.
- Normalização.
- Validação de offering/geo/lane/cost.
- Issues.
- Approval flow.
- XML export.
- CSV OTM export quando habilitado.
- Correction report.
- CRP package.
- Evidence.
```

### Critérios de aceite

```text
[ ] Batch de tarifa é criado.
[ ] Validação gera issues corretas.
[ ] Aprovação exige capability.
[ ] Export gera artifact + manifest.
[ ] Evidence é client-safe.
[ ] Não há promessa de sandbox real sem piloto.
```

---

## 7. MVP 5 — Load Plan & Cutover

### Objetivo

Consolidar CSVUTIL, setup review, load sequence e readiness de cutover.

### Escopo

```text
- Load Plan summary.
- Load Packages vindos de Data Factory/Rates.
- CSVUTIL Builder.
- ZIP Analysis.
- Setup Review Queue.
- Decisões de review.
- Load Sequence.
- Cutover Readiness.
- Blockers.
- Execution Evidence.
```

### Critérios de aceite

```text
[ ] Load Plan consome packages existentes.
[ ] CSVUTIL/CTL/CL são gerados.
[ ] ZIP Analysis registra histórico.
[ ] Item incerto não entra automaticamente em cutover.
[ ] Readiness mostra blockers/evidências exigidas.
[ ] Cutover é subfluxo de Load Plan, não módulo paralelo.
```

---

## 8. MVP 6 — Cloud Collaboration

### Objetivo

Permitir colaboração entre consultores sem mover processamento pesado para cloud.

### Escopo

```text
- Workspace cloud.
- Usuários compartilhados.
- Roles por projeto.
- Sync de project metadata.
- Sync de manifests.
- Sync de evidence client-safe.
- Artifact references.
- Sync status.
- Conflict handling básico.
```

### Critérios de aceite

```text
[ ] App funciona offline.
[ ] Sync envia evidence client-safe.
[ ] Artifact sensível não sobe automaticamente.
[ ] Conflito não apaga artifact/evidence.
[ ] Admin pode gerenciar usuários do workspace.
```

---

## 9. MVP 7 — Dev/DBA Tools controlados

### Objetivo

Reintroduzir ferramentas técnicas apenas com governança.

### Escopo

```text
- OTM Explorer dev-only.
- Environment readiness, se redesenhado.
- Oracle Lab opcional.
- Data Dictionary explorer.
- Diagnostics.
```

### Critérios de aceite

```text
[ ] USER não vê ferramentas técnicas.
[ ] DBA/MASTER vê apenas com feature flag.
[ ] Payload sensível é mascarado.
[ ] Acesso gera audit log.
```

---

## 10. Ordem de implementação recomendada

```text
1. Criar repositório limpo.
2. Criar branch/tag legacy-current para referência.
3. Criar backend foundation.
4. Criar contracts base.
5. Criar Module Registry.
6. Criar RBAC/capabilities.
7. Criar Artifact/Evidence/Job/Event core.
8. Criar shell mínimo.
9. Criar Data Factory MVP.
10. Criar Evidence Hub.
11. Criar Rates Studio.
12. Criar Load Plan & Cutover.
13. Criar Cloud Sync.
14. Reavaliar dev-only tools.
```

---

## 11. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Começar por tela | Alto | MVP 0 obrigatório antes dos módulos. |
| Módulo acoplar diretamente a outro | Alto | Usar eventos/registry. |
| Evidence expor payload | Alto | Testes client-safe obrigatórios. |
| Cloud sync virar complexo cedo | Médio/Alto | Cloud só no MVP 6. |
| Oracle local virar dependência | Médio | Oracle Lab opcional. |
| Cutover duplicar Load Plan | Alto | Cutover como subfluxo. |
| Dev-only aparecer para USER | Alto | Feature flag + capability + testes. |
| Sandbox OTM não comprovado | Médio/Alto | Não prometer piloto sem evidência real. |

---

## 12. Backlog inicial por frente

### Roadmap pos-Rates

```text
- ROADMAP-RATES-NEXT-01: manter Rates como ciclo ativo ate fechamento do fluxo operacional.
- ROADMAP-JOBS-01: Jobs / Processing Engine registrado como fundacao previa ao Catalog Core completo.
- ROADMAP-CATALOG-01: OTM Catalog Core registrado como proximo modulo estrutural depois de Jobs MVP0.
- ROADMAP-PROFILE-01: Project / Profile / Admin Foundation registrado para hardening depois do Catalog Core MVP0 e antes de Master Data/Cutover.
- ROADMAP-MD-01: Dados Mestres / Template Factory registrado para retomada depois do Catalog Core e do hardening Project/Profile/Admin.
- ROADMAP-CUTOVER-01: Cutover Checklist & CSVUTIL Builder registrado para retomada depois do Catalog Core e de Master Data.
```

Detalhe consolidado: [backlog_pos_rates.md](../roadmap/backlog_pos_rates.md)

### Platform

```text
- APP-BOOT-01: criar estrutura FastAPI.
- DB-CORE-01: SQLAlchemy + Alembic + SQLite.
- AUTH-01: bootstrap/login/session.
- RBAC-01: roles/capabilities.
- MOD-REG-01: module registry.
- NAV-01: navigation contract.
- FLAGS-01: feature flags.
- AUDIT-01: audit log.
```

### Operational Core

```text
- JOB-01: job engine.
- ART-01: artifact metadata + filesystem.
- MAN-01: manifest store.
- EVD-01: evidence store.
- EVT-01: domain events.
```

### First Functional Module

```text
- MD-01: master data module manifest.
- MD-02: template packs.
- MD-03: batch lifecycle.
- MD-04: validation issues.
- MD-05: conversion/export.
- MD-06: ZIP + MANIFEST.
- MD-07: correction report.
- MD-08: evidence producer.
```

---

## 13. Prompt base para iniciar o MVP 0 no Codex

```text
Crie a fundação backend da nova versão do OTM Project Workbench.

Objetivo:
Construir um modular monolith local-first em Python/FastAPI, sem implementar ainda módulos funcionais completos.

Stack:
- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- SQLite
- Pytest

Entregar:
1. Estrutura de pastas modular.
2. Config management.
3. Database session.
4. Alembic migrations.
5. Auth bootstrap/login/logout.
6. RBAC com roles e capabilities.
7. Workspace/Project/Profile/Environment.
8. Module Registry com manifest.yaml.
9. Feature Flags.
10. Domain Events.
11. Job Engine.
12. Artifact Store.
13. Manifest Store.
14. Evidence Store.
15. Audit Log.
16. Health checks.
17. Error model padrão.
18. Um módulo demo chamado master_data com manifesto, router, schemas e health.
19. Testes mínimos.

Regras:
- Não criar telas ainda.
- Não criar lógica hardcoded de menu no frontend.
- Não acoplar módulo a outro módulo.
- Toda rota sensível deve validar capability.
- Evidence deve ser client-safe.
- Artifact deve ter hash e sensitivity_level.

Critério de aceite:
- App sobe localmente.
- Migrations rodam.
- Usuário bootstrap é criado.
- Login funciona.
- Projeto/perfil/ambiente podem ser criados.
- /platform/modules lista módulos registrados.
- /platform/navigation retorna navegação por capability.
- Job/artifact/evidence/event/audit podem ser criados e consultados.
- Pytest passa.
```
