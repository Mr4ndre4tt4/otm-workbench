# Backlog pos-Rates

**Data de referencia:** 2026-05-18  
**Objetivo:** registrar frentes futuras sem interromper o ciclo atual de Rates, Load Plan e Evidence Hub.  
**Regra de foco:** enquanto Rates nao estiver fechado, estes itens ficam apenas como roadmap/backlog.

---

## 1. Foco atual

O ciclo ativo continua sendo Rates e seu fluxo operacional imediato:

```text
Rates Reference Catalog
Rates Batch Contract
Rates CSV Export Artifacts
Rates Approval Readiness
Rates Export Download/Summary
Load Plan intake/sequence/readiness
Evidence Hub
Cutover handoff
```

O trabalho de OTM Catalog Core, Master Data e Cutover Checklist deve ser retomado depois que o ciclo de Rates estiver estabilizado.

---

## 2. Fundacao previa: Jobs / Processing Engine

**Fonte:** `C:/Users/Enzo Trabalho/Downloads/mvp0_jobs_processing_engine_backendfirst.md`

### Decisao

Jobs / Processing Engine faz sentido e deve ser tratado como infraestrutura transversal de plataforma, nao como modulo funcional.

Ele deve entrar **antes do Catalog Core completo** ou como primeira fatia imediatamente anterior, porque o Catalog Core precisara executar processos rastreaveis como:

```text
- importar Data Dictionary;
- importar referencias reutilizaveis;
- reconstruir dependency graph;
- gerar snapshot de catalogo;
- validar macro-objetos;
- registrar artifacts/evidencias de import.
```

### Estado atual no backend

Jobs / Processing Engine ja saiu da fundacao minima e agora possui um MVP0 operacional backend-first:

```text
- modelo Job;
- POST /api/v1/platform/jobs;
- GET /api/v1/platform/jobs com filtros por source_module, job_type, status, project_id, profile_id, environment_id e domain_name;
- GET /api/v1/platform/jobs/{job_id};
- POST /api/v1/platform/jobs/{job_id}/run para executar jobs PENDING;
- POST /api/v1/platform/jobs/{job_id}/cancel para cancelamento logico de jobs PENDING;
- GET /api/v1/platform/jobs/{job_id}/events com filtros por event_type e status_after;
- lifecycle PENDING/RUNNING/SUCCEEDED/FAILED/CANCELLED;
- eventos de job persistidos;
- handler registry simples;
- handler demo local DEMO_ECHO;
- erro padronizado para handler inexistente;
- audit logs client-safe para criacao, sucesso, falha e cancelamento;
- audit/event payloads carregam contexto project_id/profile_id/environment_id/domain_name.
```

Ainda faltam pecas importantes antes de usar isso como motor operacional amplo:

```text
- vinculo explicito com artifact/evidence.
- politicas para jobs reais de Catalog Core;
- convencao de outputs de job para imports/snapshots;
- limites MVP0 de payload/result para evitar armazenar dados sensiveis.
```

### Primeiro recorte MVP0 entregue

```text
1. Modelo/API de Job endurecido sem Celery/Redis.
2. List/detail/cancel/run criados.
3. Service de lifecycle com transicoes validas para run/cancel.
4. Handler registry simples criado.
5. Handler demo local criado.
6. Eventos de job persistidos e filtraveis.
7. Audit log client-safe registrado com contexto operacional.
8. Testes de contrato criados.
```

### Fora do primeiro recorte

```text
- worker distribuido;
- retry automatico;
- fila com Redis/Rabbit/Kafka;
- execucao remota/cloud;
- scheduling recorrente;
- jobs reais de Rates/Master Data/Cutover;
- UI de monitoramento.
```

### Ordem em relacao ao Catalog Core

Recomendacao:

```text
1. Fechar hardenings finais de Rates.
2. Endurecer Jobs / Processing Engine MVP0.
3. Implementar OTM Catalog Core MVP0 minimo.
4. Usar Jobs para imports/snapshots do Catalog Core.
```

---

## 3. Proximo modulo estrutural: OTM Catalog Core

**Fonte:** `C:/Users/Enzo Trabalho/Downloads/otm_catalog_core_backendfirst.md`

### Decisao

O OTM Catalog Core faz sentido e deve ser tratado como modulo transversal/fundacao, nao como tela e nao como produto funcional isolado.

Ele deve centralizar:

