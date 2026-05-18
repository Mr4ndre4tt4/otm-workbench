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

## 2. Proximo modulo estrutural: OTM Catalog Core

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
2. Criar OTM Catalog Core MVP0 minimo.
3. Migrar Rates aos poucos para consumir Catalog Core.
4. Iniciar Master Data Template Factory usando Catalog Core desde o inicio.
5. Iniciar Cutover Checklist/CSVUTIL usando Catalog Core desde o inicio.
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

## 3. Dados Mestres / Template Factory

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
1. Skeleton do modulo master_data.
2. Template Definition, Version, Sheet e Field.
3. Relationship, Output Object e Output Mapping.
4. Seed do template Regions Basic.
5. API de list/detail de templates.
6. Template Builder para gerar Excel.
7. Batch upload/parse.
8. Validacao estrutural e de relacionamento.
9. Mapping Engine basico.
10. Geracao de output records.
11. Geracao de CSVs.
12. ZIP + MANIFEST.json.
13. Artifact/evidence client-safe.
14. Seed de Items & Packaging Standard.
```

---

## 4. Cutover Checklist & CSVUTIL Builder

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

---

## 5. Ordem recomendada depois de Rates

```text
1. Fechar hardening de Rates/Load Plan/Evidence Hub.
2. Implementar OTM Catalog Core MVP0 minimo.
3. Migrar Rates para consumir Catalog Core onde reduzir duplicacao.
4. Implementar Dados Mestres / Template Factory MVP0.
5. Integrar load packages de Dados Mestres no Load Plan existente.
6. Implementar Cutover Checklist & CSVUTIL Builder.
7. Expandir Evidence Hub para visoes consolidadas entre Rates, Catalog, Master Data e Cutover.
```

---

## 6. Guardrails permanentes

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
