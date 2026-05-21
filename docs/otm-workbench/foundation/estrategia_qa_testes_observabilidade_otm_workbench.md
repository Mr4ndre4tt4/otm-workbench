# Estratégia de QA, Testes e Observabilidade — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Documento:** estratégia de qualidade para backend, frontend, módulos, contratos, evidências, segurança e releases.  
**Objetivo:** garantir que a reconstrução do zero seja sustentável, testável e confiável desde a fundação.

---

## 1. Princípios

```text
1. Contrato testado vale mais que tela bonita.
2. Todo módulo novo precisa de teste mínimo.
3. Todo endpoint sensível precisa de teste de permissão.
4. Todo artifact precisa de teste de metadata/hash.
5. Toda evidence precisa de teste client-safe.
6. Todo batch precisa de teste de lifecycle.
7. Todo fluxo crítico precisa de smoke/E2E.
8. Todo erro padrão precisa ser validado.
9. Toda release precisa de checklist.
10. Observabilidade deve existir desde o início, mesmo simples.
```

---

## 2. Pirâmide de testes

```text
             E2E / Browser
          Contract / API Tests
       Integration / Module Tests
    Unit Tests / Services / Policies
Static checks / Type checks / Lint
```

A maior parte da cobertura deve estar em unidade, serviços, policies e contratos. E2E deve cobrir jornadas críticas, não todas as variações.

---

## 3. Testes obrigatórios por camada

### 3.1 Backend unitário

Cobrir:

```text
- Services
- Validators
- Policies
- Repositories críticos
- Event handlers
- Artifact builders
- Evidence builders
- Manifest builders
```

### 3.2 Backend API/contrato

Cobrir:

```text
- Status code
- Response schema
- Error schema
- Autorização
- Paginação
- Lifecycle transition
- Artifact/evidence reference
```

### 3.3 Frontend unitário/componente

Cobrir:

```text
- Renderização de templates de página
- Componentes do UI Kit
- Loading state
- Error state
- Empty state
- Permission-based visibility
- Primary action by status
```

### 3.4 E2E

Cobrir jornadas principais:

```text
- Login e seleção de projeto.
- Home renderizada por navigation contract.
- Upload/validação/conversão/export em Data Factory.
- Upload/validação/aprovação/export em Rates.
- Load Plan readiness com blocker.
- Evidence Hub com download seguro.
- Admin não visível para USER.
```

---

## 4. Testes por módulo

### 4.1 Data Factory

```text
[ ] Lista packs habilitados.
[ ] Cria batch.
[ ] Valida estrutura.
[ ] Valida dependências same-batch.
[ ] Gera issues com suggested_fix.
[ ] Bloqueia conversão com ERROR aberto.
[ ] Converte batch válido.
[ ] Gera ZIP ordenado.
[ ] Gera MANIFEST.json.
[ ] Gera evidence client-safe.
```

### 4.2 Rates Studio

```text
[ ] Baixa template.
[ ] Recebe workbook.
[ ] Normaliza offering/geo/lane/cost.
[ ] Gera issues.
[ ] Bloqueia aprovação com erro crítico.
[ ] Aprova batch com capability.
[ ] Gera XML.
[ ] Gera CSV OTM, se habilitado.
[ ] Gera correction report.
[ ] Gera evidence client-safe.
```

### 4.3 Load Plan & Cutover

```text
[ ] Gera CSVUTIL/CTL/CL.
[ ] Analisa ZIP.
[ ] Registra histórico/lifecycle.
[ ] Importa review queue.
[ ] Bloqueia item incerto em cutover automático.
[ ] Gera readiness manifest.
[ ] Exibe blockers.
[ ] Exporta execution evidence.
```

### 4.4 Evidence Hub

```text
[ ] Lista evidências por projeto.
[ ] Filtra por módulo/origem/status.
[ ] Não expõe payload bruto sensível.
[ ] Linka artifact/manifest.
[ ] Baixa artifact somente com capability.
[ ] Gera archive package.
```

### 4.5 Admin/Security

```text
[ ] USER não vê Admin Console.
[ ] USER não acessa endpoint admin.
[ ] ADMIN acessa usuários/configuração.
[ ] DBA acessa dev-only quando flag habilitada.
[ ] Feature flag desabilitada remove menu.
[ ] Alteração de role gera audit.
```

