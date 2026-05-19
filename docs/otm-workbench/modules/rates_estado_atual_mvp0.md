# Rates MVP0 - Estado atual

**Data de referencia:** 2026-05-19
**Escopo:** backend/API/DB-first do modulo de tarifas.
**Regra de dados:** usar somente exemplos sinteticos; nao registrar nomes, dominios ou identificadores de clientes reais.

---

## 1. Objetivo operacional

O modulo Rates MVP0 cria a fundacao para preparar, validar, aprovar e exportar pacotes tecnicos de tarifas OTM sem UI final, sem upload real para OTM e sem execucao de CSVUTIL.

O foco atual e tratar Rate Record como macro-objeto governado pelo Catalog Core:

```text
catalog_macro_object_code = RATE_RECORD
catalog_load_plan_path = /api/v1/catalog/macro-objects/RATE_RECORD/load-plan
```

Esse contexto deve acompanhar os contratos de Rates, Load Plan, Evidence Hub e cutover sempre que o artefato ou evento nascer de um batch de tarifas.

---

## 2. Fontes tecnicas usadas

O Data Dictionary local continua sendo a fonte tecnica para validar tabelas, colunas, datas, PKs, FKs e dependencias.

Fonte local esperada:

```text
OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict/*.json
```

Quando houver duvida tecnica ou funcional de OTM, a regra do projeto e consultar a documentacao oficial Oracle ou perguntar antes de assumir comportamento.

Referencias oficiais Oracle usadas para validar o contrato CSV inicial:

```text
- Oracle Transportation Management Data Management Guide - CSV:
  https://docs.oracle.com/en/cloud/saas/transportation/26b/otmdm/csv.html
```

---

## 3. Contrato CSV OTM

Os CSVs OTM devem seguir o contrato:

```text
Linha 1: nome da tabela OTM
Linha 2: nomes das colunas separados por virgula
Linhas seguintes: valores
```

Se houver coluna/valor de data, incluir antes das linhas de valores:

```text
exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'
```

Validacao Oracle registrada:

```text
- a primeira linha do arquivo CSV identifica a tabela;
- a segunda linha lista os nomes das colunas;
- linhas seguintes carregam os valores;
- comandos SQL prefixados por EXEC SQL podem aparecer apos a linha de colunas e antes dos dados;
- a documentacao Oracle mostra o uso de ALTER SESSION para definir NLS_DATE_FORMAT antes dos dados.
```

Regras ja registradas no backend para o recorte de Rates:

```text
- nomes de tabela e coluna em uppercase;
- colunas validadas contra o Data Dictionary;
- RATE_GEO_SEQ removido do CSV de RATE_GEO;
- RATE_GEO_COST_GROUP_SEQ defaultado para 1 quando aplicavel;
- RATE_GEO_COST_SEQ sequencial;
- CHARGE_AMOUNT_BASE em branco quando a regra tecnica exigir;
- arquivos/manifestos client-safe, sem paths internos em resposta publica.
```

Pontos ainda tratados como regra funcional/procedural do projeto, e nao como afirmacao Oracle ja fechada:

```text
- quando remover RATE_GEO_SEQ do CSV gerado;
- quando resetar RATE_GEO_SEQ/RATE_GEO_COST_SEQ fora do arquivo;
- quando manter CHARGE_AMOUNT_BASE em branco;
- quando forcar RATE_GEO_COST_GROUP_SEQ=1.
```

Esses pontos devem ser validados com documentacao Oracle especifica, ambiente lab ou decisao funcional antes de virar regra final de carga.

---

## 4. Cenarios sinteticos

Os templates/cenarios de Rates sao expostos por API e todos pertencem ao macro-objeto `RATE_RECORD`.

Exemplos sinteticos usados nos testes/contratos:

```text
COMPLETE_TARIFF
RATE_GEO_ONLY
ACCESSORIAL_ONLY
```

O backend usa esses cenarios para derivar:

```text
- tabelas esperadas;
- ordem funcional de carga;
- contexto de Catalog;
- caminho do load plan do macro-objeto.
```

---

## 5. APIs de Rates ja cobertas

Base:

```text
/api/v1/modules/rates
```

Contratos principais ja implementados:

```text
GET  /templates
POST /batches
GET  /batches
GET  /batches/{batch_id}
POST /batches/{batch_id}/tables
POST /batches/{batch_id}/validate
GET  /batches/{batch_id}/issues
POST /batches/{batch_id}/csv-preview
POST /batches/{batch_id}/export-csv
GET  /batches/{batch_id}/readiness
POST /batches/{batch_id}/approve
GET  /batches/{batch_id}/artifacts
GET  /batches/{batch_id}/evidence
GET  /batches/{batch_id}/exports/latest
GET  /batches/{batch_id}/artifacts/{artifact_id}/download
GET  /dictionary/tables
GET  /dictionary/tables/{table_name}
POST /dictionary/validate-load-sequence
GET  /reference/options
GET  /reference/rate-offerings
POST /reference/rate-offerings/duplicate-check
POST /csv/preview
```

APIs que aceitam ou propagam `catalog_macro_object_code` devem restringir o fluxo de Rates a `RATE_RECORD` quando a operacao for especifica de tarifas. Quando outro macro-objeto for informado, o contrato deve responder de forma explicita e client-safe.

---

## 6. Fluxo backend atual

Fluxo suportado hoje:

```text
1. Consultar templates de Rates.
2. Criar batch sintetico de tarifa.
3. Adicionar tabelas/linhas OTM ao batch.
4. Validar tabelas, colunas e ordem contra Data Dictionary.
5. Listar issues do batch.
6. Gerar preview CSV tecnico.
7. Exportar ZIP interno com CSVs e manifest.
8. Consultar readiness.
9. Aprovar batch quando os gates permitirem.
10. Listar artefatos/evidencias.
11. Consultar ultimo export.
12. Baixar artefato autenticado/auditado.
13. Registrar o export aprovado em Load Plan.
14. Seguir para CSVUTIL build, ZIP analysis, review queue, readiness, readiness export, Evidence Hub archive e cutover handoff.
```

O fluxo ainda nao executa carga real no OTM, nao conecta em OTM, nao executa CSVUTIL real e nao substitui revisao funcional.

---

## 7. Integracao com Catalog Core

Rates ja carrega contexto de Catalog em:

```text
- templates;
- batches;
- dictionary tables;
- reference options;
- rate offerings;
- duplicate check;
- load sequence validation;
- standalone CSV preview;
- batch validation;
- batch CSV preview;
- issue list;
- artifacts/evidence list;
- latest export;
- direct export response;
- readiness;
- approval;
- nested approval readiness;
- artifact download audit metadata;
- table ingestion.
```

Esse contexto tambem ja foi propagado para os fluxos derivados de Load Plan, Evidence Hub e cutover quando o pacote nasce de Rates.

Endpoints de Rates que recebem `catalog_macro_object_code` fora de `RATE_RECORD` usam o contrato padronizado:

```text
code = UNSUPPORTED_RATES_CATALOG_MACRO_OBJECT
message = Catalog macro-object is outside the Rates module sequence.
details.catalog_macro_object_code = <macro-objeto recebido>
```

---

## 8. Evidence Hub neste contexto

No ciclo de Rates, o Evidence Hub funciona como indice client-safe de evidencias e artefatos produzidos pelo backend.

Objetivo pratico:

```text
- permitir rastreabilidade do que foi gerado;
- separar metadata segura de paths internos;
- vincular manifestos, ZIPs e decisoes ao batch/pacote;
- auditar downloads;
- preparar archive packages para handoff sem expor dados sensiveis.
```

Ele nao e uma tela de arquivos soltos. E uma camada governada de evidencias para sustentar aprovacao, readiness e cutover.

---

## 9. Hardening recente

Itens fechados apos a consolidacao inicial deste documento:

```text
1. Audit metadata do download direto de artifact de Rates carrega catalog_macro_object_code e catalog_load_plan_path.
2. Resposta nested de readiness dentro de approval repete o contexto de Catalog.
3. Contrato de macro-objeto nao suportado foi padronizado para endpoints de Rates que recebem catalog_macro_object_code.
4. GET /api/v1/modules/rates/dictionary/tables propaga catalog_macro_object_code e catalog_load_plan_path quando filtrado por RATE_RECORD.
5. POST /api/v1/modules/rates/dictionary/validate-load-sequence propaga catalog_load_plan_path quando validado no contexto RATE_RECORD.
6. GET /api/v1/modules/rates/dictionary/tables/{table_name} aceita catalog_macro_object_code, propaga contexto RATE_RECORD e rejeita macro-objeto fora de Rates.
7. POST /api/v1/modules/rates/csv/preview propaga catalog_load_plan_path quando executado no contexto RATE_RECORD.
8. GET /api/v1/modules/rates/reference/options propaga catalog_load_plan_path quando filtrado por RATE_RECORD.
9. GET /api/v1/modules/rates/reference/rate-offerings propaga catalog_load_plan_path quando filtrado por RATE_RECORD.
10. POST /api/v1/modules/rates/reference/rate-offerings/duplicate-check propaga catalog_load_plan_path quando executado no contexto RATE_RECORD.
11. GET /api/v1/modules/rates/templates retorna contrato padronizado para catalog_macro_object_code fora de RATE_RECORD.
```

---

## 10. Pendencias abertas recomendadas

Antes de considerar Rates MVP0 fechado:

```text
1. Revisar fixtures/exemplos sinteticos contra exemplos reais anonimizados sem copiar dados de cliente.
2. Validar regras especiais de sequencias/campos de CSV que ainda nao foram confirmadas por fonte Oracle direta ou ambiente lab.
```

Depois desses hardenings, a recomendacao e:

```text
1. Endurecer Jobs / Processing Engine MVP0.
2. Finalizar OTM Catalog Core minimo.
3. Migrar dependencias restantes de Rates para Catalog Core.
4. Iniciar Master Data Template Factory usando Catalog Core desde o inicio.
5. Iniciar Cutover Checklist/CSVUTIL com Catalog Core e Jobs como base.
```

---

## 11. Testes de referencia

Suites diretamente relacionadas:

```text
tests/test_reference_catalog.py
tests/test_rates_dictionary.py
tests/test_rates_csv_preview.py
tests/test_rates_batches.py
tests/test_rates_batch_scenarios.py
tests/test_rates_batch_validation.py
tests/test_rates_batch_csv_preview.py
tests/test_rates_csv_export_artifacts.py
tests/test_rates_batch_approval.py
```

Suites derivadas que validam propagacao para Load Plan/Evidence/Cutover:

```text
tests/test_load_plan_package_intake.py
tests/test_load_plan_csvutil_builder.py
tests/test_load_plan_zip_analysis.py
tests/test_load_plan_review_queue.py
tests/test_load_plan_review_decisions.py
tests/test_load_plan_sequence_blockers.py
tests/test_load_plan_cutover_readiness.py
tests/test_load_plan_readiness_export.py
tests/test_evidence_hub_index.py
tests/test_load_plan_cutover_handoff.py
```