```text
- Data Dictionary Cache
- OTM Table & Field Catalog
- OTM Macro-Object Catalog
- Reference Data Catalog
- Domain Access Policy
- Dependency/FK Graph
- Validation Services
```

### Por que ele entra antes de Master Data e Cutover

Rates, Load Plan e Evidence Hub ja criaram necessidades que apontam para o mesmo nucleo:

```text
- validacao de tabela e coluna OTM;
- leitura de Data Dictionary;
- reference objects e policies;
- filtro por dominio/perfil;
- dependencia entre tabelas;
- classificacao setup/master/reference/configuration/transacional;
- bloqueio de tabelas transacionais;
- enriquecimento client-safe de manifests/evidencias.
```

Se Master Data e Cutover forem implementados antes desse core, ha alto risco de duplicar regras em cada modulo.

### Momento recomendado

```text
1. Fechar mais 1 ou 2 hardenings pequenos de Rates.
2. Endurecer Jobs / Processing Engine MVP0.
3. Criar OTM Catalog Core MVP0 minimo.
4. Migrar Rates aos poucos para consumir Catalog Core.
5. Iniciar Master Data Template Factory usando Catalog Core desde o inicio.
6. Iniciar Cutover Checklist/CSVUTIL usando Catalog Core desde o inicio.
```

### Primeiro recorte MVP0 recomendado

```text
1. Estrutura backend do modulo catalog.
2. GET /api/v1/catalog/health.
3. APIs de tabelas e colunas apoiadas no Data Dictionary local.
4. Reference options reaproveitando o catalogo de referencias existente.
5. Validation services para:
   - table exists;
   - column exists;
   - reference exists;
   - domain scope;
   - cutover/csvutil eligibility simples.
6. Bloqueio padrao de tabelas transacionais/UNKNOWN.
7. Testes de contrato.
```

### Primeiro recorte MVP0 entregue

```text
1. OTM Catalog Core registrado no module registry como modulo ACTIVE.
2. GET /api/v1/catalog/health disponivel.
3. APIs de tabelas/colunas apoiadas no Data Dictionary local disponiveis.
4. Reference options e validacoes de referencia expostas pelo Catalog Core.
5. Macro-objects, tables, dependencies e load-plan minimo expostos.
6. Testes de contrato cobrindo registry, health, data dictionary, references e macro-objects.
```

### Fora do primeiro recorte

```text
- UI;
- sync automatico com OTM;
- OTM Explorer publico;
- import completo de todo o OTM;
- execucao real de CSVUTIL;
- conexao direta com banco OTM;
- dependency graph perfeito;
- validacao SQL profunda de whereClause.
```

### Sinergia com Rates

Rates deve consumir Catalog Core para:

```text
- RATE_SERVICE, RATE_VERSION, RATE_DISTANCE e ACCESSORIAL_CODE options;
- Rate Offering duplicate/suggestion;
- field policies MUST_EXIST, SHOULD_EXIST_ALLOW_NEW, SUGGEST_ONLY, FREE_TEXT;
- domain scope;
- Data Dictionary table/column validation;
- manifest/evidence enrichment.
```

### Guardrails

```text
- Backend-first, API-first, DB-first e UI-agnostic.
- Nao replicar o OTM inteiro.
- Allowlist antes de blacklist.
- Dados transacionais bloqueados por padrao.
- Overrides exigem capability, justificativa e audit log.
- Consultar Data Dictionary local para tabelas/dependencias.
- Em duvida tecnica/funcional OTM, consultar documentacao oficial Oracle ou perguntar.
- Nao usar nomes de clientes reais.
```

---

## 4. Fundacao Project / Profile / Admin

**Fonte:** `C:/Users/Enzo Trabalho/Downloads/mvp0_project_profile_admin_foundation_backendfirst.md`

### Decisao

O conteudo faz sentido e deve entrar como hardening transversal de plataforma,
nao como modulo funcional isolado e nao como tela de administracao.

O melhor momento e **apos o Catalog Core MVP0 minimo e a primeira migracao de
Rates para consumir Catalog Core**, antes de iniciar Dados Mestres e Cutover.
Essa ordem evita que Master Data, Cutover, Jobs, Evidence e Catalog criem regras
proprias para contexto ativo, dominio, capability e visibilidade.

### Estado atual no backend

Ja existe uma fundacao minima:

```text
- User/Auth local;
- Project, Profile e Environment basicos;
- Active Context MVP0 com GET/POST, domain_name normalizado e allowed_domains PUBLIC + dominio ativo;
- Catalog Core reference options e validate/reference ja consomem Active Context quando domain_name nao e informado;
- Project Setup Status basico disponivel em GET /api/v1/platform/projects/{project_id}/setup-status;
- Effective Capabilities basico disponivel em GET /api/v1/platform/active-context/capabilities;
- Navigation Contract ja filtra module.required_capability usando capabilities efetivas do projeto ativo;
- Role e Capability basicos;
- FeatureFlag;
- Module Registry;
- Navigation Contract;
- AuditLog basico;
- Jobs com project_id/profile_id/environment_id/domain_name.
```

Mas ainda faltam pecas importantes para virar a fonte de verdade de plataforma:

```text
- allowed_domains derivado de profile/role/capability;
- capability checks granulares por acao usando Effective Capabilities;
- Domain Access Policy reaproveitada por Catalog, Rates, Master Data e Cutover;
- feature flags com escopo GLOBAL/PROJECT/PROFILE/USER/MODULE;
- APIs admin endurecidas;
- audit log para mudancas administrativas;
- bloqueio backend para endpoints funcionais por role/capability/flag.
```

### Ajustes recomendados no documento antes de virar spec executavel

```text
- Trocar exemplos com nomes reais por exemplos sinteticos como OTM1, PUBLIC e DEMO.
- Tratar client_name como opcional/sanitizado no MVP0.
- Manter conexao OTM real, SSO/OAuth avancado e secret manager externo fora do MVP0.
- Nao exigir active context retroativamente em endpoints ja existentes no mesmo PR;
  fazer a adocao por modulo em fatias pequenas.
- Capability deve autorizar acao, mas domain access deve autorizar escopo de dados.
- Feature flag deve habilitar superficie, nunca substituir permissionamento.
```

### Primeiro recorte MVP0 recomendado

```text
1. Active Context model/API usando Project, Profile e Environment existentes. [ENTREGUE MVP0 inicial]
2. Domain Access Policy simples: PUBLIC + domain_name ativo. [ENTREGUE MVP0 inicial]
3. Excecao controlada para DBA/MASTER com allowed_domains = ["*"].
4. Endpoint GET /api/v1/platform/active-context.
5. Endpoint POST /api/v1/platform/active-context.
6. Capability helper reutilizavel para checagens backend. [ENTREGUE MVP0 inicial]
7. Project Setup Status basico. [ENTREGUE MVP0 inicial]
8. Testes de contrato para USER/ADMIN/DBA/MASTER.
9. Integrar Catalog reference options ao active context em fatia posterior.
10. Integrar Rates batch/create/export/approve ao active context em fatia posterior.
```

### Fora do primeiro recorte

```text
- UI completa de admin;
- SSO corporativo;
- OAuth avancado;
- cloud sync;
- multi-tenant cloud avancado;
- workflow visual de approval;
- editor visual de Project Flow;
- integracao OTM real obrigatoria;
- secret manager externo;
- governanca avancada de change request;
- auditoria forense completa.
```

---

## 5. Dados Mestres / Template Factory

**Fonte:** `C:/Users/Enzo Trabalho/Downloads/mvp0_dados_mestres_template_factory.md`

### Objetivo

Criar uma fundacao backend-first, API-first, DB-first e UI-agnostic para templates de Dados Mestres definidos por metadata.

O modulo nao deve nascer como planilhas fixas. A arquitetura esperada e:

```text
Template Definition
Template Builder
Template Intake
Mapping Engine
Validation Engine
Canonical Records
OTM Output Records
CSV Generator
ZIP + MANIFEST.json
Artifacts + Evidence
```

### Decisoes registradas

```text
- Nao converter Excel direto para CSV OTM.
- Converter Excel para parsed rows, canonical records, output records e entao CSV OTM.
- Templates devem ser versionados.
- A UI futura deve consumir contratos do backend, sem regra de negocio propria.
- Artifacts e evidencias devem ser client-safe.
- Deve consumir OTM Catalog Core para validar mapping targets e referencias.
```

### Escopo MVP0 sugerido

