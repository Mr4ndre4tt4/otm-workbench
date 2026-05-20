# OTM Workbench Documentation

Este diretório contém a documentação base do `otm-workbench`.

## Estrutura

- `foundation/`: documentos de arquitetura, contratos, governança, QA, segurança, roadmap e convenções recebidos como fundação do projeto.
- `../superpowers/specs/`: specs consolidadas para execução assistida por Codex.

## Ordem Recomendada

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

Para frontend e experiência do usuário:

1. [Arquitetura UI/UX e frontend](foundation/arquitetura_uiux_frontend_otm_workbench.md)
2. [Guia de desenvolvimento modular](foundation/guia_desenvolvimento_modular_otm_workbench.md)
3. [Modelo de dados e contratos de API](foundation/modelo_dados_contratos_api_otm_workbench.md)
4. [Glossário e convenções](foundation/glossario_convencoes_otm_workbench.md)
5. [GUI MVP1 Plan](gui/GUI_MVP1_PLAN.md)
6. [GUI API Contract Patterns](gui/GUI_API_CONTRACT_PATTERNS.md)

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

## Próximo Passo

A spec consolidada do **MVP 0 - Fundação técnica** está em:

- [OTM Workbench MVP 0 Foundation Design](../superpowers/specs/2026-05-16-otm-workbench-mvp0-foundation-design.md)

O próximo passo é revisar essa spec e, após aprovação, gerar o plano de implementação em tarefas pequenas.
