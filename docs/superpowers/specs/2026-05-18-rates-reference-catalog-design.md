# Rates Reference Catalog Design

## Status

Aprovado para planejamento de implementação.

## Contexto

Este documento define o desenho backend-first, DB-first e API-first do primeiro recorte do módulo de Tarifas do OTM Workbench. O foco é criar a fundação de catálogo de referências, políticas por campo e contratos técnicos para futuras validações/exportações de tarifas, sem implementar UI, sem integração real obrigatória com OTM e sem citar clientes reais.

Os domínios e exemplos usados neste desenho são sintéticos, como `PUBLIC`, `OTM1`, `OTM2`, `DEMO` e `SANDBOX`.

Fontes usadas:

- `C:\Users\Enzo Trabalho\Downloads\mvp0_tarifas_reference_catalog.md`
- `C:\Users\Enzo Trabalho\Downloads\Instruções Rates OTM.md`
- `OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict/*.json`

## Objetivo

Criar a fundação backend/DB do módulo de Tarifas para que o Workbench consiga conhecer, filtrar, sugerir e validar referências OTM relevantes para tarifas antes de existir qualquer tela final.

O catálogo local deve ser assistivo e validativo. Ele ajuda a preencher templates, validar GIDs, sugerir reuso, evitar duplicidades e preparar exportações futuras, mas não deve bloquear a criação de novos objetos quando a política funcional permitir.

## Não Objetivos

- Não criar UI.
- Não criar editor visual de tarifas.
- Não implementar template Excel completo.
- Não implementar validação completa de workbook de tarifas.
- Não implementar export XML/CSV final.
- Não implementar conexão OTM real obrigatória.
- Não implementar Load Plan, CSVUTIL final ou carga real.
- Não armazenar nomes, domínios ou identificadores de clientes reais.

## Princípios

Toda regra de negócio deve residir no backend. UI futura deve consumir contratos de options, policies, capabilities, actions, validation e export preview sem reimplementar decisão de domínio, role ou severidade.

Estados relevantes devem ser persistidos no banco local: tipos de referência, objetos, policies, batches de importação, metadados de Data Dictionary, ordem técnica de tabelas, eventos e auditoria.

O Data Dictionary OTM é fonte obrigatória para validar tabelas, colunas, chaves primárias, FKs, obrigatoriedade, constraints e dependências. Nenhuma tabela de tarifa deve entrar em um contrato de carga/export sem validação contra `OTM_RESOURCES/DATA_DICT26B`.

## Data Dictionary como Fonte Técnica

O módulo deve incluir uma camada de leitura/normalização do Data Dictionary local. Para cada tabela OTM relevante, o backend deve conseguir responder:

- tabela existe no Data Dictionary;
- schema e nome canônico;
- colunas disponíveis;
- colunas obrigatórias (`isNull=false`);
- PK;
- FKs e tabelas pai;
- constraints de valores;
- colunas de tipo `DATE`;
- child tables relevantes para impacto de carga.

O primeiro recorte deve validar ao menos estas tabelas:

```text
RATE_OFFERING
RATE_UNIT_BREAK_PROFILE
RATE_UNIT_BREAK
X_LANE
RATE_GEO
ACCESSORIAL_CODE
ACCESSORIAL_COST
ACCESSORIAL_COST_UNIT_BREAK
RATE_OFFERING_ACCESSORIAL
RATE_GEO_ACCESSORIAL
RATE_GEO_STOPS
RATE_GEO_COST_GROUP
RATE_GEO_COST
```

Validação inicial já observada no Data Dictionary:

| Tabela | PK | Dependências principais |
|---|---|---|
| `RATE_OFFERING` | `RATE_OFFERING_GID` | `RATE_OFFERING_TYPE`, `SERVPROV`, `CURRENCY`, `TRANSPORT_MODE`, `EQUIPMENT_GROUP_PROFILE`, `RATE_SERVICE`, `RATE_VERSION` |
| `RATE_UNIT_BREAK_PROFILE` | `RATE_UNIT_BREAK_PROFILE_GID` | sem FK principal no recorte inicial |
| `RATE_UNIT_BREAK` | `RATE_UNIT_BREAK_GID` | `RATE_UNIT_BREAK_PROFILE` |
| `X_LANE` | `X_LANE_GID` | `LOCATION`, `COUNTRY_CODE`, `REGION`, `GEO_HIERARCHY` |
| `RATE_GEO` | `RATE_GEO_GID` | `RATE_OFFERING`, `X_LANE`, `EQUIPMENT_GROUP_PROFILE`, `RATE_SERVICE`, `CURRENCY` |
| `ACCESSORIAL_CODE` | `ACCESSORIAL_CODE_GID` | sem FK principal no recorte inicial |
| `ACCESSORIAL_COST` | `ACCESSORIAL_COST_GID` | `RATE_GEO_COST_OPERAND`, `RATABLE_OPERATOR` |
| `ACCESSORIAL_COST_UNIT_BREAK` | `ACCESSORIAL_COST_GID`, `RATE_UNIT_BREAK_GID`, `RATE_UNIT_BREAK2_GID` | `ACCESSORIAL_COST`, `RATE_UNIT_BREAK`, `CURRENCY` |
| `RATE_OFFERING_ACCESSORIAL` | `ACCESSORIAL_COST_GID`, `RATE_OFFERING_GID`, `ACCESSORIAL_CODE_GID` | `ACCESSORIAL_COST`, `RATE_OFFERING`, `ACCESSORIAL_CODE` |
| `RATE_GEO_ACCESSORIAL` | `ACCESSORIAL_COST_GID`, `RATE_GEO_GID`, `ACCESSORIAL_CODE_GID` | `ACCESSORIAL_COST`, `RATE_GEO`, `ACCESSORIAL_CODE` |
| `RATE_GEO_STOPS` | `RATE_GEO_GID`, `LOW_STOP`, `HIGH_STOP` | `RATE_GEO`, `CURRENCY` |
| `RATE_GEO_COST_GROUP` | `RATE_GEO_COST_GROUP_GID` | `RATE_GEO` |
| `RATE_GEO_COST` | `RATE_GEO_COST_GROUP_GID`, `RATE_GEO_COST_SEQ` | `RATE_GEO_COST_GROUP`, `RATE_GEO_COST_OPERAND`, `RATABLE_OPERATOR`, `CURRENCY`, `ACCESSORIAL_CODE`, `RATE_UNIT_BREAK_PROFILE` |

Essa tabela acima é uma fotografia inicial do Data Dictionary e não substitui validação automatizada. A implementação deve ler os JSONs do Data Dictionary em runtime/teste para evitar contratos divergentes.

## Ordem Técnica de Carga

A sequência operacional inicial informada para tarifas é:

```text
RATE_OFFERING
RATE_UNIT_BREAK_PROFILE
RATE_UNIT_BREAK
X_LANE
RATE_GEO
ACCESSORIAL_CODE
ACCESSORIAL_COST
ACCESSORIAL_COST_UNIT_BREAK
RATE_OFFERING_ACCESSORIAL
RATE_GEO_ACCESSORIAL
RATE_GEO_STOPS
RATE_GEO_COST_GROUP
RATE_GEO_COST
```

O sistema deve tratar essa sequência como ordem funcional inicial, mas deve validá-la contra dependências do Data Dictionary. Quando a sequência funcional divergir de FKs técnicas, o backend deve produzir um relatório explícito com:

- tabela;
- dependência;
- severidade;
- recomendação;
- justificativa funcional para permitir ou bloquear.

Exemplo: `RATE_GEO` depende de `X_LANE` e `RATE_OFFERING`, então uma carga de `RATE_GEO` só é tecnicamente completa se as referências necessárias existirem no catálogo/import atual ou já existirem no ambiente alvo.

## Contrato de CSV OTM

O formato CSV OTM futuro deve seguir este contrato:

```text
Linha 1: nome da tabela OTM
Linha 2: nomes das colunas separados por virgula
Linhas seguintes: valores
```

Se qualquer coluna exportada da tabela tiver tipo `DATE` ou se houver valor de data no payload, o arquivo deve incluir antes das linhas de valores uma instrução `exec alter session` para declarar o formato de data.

Formato padrão inicial:

```text
exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'
```

O gerador deve preservar estes princípios:

- nomes de tabela e colunas em uppercase;
- colunas validadas contra Data Dictionary;
- campos removidos ou controlados por regra técnica não devem aparecer por acidente;
- datas formatadas de modo compatível com a linha `exec alter session`;
- valores vazios representados de forma consistente;
- cada tabela gerada separadamente para respeitar ordem de carga.

Regras especiais registradas para ciclos futuros:

- `RATE_OFFERING`: deixar campo sequencial interno em branco quando aplicável.
- `RATE_GEO`: remover `RATE_GEO_SEQ` do CSV e resetar conforme procedimento técnico posterior.
- `RATE_GEO_COST_GROUP`: usar `RATE_GEO_COST_GROUP_SEQ=1` quando a tabela/coluna estiver no recorte exportado.
- `RATE_GEO_COST`: `RATE_GEO_COST_SEQ` deve ser sequencial e depois resetado conforme procedimento técnico; `CHARGE_AMOUNT_BASE` deve ficar nulo quando a regra de carga exigir.
- `X_LANE`: deve ser transparente para o usuário e ter o mesmo identificador funcional da `RATE_GEO` no fluxo padrão de rate record.

## Escopo Funcional do Primeiro Recorte

O primeiro recorte implementável deve cobrir:

- Catálogo de tipos de referência.
- Catálogo de objetos de referência.
- Políticas de referência por campo.
- Importação manual controlada por CSV/JSON para alimentar catálogo.
- Filtro por projeto, ambiente, perfil e domínio.
- Regra de visibilidade `PUBLIC + domínio do perfil`.
- Exceção por capability para visualização multi-domínio por `DBA`/`MASTER`.
- Validação de referência por policy.
- Consulta de Rate Offerings existentes como presets/referências.
- Detecção de possível duplicidade de Rate Offering por combinação funcional.
- Leitura/validação do Data Dictionary para tabelas de tarifa.
- Registro de auditoria para import, alteração de policy e uso administrativo.

## Modelos de Dados Propostos

Adicionar modelos persistentes para catálogo:

```text
reference_object_types
reference_objects
reference_field_policies
reference_import_batches
reference_snapshots
reference_snapshot_items
```

Adicionar modelos técnicos para metadados OTM:

```text
otm_table_definitions
otm_table_columns
otm_table_foreign_keys
otm_load_sequences
otm_csv_contracts
```

Os modelos `otm_*` não devem duplicar o Data Dictionary inteiro. Eles devem cachear o subconjunto validado que o Workbench usa para decisões, testes e relatórios. A fonte canônica continua sendo o arquivo JSON do Data Dictionary versionado/local.

Campos mínimos de `reference_objects`:

```text
id
project_id
environment_id
object_type
gid
xid
domain_name
display_name
is_active
metadata_json
source
last_synced_at
sync_batch_id
created_at
updated_at
```

Campos mínimos para Rate Offering no metadata:

```text
rate_offering_gid
rate_offering_xid
domain_name
servprov_gid
transport_mode_gid
rate_service_gid
equipment_group_gid
equipment_group_profile_gid
currency_gid
is_active
effective_date
expiration_date
metadata_json
last_synced_at
```

## Policies

O módulo deve suportar:

```text
MUST_EXIST
SHOULD_EXIST_ALLOW_NEW
SUGGEST_ONLY
FREE_TEXT
```

Política inicial:

| Objeto/Campo | Policy | Ausente |
|---|---|---|
| `TRANSPORT_MODE` | `MUST_EXIST` | `ERROR` |
| `CURRENCY` | `MUST_EXIST` | `ERROR` |
| `ACCESSORIAL_CODE` | `MUST_EXIST` | `ERROR` |
| `RATE_SERVICE` | `SHOULD_EXIST_ALLOW_NEW` | `WARNING` |
| `RATE_DISTANCE` | `SHOULD_EXIST_ALLOW_NEW` | `WARNING` |
| `RATE_VERSION` | `SHOULD_EXIST_ALLOW_NEW` | `WARNING` |
| `EQUIPMENT_GROUP` | `SHOULD_EXIST_ALLOW_NEW` | `WARNING` |
| `EQUIPMENT_GROUP_PROFILE` | `SHOULD_EXIST_ALLOW_NEW` | `WARNING` |
| `RATE_OFFERING` | `SUGGEST_ONLY` | `WARNING` ou `INFO` |
| `RATE_GEO_GID` | `FREE_TEXT` | sem issue |
| `RATE_GEO_XID` | `FREE_TEXT` | sem issue |

## Capabilities

Capabilities iniciais:

```text
reference.options.view
reference.catalog.view
reference.catalog.import
reference.catalog.sync
reference.catalog.admin
reference.catalog.view_all_domains
rates.reference.view
rates.reference.validate
rates.rate_offering.suggest
rates.rate_offering.create_new_allowed
rates.dictionary.view
rates.dictionary.validate_sequence
rates.csv.preview
```

Visibilidade de dados e ações devem ser separadas. Um usuário pode enxergar referências do seu domínio sem poder importar catálogo, alterar policy ou validar sequência técnica.

## APIs Propostas

Endpoints de catálogo:

```http
GET /api/v1/reference/object-types
GET /api/v1/reference/options?object_type=RATE_SERVICE
POST /api/v1/reference/import-batches
GET /api/v1/reference/import-batches/{batch_id}
POST /api/v1/reference/validate
```

Endpoints técnicos de Tarifas:

```http
GET /api/v1/modules/rates/reference/rate-offerings
POST /api/v1/modules/rates/reference/rate-offerings/duplicate-check
GET /api/v1/modules/rates/dictionary/tables
GET /api/v1/modules/rates/dictionary/tables/{table_name}
POST /api/v1/modules/rates/dictionary/validate-load-sequence
POST /api/v1/modules/rates/csv/preview
```

O endpoint de preview CSV deve ser backend-only e não representa export final. Ele serve para validar contrato, colunas, datas e ordem técnica em testes.

## Fluxos de Teste Funcional

O desenho deve preparar estes cenários:

1. Tarifa completa:
   `RATE_OFFERING`, `RATE_OFFERING_ACCESSORIAL`, `X_LANE`, `RATE_GEO`, `ACCESSORIAL_CODE`, `ACCESSORIAL_COST`, `ACCESSORIAL_COST_UNIT_BREAK`, `RATE_GEO_COST_GROUP`, `RATE_GEO_COST`, `RATE_GEO_ACCESSORIAL`.

2. Somente rate geo:
   `X_LANE`, `RATE_GEO`, `ACCESSORIAL_COST`, `RATE_GEO_COST_GROUP`, `RATE_GEO_COST`, `RATE_GEO_ACCESSORIAL`.

3. Somente accessorial:
   `ACCESSORIAL_COST`, `RATE_OFFERING_ACCESSORIAL`, `RATE_GEO_ACCESSORIAL`.

Cada cenário deve declarar quais tabelas são obrigatórias, opcionais ou dependem de existência prévia no catálogo/ambiente alvo.

## Estratégia de Testes

Testes mínimos:

- usuário comum em `OTM1` vê `PUBLIC + OTM1`;
- usuário comum em `OTM1` não vê `OTM2`;
- `DBA`/`MASTER` com capability apropriada vê múltiplos domínios;
- import JSON/CSV cria batch, insere objetos e registra auditoria;
- `MUST_EXIST` ausente gera `ERROR`;
- `SHOULD_EXIST_ALLOW_NEW` ausente gera `WARNING`;
- `SUGGEST_ONLY` para Rate Offering não bloqueia criação nova;
- `FREE_TEXT` não exige catálogo;
- Data Dictionary reconhece as tabelas de tarifa do recorte;
- validação de sequência identifica dependências por FK;
- preview CSV põe tabela na primeira linha e colunas na segunda;
- preview CSV inclui `exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'` quando houver coluna/valor de data;
- preview CSV rejeita coluna inexistente no Data Dictionary.

## Decisões

- Criar branch separada `codex/rates-reference-catalog` a partir de `main`.
- Pausar o trabalho de `codex/mvp1-application-shell` enquanto o foco for backend/DB de Tarifas.
- Não implementar UI neste ciclo.
- Não citar clientes reais em docs, testes, fixtures, seeds ou exemplos.
- Usar Data Dictionary local como fonte técnica obrigatória.
- Começar com import manual CSV/JSON, sem depender de OTM real.
- Tratar Rate Offering existente como referência/preset assistivo, não como trava.
- Tratar duplicidade de Rate Offering como `WARNING`.

## Riscos

O catálogo pode virar uma réplica local grande demais do OTM. Mitigação: limitar o primeiro recorte aos objetos de tarifas e tabelas de carga listadas.

A sequência funcional pode divergir de FKs técnicas. Mitigação: criar validação explícita contra Data Dictionary e permitir exceções apenas com justificativa registrada.

CSV preview pode parecer export final. Mitigação: nomear como preview/contract e manter export completo fora do primeiro recorte.

Domínios reais podem vazar em fixtures. Mitigação: testes e docs usam apenas domínios sintéticos.

## Próximos Passos

1. Escrever plano de implementação TDD para o módulo `reference` e subárea `modules/rates`.
2. Implementar modelos e migração do catálogo.
3. Implementar leitor/normalizador do Data Dictionary para as tabelas de tarifa.
4. Implementar policies e validação de referência.
5. Implementar import controlado.
6. Implementar endpoints backend.
7. Implementar preview CSV técnico.
8. Rodar testes, lint e migrations.

## Última Atualização

2026-05-18