```text
1. Skeleton do modulo master_data. [ENTREGUE MVP0 inicial]
2. Template Definition, Version, Sheet e Field. [INICIADO com MasterDataTemplate DB e sheets_json]
3. Relationship, Output Object e Output Mapping.
4. Seed do template Regions Basic. [ENTREGUE MVP0 inicial]
5. API de list/detail de templates. [ENTREGUE MVP0 inicial]
6. Template Builder para gerar Excel. [INICIADO com endpoint build-workbook gerando XLSX sintético e Artifact client-safe]
7. Batch upload/parse. [INICIADO com upload XLSX, parse por sheet e persistencia em master_data_batches]
8. Validacao estrutural e de relacionamento. [INICIADO com validacao Catalog/Data Dictionary de tabelas/colunas, issues estruturais de workbook, relacionamento same-batch e bloqueio de mapping quando templates possuem regras pendentes]
9. Mapping Engine basico. [INICIADO com mapeamento de batch validado para canonical records por target_column]
10. Geracao de output records. [INICIADO com materializacao de canonical records em master_data_output_records]
11. Geracao de CSVs. [INICIADO com master_data_csv_files e CSV OTM por tabela]
12. ZIP + MANIFEST.json. [INICIADO com pacote CSV ZIP e manifest.json]
13. Artifact/evidence client-safe. [INICIADO com Artifact do workbook de template e pacote CSV ZIP]
14. Seed de Items & Packaging Standard. [ENTREGUE MVP0 inicial com ITEM, PACKAGED_ITEM e TI_HI validados no Data Dictionary]
15. Seed de Locations Basic. [ENTREGUE MVP0 inicial com LOCATION e LOCATION_ADDRESS validados no Data Dictionary, preparando Coordinate Quality]
```

---

## 6. Cutover Checklist & CSVUTIL Builder

**Fonte:** `C:/Users/Enzo Trabalho/Downloads/mvp0_cutover_checklist_csvutil_backendfirst.md`

### Objetivo

Criar uma capacidade backend-first dentro de Load Plan & Cutover para governar decisao, ordem, dependencias, status, readiness e evidencia de cutover.

Decisao central:

```text
Cutover Checklist = decisao, ordem, dependencia, status, readiness e evidencia.
CSVUTIL = ferramenta operacional auxiliar para itens marcados como CSV/CSVUTIL.
Data Dictionary/Catalog Core = validacao de tabelas, campos, relacionamentos e bloqueio de dados transacionais.
```

### Decisoes registradas

```text
- CSVUTIL nao decide o escopo do cutover.
- Checklist catalogado decide escopo, ordem, metodo, dependencias, status e evidencias.
- CSVUTIL no MVP0 apenas gera csvutil.ctl e artifact; nao executa OTM.
- Tabelas tecnicas devem ser metadata editavel, mas validadas.
- Dados transacionais devem ser bloqueados por padrao.
- Overrides exigem capability, justificativa e audit log.
- Deve consumir OTM Catalog Core para macro-objetos, tabelas, categorias e dependencies.
```

### Escopo MVP0 sugerido

```text
1. Checklist templates.
2. Template versions.
3. Seed inicial de macro-objetos OTM setup/master data.
4. Checklist instance a partir de template publicado.
5. Itens com status, evidencia, metodo, ordem e dependencias.
6. Mapping macro-objeto para tabelas tecnicas.
7. Validacao Catalog Core/Data Dictionary para tabelas e colunas.
8. Bloqueio de tabelas transacionais por padrao.
9. CSV eligible e CSV selected.
10. CSVUTIL parameter sets.
11. Overrides por item/tabela.
12. Bulk update de parametros CSVUTIL.
13. Geracao de csvutil.ctl para download.
14. Registro do CTL como artifact/evidence.
15. Readiness endpoint com blockers claros.
```

### Status de implementacao

```text
1. Checklist templates. [INICIADO com seed MVP0_STANDARD_CUTOVER persistido em DB]
2. Template items base. [INICIADO com PACKAGE_REGISTERED, SEQUENCE_REVIEW e TABLE_READY]
3. Checklist instance a partir de LoadPlanPackage. [ENTREGUE primeira fatia backend OTM-14]
4. Itens por pacote/sequencia. [INICIADO com TABLE_READY gerado por tabela tecnica]
5. Evidence/Audit/DomainEvent client-safe. [ENTREGUE para criacao de checklist]
6. Atualizacao de item com status, metodo e evidencia. [ENTREGUE primeira fatia backend OTM-15]
7. Readiness de Cutover Checklist por itens persistidos. [ENTREGUE primeira fatia backend OTM-16]
8. CSVUTIL a partir de itens selecionados do Cutover Checklist. [ENTREGUE primeira fatia backend OTM-17]
9. Gate de Cutover Handoff por readiness do Cutover Checklist. [ENTREGUE primeira fatia backend OTM-18]
10. Parameter set controlado para build CSVUTIL. [ENTREGUE primeira fatia backend OTM-19]
11. Overrides controlados por tabela para CSVUTIL via Cutover Checklist. [ENTREGUE primeira fatia backend OTM-20]
12. Export de pacote Cutover client-safe a partir do checklist. [ENTREGUE primeira fatia backend OTM-21]
13. Decisao Go/No-Go de Cutover baseada em readiness e pacote exportado. [ENTREGUE primeira fatia backend OTM-22]
14. CSVUTIL real, overrides SQL avancados, aprovacao humana avancada e UI. [PENDENTE]
```

