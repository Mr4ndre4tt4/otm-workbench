# OTM Workbench Documentation

Este diretório contém a documentação base do `otm-workbench`.

## Estrutura

- `../agent/`: camada curta de governanca operacional para agentes e humanos:
  norte do projeto, escopo atual, roadmap, pipeline, inventario, recovery plan,
  decisoes, riscos e handoff.

- `foundation/`: documentos de arquitetura, contratos, governança, QA, segurança, roadmap e convenções recebidos como fundação do projeto.
- `governance/`: regras leves de visibilidade, GitHub Issues/PRs/Actions e cadência de acompanhamento.
- `engineering/`: regras operacionais para agentes, harness engineering, entrega, QA e integração GitHub.
- `../superpowers/specs/`: specs consolidadas para execução assistida por Codex.

## Ordem Recomendada

Para entender o estado atual de governanca e reorganizacao:

1. [Project Brief](../agent/PROJECT_BRIEF.md)
2. [Project North Star](../agent/PROJECT_NORTH_STAR.md)
3. [Current Scope](../agent/CURRENT_SCOPE.md)
4. [Reorganization Roadmap](../agent/ROADMAP.md)
5. [Delivery Pipeline](../agent/DELIVERY_PIPELINE.md)
6. [Module Scope Ledger](../agent/MODULE_SCOPE_LEDGER.md)
7. [Module Documentation Index](../agent/MODULE_DOCUMENTATION_INDEX.md)
8. [Repository Recovery Plan](../agent/RECOVERY_PLAN.md)
9. [To-Be Solution Alignment Plan](../agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md)
10. [Test Scenario And Fixture Strategy](../agent/TEST_SCENARIO_FIXTURE_STRATEGY.md)

Para entender a arquitetura e as decisões do produto:

1. [Arquitetura funcional](foundation/arquitetura_funcional_otm_workbench.md)
2. [Arquitetura técnica](foundation/arquitetura_tecnica_otm_workbench.md)
3. [Arquitetura UI/UX e frontend](foundation/arquitetura_uiux_frontend_otm_workbench.md)
4. [Guia de desenvolvimento modular](foundation/guia_desenvolvimento_modular_otm_workbench.md)
5. [Modelo de dados e contratos de API](foundation/modelo_dados_contratos_api_otm_workbench.md)

Para iniciar o desenvolvimento:

1. [Arquitetura técnica](foundation/arquitetura_tecnica_otm_workbench.md)
2. [Modelo de dados e contratos de API](foundation/modelo_dados_contratos_api_otm_workbench.md)
3. [Segurança, permissões e governança](foundation/seguranca_permissoes_governanca_otm_workbench.md)
4. [Guia de desenvolvimento modular](foundation/guia_desenvolvimento_modular_otm_workbench.md)
5. [Plano MVP e roadmap de execução](foundation/plano_mvp_roadmap_execucao_otm_workbench.md)
6. [GitHub delivery governance](governance/GITHUB_DELIVERY_GOVERNANCE.md)
7. [Artifact trust boundary review](governance/ARTIFACT_TRUST_BOUNDARY_REVIEW_OTM98.md)
8. [Harness Engineering Plan](engineering/HARNESS_ENGINEERING_PLAN.md)

Para frontend e experiência do usuário:

1. [Arquitetura UI/UX e frontend](foundation/arquitetura_uiux_frontend_otm_workbench.md)
2. [Guia de desenvolvimento modular](foundation/guia_desenvolvimento_modular_otm_workbench.md)
3. [Modelo de dados e contratos de API](foundation/modelo_dados_contratos_api_otm_workbench.md)
4. [Glossário e convenções](foundation/glossario_convencoes_otm_workbench.md)
5. [GUI MVP1 Plan](gui/GUI_MVP1_PLAN.md)
6. [GUI Functional QA Journeys](gui/GUI_FUNCTIONAL_QA_JOURNEYS.md)
7. [GUI Module Completion Acceptance Contract](gui/GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md)
8. [Harness Engineering Plan](engineering/HARNESS_ENGINEERING_PLAN.md)

## Decisões Base

- Arquitetura: modular monolith local-first.
- Backend: Python, FastAPI e Pydantic.
- Banco local principal: SQLite.
- Frontend: React, TypeScript e Vite.
- Navegação: contrato backend-owned.
- Permissões: RBAC com capabilities.
- Artifacts: arquivos no filesystem/storage com metadata no banco.
- Evidence: client-safe, baseada em manifestos e referências.
- Cloud: colaboração e sincronização opcionais.

## Proximo Passo

O proximo passo ativo e adaptar a solucao atual para o To-Be validado no
Complete Solution Mockup:

1. usar como To-Be ativo:
   [OTM Workbench - Complete Solution Mockup](https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup);
2. consultar o relatorio:
   [Complete Solution Deep-Flow Report](../agent/figma-wireframes/OTM_WORKBENCH_COMPLETE_SOLUTION_DEEP_FLOW_REPORT.md);
3. classificar rotas, componentes e testes do frontend como manter, esconder,
   absorver, alterar, arquivar, remover ou criar;
4. limpar a exposicao do frontend para retirar modulos que nao serao atacados
   agora, preservando dependencias internas;
5. planejar e aplicar segregacao por client/domain, environment e
   visibility/access policy;
6. finalizar Settings;
7. finalizar Cockpit;
8. seguir com Rates, Assets, Master Data, Integration e Order Release;
9. em cada modulo, revalidar resultado desejado, fixtures, Data Dictionary,
   documentacao oficial Oracle, testes, QA, evidencias e GitHub.

A spec historica do MVP 0 continua disponivel como referencia:

- [OTM Workbench MVP 0 Foundation Design](../superpowers/specs/2026-05-16-otm-workbench-mvp0-foundation-design.md)
