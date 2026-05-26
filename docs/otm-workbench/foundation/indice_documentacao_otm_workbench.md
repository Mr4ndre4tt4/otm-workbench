# Índice da Documentação de Fundação — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Objetivo:** organizar os documentos necessários para reconstruir o OTM Project Workbench do zero com fundação técnica, funcional, frontend, modularidade, segurança, dados, sync e roadmap.

---

## 1. Leitura recomendada

### Ordem para arquitetura e decisão

```text
1. arquitetura_funcional_otm_workbench.md
2. arquitetura_tecnica_otm_workbench.md
3. arquitetura_uiux_frontend_otm_workbench.md
4. guia_desenvolvimento_modular_otm_workbench.md
5. modelo_dados_contratos_api_otm_workbench.md
```

### Ordem para iniciar desenvolvimento

```text
1. arquitetura_tecnica_otm_workbench.md
2. modelo_dados_contratos_api_otm_workbench.md
3. seguranca_permissoes_governanca_otm_workbench.md
4. guia_desenvolvimento_modular_otm_workbench.md
5. plano_mvp_roadmap_execucao_otm_workbench.md
```

### Ordem para frontend/UI

```text
1. arquitetura_uiux_frontend_otm_workbench.md
2. guia_desenvolvimento_modular_otm_workbench.md
3. modelo_dados_contratos_api_otm_workbench.md
4. glossario_convencoes_otm_workbench.md
```

---

## 2. Documentos principais

| Documento | Objetivo |
|---|---|
| `arquitetura_funcional_otm_workbench.md` | Define jornadas, módulos, papéis, fluxos e critérios funcionais. |
| `arquitetura_tecnica_otm_workbench.md` | Define stack, backend, modular monolith, banco, eventos, jobs e arquitetura. |
| `arquitetura_uiux_frontend_otm_workbench.md` | Define UI/UX, frontend, design system, shell, componentes e padrão de telas. |
| `guia_desenvolvimento_modular_otm_workbench.md` | Define como criar novos módulos/telas sem quebrar a arquitetura. |
| `modelo_dados_contratos_api_otm_workbench.md` | Define entidades, lifecycles, contratos de API e modelos canônicos. |
| `seguranca_permissoes_governanca_otm_workbench.md` | Define roles, capabilities, dados sensíveis, audit, feature flags e change requests. |
| `estrategia_local_first_cloud_sync_otm_workbench.md` | Define o que roda local, o que vai para cloud, sync e colaboração. |
| `modelo_artifacts_evidencias_manifestos_otm_workbench.md` | Define artifact, evidence, manifest, ZIP, correction report e archive package. |
| `estrategia_qa_testes_observabilidade_otm_workbench.md` | Define testes, QA, logs, health checks, métricas e release checklist. |
| `plano_mvp_roadmap_execucao_otm_workbench.md` | Define sequência de MVPs, critérios de aceite, riscos e prompt para Codex. |
| `glossario_convencoes_otm_workbench.md` | Define nomes, status, rotas, capabilities, eventos e termos padronizados. |
| `../engineering/HARNESS_ENGINEERING_PLAN.md` | Define como agentes, docs, Linear, GitHub, testes, browser QA e evidências devem operar como um harness único. |
| `../modules/rates_estado_atual_mvp0.md` | Consolida o estado backend/API/DB-first atual do modulo Rates MVP0, seus contratos, integracoes e pendencias. |

---

## 3. Mapa de decisões

| Tema | Decisão |
|---|---|
| Arquitetura | Modular Monolith local-first. |
| Backend | Python + FastAPI + Pydantic. |
| Banco local | SQLite como principal. |
| Banco analítico | DuckDB opcional. |
| Oracle local | Apenas Oracle Lab opcional, não banco principal. |
| Cloud | Colaboração e sync opcional. |
| Frontend | React + TypeScript + Vite no projeto novo. |
| UI | Design System próprio com templates e componentes padronizados. |
| Permissão | RBAC + capabilities. |
| Navegação | Backend-owned navigation contract. |
| Integração entre módulos | Domain events, registry e contratos. |
| Artifacts | Arquivo no filesystem/storage; metadata no banco. |
| Evidence | Client-safe, baseada em manifestos/referências. |
| Cutover | Subfluxo de Load Plan, não módulo paralelo. |
| Dev-only | Feature flag + capability. |

---

## 4. Mapa de MVPs

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

## 5. Regra de ouro do projeto

```text
Toda nova funcionalidade deve entrar como módulo governado por contrato,
não como tela solta.
```

Isso significa:

```text
- manifesto
- capability
- API contract
- UI template
- lifecycle
- artifact/evidence, se aplicável
- audit, se alterar estado crítico
- testes
```

---

## 6. Próximo passo recomendado

O próximo passo prático é iniciar o **MVP 0 — Fundação técnica** usando o prompt do documento:

```text
plano_mvp_roadmap_execucao_otm_workbench.md
```

Antes de iniciar, validar:

```text
[ ] Repositório novo criado.
[ ] Versão antiga congelada/tagueada.
[ ] Stack definida.
[ ] Documentos de arquitetura adicionados em /docs.
[ ] MVP 0 dividido em tarefas pequenas.
[ ] Critérios de aceite definidos.
```