---

## 7. Assets Library

**Fonte:** `C:/Users/Enzo Trabalho/Downloads/mvp0_assets_library_backendfirst.md`

### Decisao

O Assets Library faz sentido como modulo transversal de plataforma, mas nao deve
furar a fila atual. Ele deve entrar depois de Rates/Load Plan, Jobs, Catalog Core
e Project/Profile/Admin estarem estabilizados, porque depende diretamente de:

```text
- Artifact Store para armazenamento fisico;
- Evidence Hub para nao confundir asset reutilizavel com evidencia validada;
- Catalog Core para links com macro-objetos, tabelas e campos OTM;
- Project/Profile/Admin para escopo, visibilidade, capability e active context;
- Jobs / Processing Engine para scans, indexacao e operacoes pesadas futuras.
```

### O que faz sentido

```text
- Tratar asset como arquivo reutilizavel governado, nao como artifact nem evidence.
- DB-first para tipos, categorias, tags, visibilidades, status, escopos e sensibilidade.
- Versionamento simples com current_version_id e historico preservado.
- Links genericos para modulo, macro-objeto, tabela OTM, batch, checklist, artifact e evidence.
- Upload/download com SHA256, metadados e storage local controlado.
- Scanner simples de risco para tokens, passwords, Authorization, client_secret e chaves.
- Audit log para criacao, alteracao, download, nova versao, link e classificacao.
- API-first e UI-agnostic para a UI futura apenas consumir classificacoes e acoes.
```

### Ajustes recomendados antes de virar spec executavel

```text
- Nao criar um "Google Drive interno"; metadata obrigatoria e governanca devem vir na primeira fatia.
- Evitar tabela propria asset_audit_logs no MVP0 se AuditLog/DomainEvent existentes forem suficientes.
- Reaproveitar Artifact Store para metadados tecnicos de arquivo quando possivel, mantendo semantica de Asset separada.
- Nao implementar editor DOCX/PDF, preview avancado de ZIP, execucao de SQL/OIC/migration project ou sync cloud.
- Nao permitir GLOBAL para assets com possivel segredo ou dados sensiveis.
- Validar links de MACRO_OBJECT/OTM_TABLE contra Catalog Core/Data Dictionary.
- Usar exemplos sinteticos como OTM1, PUBLIC e DEMO; nao registrar nomes de clientes reais.
```

### Primeiro recorte MVP0 recomendado

```text
1. Skeleton backend do modulo assets. [ENTREGUE primeira fatia backend OTM-23]
2. Modelos DB-first para asset classifications:
   - asset_types;
   - asset_categories;
   - asset_tags;
   - asset_visibility_levels;
   - asset_scope_types;
   - asset_statuses;
   - asset_sensitivity_levels;
   - asset_link_types. [INICIADO com tabela generica asset_classifications OTM-23]
3. Seeds iniciais system-protected. [ENTREGUE primeira fatia backend OTM-23]
4. APIs de listagem de classificacoes. [ENTREGUE primeira fatia backend OTM-23]
5. APIs ADMIN/DBA/MASTER para criar tipo e categoria.
6. Modelo central de asset + asset_versions + asset_files. [INICIADO com asset e asset_versions OTM-24/OTM-25]
7. Criar asset em DRAFT via API. [ENTREGUE primeira fatia backend OTM-24]
8. Upload da primeira versao com SHA256 e size_bytes. [ENTREGUE primeira fatia backend OTM-25]
9. Download da versao atual com audit quando sensivel. [ENTREGUE primeira fatia backend OTM-26]
10. Criar nova versao sem apagar a anterior.
11. Editar metadata basica e arquivar/deprecar asset. [ENTREGUE primeira fatia backend OTM-27]
12. Links genericos para MODULE, MACRO_OBJECT, OTM_TABLE, RATE_BATCH, ARTIFACT e EVIDENCE. [INICIADO com MODULE, MACRO_OBJECT, OTM_TABLE, ARTIFACT e EVIDENCE OTM-28]
13. Busca/filtros simples por tipo, categoria, tag, status, escopo, modulo, macro-objeto e tabela OTM. [ENTREGUE primeira fatia backend OTM-29]
14. Scanner simples de possiveis segredos e bloqueio de GLOBAL quando houver risco. [ENTREGUE primeira fatia backend OTM-30]
15. Testes de permissao, versionamento, filtros, download auditado e scanner. [ENTREGUE primeira fatia backend OTM-31]
```