---

## 5. Testes de permissão

Para cada endpoint sensível, testar:

```text
- Sem autenticação: 401.
- Autenticado sem capability: 403.
- Autenticado com capability: sucesso.
- Feature flag off: 404 ou 403 conforme regra.
- Role incorreta: 403.
```

Exemplo:

```text
POST /api/v1/modules/rates/batches/{id}/approve
- USER sem rates.batch.approve -> 403
- ADMIN com rates.batch.approve -> 200
```

---

## 6. Testes de dados sensíveis

Testar que respostas não contêm:

```text
- password
- token
- api_key
- Authorization
- raw_payload
- secret
- connection_string
```

Testar que evidências não contêm:

```text
- planilha inteira
- XML completo sensível
- CSV completo sensível
- senha/token
- headers de autenticação
```

---

## 7. Testes de artifacts e manifestos

Todo export deve validar:

```text
[ ] Artifact existe no filesystem.
[ ] Artifact metadata existe no banco.
[ ] SHA256 confere.
[ ] size_bytes confere.
[ ] sensitivity_level foi definido.
[ ] manifest_id está vinculado.
[ ] source_module está correto.
[ ] source_entity_id está correto.
```

Todo manifest deve validar:

```text
[ ] Tem schema_version.
[ ] Tem project/profile/environment.
[ ] Tem source_module.
[ ] Tem generated_at/by.
[ ] Tem status.
[ ] Tem files.
[ ] Tem checksums.
[ ] Tem validation_summary.
```

---

## 8. Comandos mínimos locais

Backend:

```bash
pytest -q
python -m compileall -q app
```

### 8.1 Backend runtime e isolamento de banco

O backend usa SQLite local em testes. Para evitar colisao entre execucoes e
preparar paralelizacao futura, `tests/conftest.py` deve configurar
`OTM_DATABASE_URL` antes de importar o app/database, apontando para um arquivo
temporario por processo/worker pytest.

Regra atual:

```text
- Execucao serial e suportada.
- Execucao paralela so deve ser habilitada quando cada worker usar banco
  isolado e nenhum teste depender de estado global compartilhado.
- Se CI nao puder paralelizar com seguranca, segmentar a suite por grupos de
  modulo com budget proprio.
```

Matriz backend recomendada para CI enquanto a suite completa for pesada:

```bash
python -m pytest tests/test_operational_context.py tests/test_project_cockpit_summary.py -q
python -m pytest tests/test_rates_summary.py tests/test_rates_batch_approval.py tests/test_rates_csv_export_artifacts.py -q
python -m pytest tests/test_rates_batches.py tests/test_rates_batch_csv_preview.py tests/test_rates_batch_scenarios.py tests/test_rates_batch_validation.py tests/test_rates_csv_preview.py tests/test_rates_dictionary.py tests/test_reference_catalog.py -q
python -m pytest tests/test_integration_mapping_foundation.py tests/test_integration_mapping_definitions.py tests/test_integration_mapping_systems.py tests/test_integration_mapping_schema_tree.py tests/test_integration_mapping_schema_persistence.py tests/test_integration_mapping_payload_artifacts.py tests/test_integration_mapping_mappings.py tests/test_integration_mapping_validation.py tests/test_integration_mapping_preview.py tests/test_integration_mapping_joins.py tests/test_integration_mapping_lookups.py tests/test_integration_mapping_loops.py tests/test_integration_mapping_audit_events.py tests/test_integration_mapping_synthetic_e2e.py tests/test_integration_mapping_spec_generator.py -q
python -m pytest tests/test_load_plan_cutover_go_no_go.py tests/test_load_plan_cutover_checklist.py tests/test_load_plan_csvutil_builder.py tests/test_load_plan_cutover_package_export.py tests/test_load_plan_cutover_handoff.py tests/test_load_plan_cutover_readiness.py tests/test_load_plan_zip_analysis.py tests/test_load_plan_sequence_blockers.py tests/test_load_plan_readiness_export.py tests/test_load_plan_review_decisions.py tests/test_load_plan_review_queue.py tests/test_load_plan_package_intake.py -q
python -m pytest tests/test_order_release_generator_xml_artifact.py tests/test_order_release_generator_submit_guard.py tests/test_order_release_generator_jobs.py tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py tests/test_order_release_generator_xml_preview.py -q
python -m pytest tests/test_assets_library_foundation.py tests/test_assets_library_assets.py tests/test_assets_library_links.py tests/test_assets_library_permissions.py tests/test_assets_library_versions.py tests/test_master_data_templates.py tests/test_catalog_core.py tests/test_coordinate_quality_engine.py tests/test_coordinate_quality_api.py tests/test_health.py tests/test_evidence_hub_index.py tests/test_error_contracts.py tests/test_database.py tests/test_modules_navigation.py tests/test_operational_metadata.py tests/test_auth_permissions.py -q
python -m pytest tests/test_cli.py -q
```