### Fora do primeiro recorte

```text
- UI completa;
- marketplace interno;
- workflow complexo de aprovacao/publicacao;
- OCR;
- full-text search avancado;
- preview avancado de ZIP;
- editor DOCX/PDF;
- execucao de SQL, OIC, migration project ou CSVUTIL;
- integracao direta com Google Drive/SharePoint;
- validacao profunda de migration project;
- worker distribuido para scans/indexacao.
```

### Posicao recomendada na fila

```text
1. Nao interromper o ciclo atual de Rates/Load Plan/Catalog.
2. Nao entrar antes de Project/Profile/Admin Foundation, porque escopo e visibilidade sao centrais.
3. Entrar preferencialmente depois do MVP0 de Master Data e Cutover Checklist,
   ou como primeira fatia transversal logo antes deles apenas se precisarmos anexar
   templates, guias e pacotes reutilizaveis de forma governada.
4. Se antecipado, limitar a primeira entrega a classifications + metadata + links,
   sem upload pesado e sem editor de conteudo.
```

---

## 8. Integration Mapping Studio

**Fonte:** `C:/Users/Enzo Trabalho/Downloads/mvp0_integration_mapping_studio_backendfirst.md`

**Arquivos de apoio analisados:** payload XML de PlannedShipment, payload JSON de criacao de viagem, amostras de GET REST, documento funcional DOCX e diagrama de mapping. Os dados reais desses arquivos nao devem ser copiados para o repositorio; qualquer teste futuro deve usar fixtures sinteticas como `OTM1`, `PUBLIC`, `DEMO`, `EXT_SYSTEM` e `CARRIER_API`.

### Decisao

O Integration Mapping Studio faz sentido como modulo estrategico futuro, mas nao
deve furar a fila atual. Ele deve entrar depois de Jobs, Catalog Core,
Project/Profile/Admin e Assets Library estarem minimamente disponiveis, porque
depende diretamente de:

```text
- Jobs / Processing Engine para parse, preview, validacao e geracao de spec;
- Artifact Store para payloads, schema tree exports, previews e specs geradas;
- Evidence Hub para registrar validacao/aprovacao sem expor payload cru;
- Assets Library para reutilizar payloads, specs, diagramas, collections e mapping exports;
- Catalog Core para validar objetos OTM, paths conhecidos, refnums, status e endpoints;
- Project/Profile/Admin para escopo, visibilidade, capabilities e active context.
```

### O que os arquivos de apoio mostram

O cenario de referencia deve ser tratado de forma generica e sanitizada como:

```text
OTM PlannedShipment XML
-> Integration Mapping Studio
-> External carrier/delivery API JSON
```

Padroes tecnicos confirmados pelos apoios:

```text
- schema de origem XML com ShipmentHeader, ShipmentStop, ShipUnit e Release;
- schema de destino JSON com header e colecao de entregas;
- mappings diretos de identificadores e datas;
- formatacao de data para ISO 8601;
- lookup REST para dados complementares de location/refnum/address;
- filtro por qualifier de refnum;
- loop em stops de destino;
- join entre stop, ship unit e release;
- agregacoes como contagem/distinct;
- response handling para sucesso/erro;
- documentacao funcional/tecnica geravel a partir do mapping persistido.
```

### O que faz sentido

```text
- Tratar o modulo como specification-first, nao como executor produtivo de integracao.
- Persistir Integration Definition, schemas, schema nodes, mappings, loops, joins, lookups e response actions.
- Gerar schema tree de XML/JSON por API.
- Validar source_path e target_path antes de preview.
- Manter transformacoes controladas, como DIRECT, CONSTANT, CONCAT, FORMAT_DATE_ISO8601, FILTER_BY_QUALIFIER, COUNT_DISTINCT, LOOKUP_VALUE e DEFAULT_IF_EMPTY.
- Usar mocks de lookup no MVP0; nao chamar sistemas externos obrigatoriamente.
- Gerar preview local como job e artifact.
- Gerar spec Markdown como artifact e, futuramente, asset.
- Registrar audit log/domain events para mudancas relevantes.
- Criar fixtures sinteticas para testes, nunca reaproveitando dados reais dos arquivos de apoio.
```

### O que nao faz sentido no MVP0

```text
- Substituir OIC ou virar iPaaS proprio.
- Executar integracao produtiva.
- Fazer deploy externo.
- Gerar package OIC completo.
- Criar canvas visual antes do modelo backend estar estavel.
- Permitir codigo arbitrario como transformacao.
- Armazenar credenciais em mappings/lookups.
- Usar payload real de cliente em testes, artifacts ou evidencias.
- Depender de DOCX/PDF como formato obrigatorio de spec no MVP0.
- Fazer import completo de OpenAPI/XSD complexo.
```

### Primeiro recorte MVP0 recomendado

```text
1. Skeleton backend do modulo integration_mapping. [ENTREGUE primeira fatia backend OTM-39]
2. Module registry + health endpoint. [ENTREGUE primeira fatia backend OTM-39]
3. Modelo/API de Integration Definition com status DRAFT. [ENTREGUE primeira fatia backend OTM-40]
4. Modelo/API de systems/endpoints sem credenciais reais. [ENTREGUE primeira fatia backend OTM-41]
5. Upload/import de payload XML/JSON como artifact interno. [ENTREGUE primeira fatia backend OTM-42]
6. Parser simples XML/JSON para schema tree. [ENTREGUE primeira fatia backend OTM-43]
7. Persistencia de schema documents e schema nodes. [ENTREGUE primeira fatia backend OTM-44]
8. Mapping CRUD tabular. [ENTREGUE primeira fatia backend OTM-45]
9. Transformation type catalog com seeds controlados.
10. Loop definition simples para colecoes.
11. Join rule simples para relacionar estruturas do payload origem.
12. Lookup definition com mocks, sem chamada real obrigatoria.
13. Validation service para paths, required targets, loops, joins e lookups.
14. Preview job com fixture sintetica e resultado como artifact.
15. Markdown spec generator com identificacao, schemas, mappings, loops, lookups, response handling e casos de teste.
16. Audit log/domain events para create/update/validate/preview/generate-spec.
17. Testes com cenario sintetico inspirado no padrao OTM PlannedShipment -> External Delivery JSON.
```

### Fora do primeiro recorte

```text
- UI completa;
- canvas visual;
- geracao ou deploy de package OIC;
- runtime produtivo de integracao;
- autenticacao real em sistemas externos;
- monitoramento produtivo;
- debugger avancado;
- linguagem livre de expressao;
- transformacao por codigo customizado;
- colaboracao em tempo real;
- geracao automatica por IA sem revisao humana;
- DOCX/PDF obrigatorio;
- OpenAPI/XSD complexo completo.
```

### Posicao recomendada na fila

```text
1. Nao interromper o ciclo atual de Rates/Load Plan/Catalog.
2. Nao entrar antes de Jobs, Catalog Core e Project/Profile/Admin Foundation.
3. Entrar preferencialmente depois de Assets Library MVP0, porque payloads, specs e diagrams devem virar assets governados.
4. Se antecipado, limitar a primeira entrega a Integration Definition + schema parser + mapping CRUD + validation, sem preview completo.
5. Usar sempre exemplos sinteticos e remover qualquer dado real dos arquivos de apoio.
```

---

## 9. Order Release Generator Pipeline

**Fonte:** `C:/Users/Enzo Trabalho/Documents/Projetos/OTM General/gerador_or.zip`

**Spec:** `docs/superpowers/specs/2026-05-19-order-release-generator-pipeline-design.md`

### Decisao

O Order Release Generator Pipeline faz sentido como modulo futuro especializado,
mas nao deve reutilizar diretamente o script recebido. O apoio mostra um fluxo
util para gerar Order Releases por template tabular, agrupar linhas por release,
montar XML OTM Transmission/GLogXMLElement/Release/ReleaseLine e opcionalmente
salvar XML local ou postar no OTM.

O modulo deve nascer backend-first, DB-first, API-first e template-driven, para
que a UI futura consiga alterar templates, campos, aliases, defaults,
transformacoes e refnums sem editar codigo.

### Sinergias