Evidencia de 2026-05-21 no PR #181: os grupos pesados passaram serialmente,
mas a soma ultrapassa 10 minutos. Timeout da suite completa nesse budget deve
ser tratado como limite de runtime, nao automaticamente como travamento.

Frontend:

```bash
npm run typecheck
npm run test
npm run lint
npm run build
```

E2E:

```bash
npm run test:e2e
```

Observação: os comandos finais dependem da stack escolhida. O importante é ter comandos simples e repetíveis.

---

## 9. Dados de teste

Criar fixtures padronizadas:

```text
fixtures/
  projects/
    basic_project.json
  users/
    user_admin_dba_master.json
  master_data/
    regions_valid.xlsx
    regions_missing_detail.xlsx
    items_packaging_valid.xlsx
  rates/
    rates_valid.xlsx
    rates_invalid_lane.xlsx
  load_plan/
    csvutil_valid.zip
    csvutil_with_uncertain_items.zip
  evidence/
    evidence_safe.json
    evidence_sensitive_payload_blocked.json
```

---

## 10. Observabilidade

### 10.1 Logs estruturados

Formato mínimo:

```json
{
  "timestamp": "2026-05-16T12:00:00Z",
  "level": "INFO",
  "request_id": "req_001",
  "user_id": "usr_001",
  "project_id": "prj_001",
  "module": "master_data",
  "action": "batch.validate",
  "message": "Batch validation completed",
  "metadata": {
    "batch_id": "bat_001",
    "issue_count": 3
  }
}
```

### 10.2 Request ID

Todo request deve receber `request_id` para rastrear:

```text
- API request
- Job
- Artifact generation
- Evidence generation
- Audit log
```

### 10.3 Health checks

```text
GET /api/v1/platform/health
GET /api/v1/platform/health/database
GET /api/v1/platform/health/artifacts
GET /api/v1/platform/health/modules
GET /api/v1/platform/health/services/pelias
GET /api/v1/platform/health/cloud-sync
```

### 10.4 Métricas simples

```text
- jobs_total
- jobs_failed_total
- batches_created_total
- artifacts_generated_total
- evidence_generated_total
- api_request_duration_ms
- validation_issue_count
- sync_failures_total
```

---

## 11. Release checklist

```text
[ ] Migrations rodam do zero.
[ ] Migrations rodam em banco existente.
[ ] Testes unitários passam.
[ ] Testes de API passam.
[ ] Testes de permissão passam.
[ ] Testes de evidence client-safe passam.
[ ] Build frontend passa.
[ ] E2E mínimo passa.
[ ] Health check verde.
[ ] Nenhum segredo em logs.
[ ] Nenhum payload sensível em evidence.
[ ] Artifacts gerados têm hash.
[ ] Documentação atualizada.
```

---

## 12. Definition of Done por entrega

Uma entrega só deve ser aceita quando:

```text
- Implementa o escopo funcional combinado.
- Não quebra contratos existentes.
- Inclui testes mínimos.
- Respeita RBAC/capabilities.
- Gera audit/evidence/artifact quando aplicável.
- Usa erro padrão.
- Atualiza documentação de contrato, se necessário.
- Passa no checklist local.
```

---

## 13. Anti-patterns de QA

```text
- Testar apenas caminho feliz.
- Criar tela sem teste de permissão.
- Criar export sem testar hash/manifest.
- Criar evidence sem testar payload sensível.
- Depender de sandbox OTM real para teste unitário.
- Não versionar fixture.
- Não testar user comum contra endpoint admin.
- Aceitar módulo público com placeholder.
```