```text
- Jobs / Processing Engine para parse, validation, preview, generate XML e submit.
- Catalog Core para validar ORDER_RELEASE, locations, items, commodities, THUs, refnum qualifiers, release method e domain scope.
- Assets Library para guardar templates, payloads de exemplo, specs e XMLs reutilizaveis.
- Evidence Hub para registrar generated XML, validation reports e submission results sem expor payload cru.
- Project/Profile/Admin para capabilities, active environment, domain e conexoes OTM permitidas.
- Integration Mapping Studio para compartilhar conceitos de schema tree/mapping, sem transformar este modulo em iPaaS generico.
```

### Primeiro recorte recomendado

```text
1. Registrar modulo order-release-generator. [ENTREGUE primeira fatia backend OTM-32]
2. Criar health endpoint. [ENTREGUE primeira fatia backend OTM-32]
3. Persistir templates versionados. [ENTREGUE primeira fatia backend OTM-32]
4. Criar seed sintetico TL Order Release. [ENTREGUE primeira fatia backend OTM-32]
5. Criar batch e rows normalizados. [ENTREGUE primeira fatia backend OTM-33]
6. Validar colunas obrigatorias e agrupamento por release_gid. [ENTREGUE primeira fatia backend OTM-33]
7. Gerar preview XML com fixture sintetica. [ENTREGUE primeira fatia backend OTM-34]
8. Persistir XML/db.xml como artifact. [ENTREGUE primeira fatia backend OTM-35]
9. Criar evidence client-safe. [ENTREGUE primeira fatia backend OTM-36]
10. Integrar preview/generate com Jobs. [ENTREGUE primeira fatia backend OTM-37]
11. Deixar submit OTM bloqueado/guarded no MVP0 sem capability/conexao. [ENTREGUE primeira fatia backend OTM-38]
```

### Fora do primeiro recorte

```text
- UI de template;
- upload produtivo ao OTM;
- credenciais em planilha;
- runtime generico de integracao;
- copiar dados reais dos arquivos de apoio;
- suporte completo a todos os campos de Order Release;
- validacao OTM real obrigatoria.
```

### Posicao recomendada na fila

```text
1. Nao interromper Jobs/Catalog Core.
2. Entrar depois de Jobs MVP0 e Catalog Core minimo.
3. Pode entrar antes do Integration Mapping Studio completo se for limitado a Order Release + XML artifact local.
4. Submit OTM direto deve aguardar Project/Profile/Admin capabilities e conexoes governadas.
```

---

## 10. Ordem recomendada depois de Rates

```text
1. Fechar hardening de Rates/Load Plan/Evidence Hub.
2. Endurecer Jobs / Processing Engine MVP0.
3. Implementar OTM Catalog Core MVP0 minimo.
4. Migrar Rates para consumir Catalog Core onde reduzir duplicacao.
5. Endurecer Project / Profile / Admin Foundation para active context, capabilities e domain access.
6. Implementar Dados Mestres / Template Factory MVP0.
7. Implementar Coordinate Quality MVP0 dentro de Dados Mestres para validacao Lat/Lon de Locations, sem UI/exe e sem dependencia obrigatoria de geocoder externo.
8. Integrar load packages de Dados Mestres no Load Plan existente.
9. Implementar Cutover Checklist & CSVUTIL Builder.
10. Implementar Assets Library MVP0, se a fila ainda exigir biblioteca governada de arquivos reutilizaveis.
11. Implementar Order Release Generator Pipeline MVP0 se a fila pedir geracao governada de XML/db.xml para testes OTM.
12. Implementar Integration Mapping Studio MVP0, se a fila pedir especificacao/mapping de integracoes.
13. Expandir Evidence Hub para visoes consolidadas entre Rates, Jobs, Catalog, Master Data, Cutover, Assets, Order Release Generator e Integrations.
```

---

## 11. Guardrails permanentes

```text
- Backend-first, API-first, DB-first e UI-agnostic.
- Nao usar nomes de clientes reais.
- Exemplos devem usar dados sinteticos.
- Data Dictionary deve orientar tabelas, dependencias e ordem de carga.
- CSVs OTM devem seguir formato: tabela na primeira linha, colunas na segunda, valores depois.
- Se houver data em CSV OTM, incluir antes dos valores:
  exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'
- Em duvidas tecnicas ou funcionais de OTM/Oracle, consultar documentacao oficial Oracle ou perguntar.
- Nao executar cargas reais no OTM no MVP0.
```
