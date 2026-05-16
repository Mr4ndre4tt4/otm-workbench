# OTM Project Workbench — Arquitetura Funcional

**Data de referência:** 2026-05-16  
**Objetivo do documento:** definir a arquitetura funcional da nova versão do OTM Project Workbench, reconstruída do zero, com foco em jornadas, módulos, regras de negócio, papéis, fluxos, critérios de aceite e governança funcional.  
**Documento complementar:** `arquitetura_tecnica_otm_workbench.md`.

---

## 1. Visão executiva

O OTM Project Workbench deve ser reconstruído como uma **bancada operacional funcional para projetos Oracle Transportation Management**, orientada por jornadas e não por telas técnicas isoladas.

A nova aplicação deve ajudar consultores e times de projeto a:

- preparar dados antes da carga no OTM;
- validar estrutura, dependências e qualidade dos dados;
- transformar templates amigáveis ao cliente em artefatos técnicos OTM;
- gerar pacotes CSV/XML/ZIP com manifesto e rastreabilidade;
- apoiar validação de tarifas e pacotes CRP;
- controlar plano de carga, CSVUTIL, setup control e cutover;
- produzir evidências client-safe;
- reduzir retrabalho, planilhas soltas e ausência de governança.

A aplicação **não substitui o OTM**. Ela atua como uma camada de preparação, validação, organização, rastreabilidade e governança operacional.

A decisão funcional mais importante é:

```text
O consultor não deve navegar por ferramentas técnicas.
O consultor deve navegar por jornadas de trabalho com próxima ação clara.
```

---

## 2. Princípios funcionais da nova aplicação

### 2.1 Princípios gerais

1. **Fluxo antes de ferramenta**  
   O usuário deve entender o que fazer, por que fazer e qual o próximo passo. Ferramentas técnicas ficam dentro do fluxo, não como menus soltos.

2. **Cada módulo deve gerar valor operacional real**  
   Nenhum módulo público deve aparecer como placeholder, tela vazia ou protótipo sem ação útil.

3. **Cada ação relevante deve gerar rastreabilidade**  
   Uploads, validações, conversões, exports, aprovações, blockers e evidências devem manter histórico.

4. **O usuário comum não deve ver complexidade administrativa**  
   Configurações, feature flags, ferramentas dev-only, OTM Explorer e catálogos técnicos ficam restritos a ADMIN/DBA/MASTER.

5. **Evidência deve ser client-safe**  
   Reports devem mostrar resumo, status, origem e referências. Payload bruto sensível não deve ser exposto.

6. **Módulos devem conversar por artefatos, manifestos e eventos funcionais**  
   Dados Mestres gera Load Package. Load Plan consome Load Package. Evidence Hub indexa evidências. Cutover consome readiness e pacotes confirmados.

7. **A navegação deve refletir o estado real do projeto**  
   Home, Project Readiness e menus devem exibir status, blockers e próximas ações derivados do backend.

8. **Governança sem travar produtividade**  
   Alterações críticas de catálogo, fluxo, pack, sequência ou permissão exigem trilha de decisão e rollback, mas o consultor deve conseguir executar o trabalho operacional sem fricção excessiva.

---

## 3. Escopo funcional da nova versão

### 3.1 Dentro do escopo

A nova aplicação deve cobrir:

- criação e seleção de projetos;
- perfis, ambientes e domínios funcionais;
- Home / Project Cockpit;
- Project Readiness;
- Data Factory / Dados Mestres;
- Template & Mapping Studio, inicialmente read-only/preview;
- Rates Studio;
- Load Plan & CSVUTIL;
- Cutover Readiness e Execution Evidence;
- Evidence Hub;
- Admin Console;
- ferramentas dev/DBA somente por permissão ou feature flag;
- integração funcional com OTM por artefatos, CSVUTIL, XML, CSV, ZIP, consulta e evidência.

### 3.2 Fora do escopo inicial

Não devem ser prioridade no início:

- substituir o OTM;
- criar um editor livre de qualquer objeto OTM;
- expor OTM Explorer como módulo público;
- permitir alterações de catálogo sem governança;
- publicar automaticamente em ambiente OTM real sem validação e evidência;
- construir microfluxos específicos de um único cliente como se fossem produto core;
- criar telas bonitas sem lifecycle, artifact, evidence e critério de aceite.

---

## 4. Personas e papéis funcionais

### 4.1 Personas principais

| Persona | Descrição | Necessidade principal |
|---|---|---|
| **Consultor Funcional OTM** | Executa preparação de dados, validação, revisão e exportação | Ter fluxo guiado e evitar erro de carga |
| **Líder Funcional / PM** | Acompanha status, blockers, evidências e readiness | Ter visibilidade por projeto e próxima ação |
| **Consultor Técnico / DBA** | Apoia setup, queries, troubleshooting, CSVUTIL e Data Dictionary | Ter ferramentas técnicas controladas |
| **Admin da Aplicação** | Gerencia usuários, perfis, ambientes, conexões e flags | Controlar acesso e governança |
| **Cliente / Usuário de Negócio** | Fornece dados e recebe correction reports | Entender claramente o que corrigir |
| **Auditor / Sponsor do Projeto** | Consulta evidências, pacotes e status | Ter rastreabilidade client-safe |

### 4.2 Papéis sistêmicos

| Papel | Descrição funcional | Deve poder fazer | Não deve poder fazer |
|---|---|---|---|
| `USER` | Consultor/operador do fluxo | Intake, validação, revisão, export operacional, evidências permitidas | Ver admin técnico, alterar catálogo, ver payload sensível |
| `ADMIN` | Administrador funcional | Gerenciar usuários, perfis, projetos, permissões, flags funcionais | Executar ações DBA sensíveis sem permissão adicional |
| `DBA` | Usuário técnico avançado | Acessar ferramentas técnicas, Data Dictionary, OTM Explorer controlado | Expor ferramentas técnicas ao usuário comum |
| `MASTER` | Super admin | Configuração global, override, rollback, governança | Ignorar auditabilidade |

### 4.3 Princípios de permissão

```text
Permissão funcional deve ser por capability, não apenas por tela.
```

Exemplos de capabilities funcionais:

```text
project.view
project.setup.execute
master_data.batch.create
master_data.batch.validate
master_data.batch.convert
master_data.package.export
rates.batch.approve
load_plan.csvutil.generate
load_plan.cutover.readiness.view
evidence.artifact.download
admin.users.manage
dev.otm_explorer.access
```

---

## 5. Conceitos funcionais fundamentais

### 5.1 Workspace

Representa o espaço colaborativo de um time ou organização.

Exemplos:

```text
- Oracle LATAM Consulting
- Time OTM Brasil
- Projeto Ajinomoto
```

### 5.2 Project

Representa uma iniciativa real de implementação, rollout, melhoria ou migração.

Um projeto pode ter:

- cliente;
- escopo;
- país/região;
- fase;
- ambiente ativo;
- domínio OTM;
- módulos habilitados;
- evidências;
- batches;
- pacotes;
- planos de carga;
- histórico de decisões.

### 5.3 Profile

Representa um contexto funcional de trabalho.

Pode conter:

- cliente;
- domínio OTM;
- ambiente;
- paths locais;
- preferências;
- configuração de conexão;
- metadata de packs e load plan;
- feature flags específicas.

### 5.4 Environment

Representa o ambiente de trabalho ou carga.

Exemplos:

```text
DEV
TEST
UAT
CRP
PROD
```

### 5.5 Batch

Representa um lote de dados importados, validados, convertidos ou exportados.

Exemplos:

```text
- Batch de Regions
- Batch de Items & Packaging
- Batch de Location
- Batch de tarifas
```

### 5.6 Load Package

Representa um pacote técnico gerado para carga no OTM.

Deve conter:

- arquivos CSV/XML;
- ordem de carga;
- manifesto;
- resumo;
- status;
- origem;
- evidências.

### 5.7 Manifest

Documento técnico-funcional que descreve um pacote ou artefato.

Deve conter:

- origem;
- módulo fonte;
- arquivos gerados;
- contagens;
- status;
- validações executadas;
- blockers;
- hash/referência;
- data/hora;
- usuário responsável.

### 5.8 Evidence

Registro client-safe de uma ação, pacote, validação ou decisão.

Não deve ser apenas “um arquivo”. Deve ser um objeto funcional rastreável.

---

## 6. Navegação funcional recomendada

### 6.1 Menu principal do usuário comum

```text
Home / Project Cockpit
Project Readiness
Data Factory
Rates Studio
Load Plan & Cutover
Evidence Hub
```

### 6.2 Menu administrativo

```text
Admin Console
- Users & Roles
- Projects & Profiles
- Environments
- OTM Connections
- Feature Flags
- Audit Log
- Catalog Governance
```

### 6.3 Menu técnico controlado

```text
Developer / DBA Tools
- OTM Explorer
- Data Dictionary
- FK Catalog
- Environment Readiness
- Oracle Lab / SQL Lab
```

Esse menu deve aparecer somente para `DBA`, `MASTER` ou usuários com capability específica.

### 6.4 Mapa de navegação sugerido

```text
/
├── /login
├── /home
├── /project-readiness
├── /data-factory
│   ├── /overview
│   ├── /template-packs
│   ├── /batches
│   ├── /validation
│   ├── /conversion
│   ├── /coordinate-quality
│   └── /evidence
├── /rates-studio
│   ├── /overview
│   ├── /templates
│   ├── /upload
│   ├── /validation
│   ├── /approval
│   ├── /export
│   └── /evidence
├── /load-plan-cutover
│   ├── /overview
│   ├── /load-packages
│   ├── /csvutil-builder
│   ├── /zip-analysis
│   ├── /setup-review
│   ├── /load-sequence
│   ├── /cutover-readiness
│   └── /execution-evidence
├── /evidence-hub
├── /admin
└── /dev-tools
```

---

## 7. Mapa funcional de domínios

```text
┌─────────────────────────────────────────────────────────────┐
│                    Project Cockpit / Home                   │
│  Status, próximas ações, blockers, atalhos e visão geral     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Project Readiness                       │
│  Perfil, ambiente, domínio, conexão, permissões e checklist  │
└───────────────┬───────────────────────┬─────────────────────┘
                │                       │
                ▼                       ▼
┌───────────────────────────────┐ ┌───────────────────────────┐
│         Data Factory           │ │       Rates Studio         │
│ Templates, batches, validação, │ │ Tarifas, workbook, issues, │
│ conversão e load packages      │ │ aprovação, XML/CSV e CRP   │
└───────────────┬───────────────┘ └──────────────┬────────────┘
                │                                │
                └───────────────┬────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Load Plan & Cutover                      │
│ CSVUTIL, ZIP analysis, review, sequência, readiness, exec.   │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         Evidence Hub                        │
│ Evidências, artefatos, manifestos, downloads e auditoria     │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Macro-jornadas funcionais

## 8.1 Jornada 1 — Project Onboarding & Readiness

### Objetivo

Preparar o projeto para execução, garantindo que o usuário esteja no contexto correto antes de importar dados, validar tarifas ou gerar pacotes.

### Fluxo funcional

```text
1. Usuário faz login.
2. Seleciona ou cria workspace/projeto.
3. Seleciona ou cria perfil.
4. Define ambiente e domínio OTM.
5. Configura conexão OTM quando aplicável.
6. Valida permissões e capabilities.
7. Project Readiness calcula status.
8. Home exibe próxima ação recomendada.
```

### Saídas esperadas

- Projeto ativo definido;
- perfil ativo definido;
- ambiente ativo definido;
- domínio OTM definido;
- status de readiness;
- blockers claros;
- próxima ação funcional.

### Critérios de aceite

- O usuário não deve conseguir executar fluxos críticos sem projeto/perfil ativo.
- O usuário deve entender claramente o que falta configurar.
- A Home deve exibir o estado real do projeto.
- Admin settings não devem se misturar ao checklist funcional do consultor.

---

## 8.2 Jornada 2 — Template Factory & Data Intake

### Objetivo

Transformar dados recebidos do cliente em batches persistentes, validados e prontos para conversão em artefatos OTM.

### Fluxo funcional

```text
1. Usuário acessa Data Factory.
2. Escolhe um pack de negócio.
3. Baixa template amigável.
4. Cliente/consultor preenche o template.
5. Usuário faz upload.
6. Sistema cria batch persistente.
7. Sistema valida estrutura.
8. Sistema valida dados e dependências.
9. Usuário corrige ou gera correction report.
10. Batch aprovado segue para conversão.
```

### Packs prioritários

| Pack | Objetos OTM | Valor funcional |
|---|---|---|
| **Regions** | `REGION`, `REGION_DETAIL` | Base para regiões, zonas e rotas |
| **Items & Packaging** | `ITEM`, `SHIP_UNIT_SPEC`, `PACKAGED_ITEM`, `TI_HI` | Base para produtos, embalagem e unidade logística |
| **Location** | `LOCATION` e relacionados | Base para pontos logísticos, origem/destino e coordenadas |

### Saídas esperadas

- batch criado;
- issues identificadas;
- correction report quando necessário;
- status funcional do batch;
- trilha de ações;
- batch reabrível.

### Critérios de aceite

- Todo upload deve gerar um batch rastreável.
- O usuário deve conseguir voltar ao batch depois.
- Erros devem ser claros e acionáveis.
- Dependências devem ser validadas antes da conversão.
- Dados inválidos não devem gerar load package aprovado.

---

## 8.3 Jornada 3 — Validation, Transformation & Export

### Objetivo

Converter batches válidos em pacotes técnicos OTM com ordem correta, manifesto, evidência e possibilidade de uso no Load Plan.

### Fluxo funcional

```text
1. Batch fica com status válido.
2. Usuário solicita conversão.
3. Sistema transforma dados amigáveis em objetos técnicos OTM.
4. Sistema gera arquivos CSV/XML quando aplicável.
5. Sistema cria ZIP ordenado.
6. Sistema cria MANIFEST.json.
7. Sistema registra artifact e evidence.
8. Load Package fica disponível para Load Plan.
```

### Saídas esperadas

- ZIP OTM;
- arquivos CSV/XML;
- manifesto;
- evidence;
- artifact metadata;
- status de pacote.

### Critérios de aceite

- Todo pacote exportado deve ter manifesto.
- O manifesto deve informar origem, arquivos, contagens, validações e status.
- Pacote gerado deve apontar para o batch de origem.
- Evidence deve ser client-safe.
- Load Plan deve conseguir consumir o pacote.

---

## 8.4 Jornada 4 — Rates Studio & CRP

### Objetivo

Transformar planilhas de tarifas em objetos de tarifa OTM validados, aprováveis e exportáveis.

### Fluxo funcional

```text
1. Usuário baixa template de tarifas.
2. Usuário faz upload do workbook preenchido.
3. Sistema normaliza os dados.
4. Sistema valida offering, geo, lane, custos, acessórios e condições.
5. Sistema lista issues.
6. Usuário revisa e corrige.
7. Usuário aprova batch quando válido.
8. Sistema gera XML/CSV OTM quando aplicável.
9. Sistema gera correction report, CRP package e evidence.
```

### Saídas esperadas

- batch de tarifas;
- issues de validação;
- aprovação;
- XML de tarifas;
- CSV OTM quando aplicável;
- correction report;
- CRP package;
- evidence.

### Critérios de aceite

- Batch de tarifas deve ter status claro.
- Aprovação deve ser controlada por permissão.
- Não deve haver evidência falsa de execução em sandbox.
- Export deve ser separado de validação.
- O usuário deve entender o motivo de bloqueio.

---

## 8.5 Jornada 5 — Load Plan, CSVUTIL & Setup Control

### Objetivo

Ser o centro operacional de preparação de carga, análise de pacotes, CSVUTIL, review queue, sequência, blockers e readiness para cutover.

### Fluxo funcional

```text
1. Load Plan recebe Load Packages de Dados Mestres e Rates.
2. Usuário analisa pacotes disponíveis.
3. Sistema calcula sequência/dependências.
4. Usuário gera ou analisa CSVUTIL.
5. Sistema analisa ZIPs e histórico de cargas.
6. Review queue identifica itens incertos.
7. Usuário classifica/decide itens.
8. Sistema bloqueia itens não confirmados.
9. Sistema consolida readiness.
10. Cutover consome apenas itens elegíveis.
```

### Saídas esperadas

- Load Plan;
- CTL/CL;
- ZIP analysis;
- review queue;
- decisões de revisão;
- sequência de carga;
- blockers;
- readiness manifest;
- handoff para cutover.

### Critérios de aceite

- Itens incertos não entram automaticamente em cutover.
- Usuário deve ver por que algo está bloqueado.
- Sequência deve ser clara e justificável.
- Review queue deve manter decisão e trilha.
- Cutover deve consumir Load Plan, não duplicar lógica.

---

## 8.6 Jornada 6 — Cutover Readiness & Execution Evidence

### Objetivo

Apoiar preparação e execução de cutover com pacotes, checklist, blockers, prévia, export e evidência.

### Fluxo funcional

```text
1. Load Plan consolida pacotes elegíveis.
2. Cutover Readiness exibe blockers e evidências exigidas.
3. Usuário revisa checklist.
4. Usuário gera preview do pacote.
5. Usuário exporta pacote quando pronto.
6. Sistema registra evidência de execução.
7. Evidence Hub indexa artefatos e status.
```

### Saídas esperadas

- checklist de cutover;
- blockers;
- preview;
- pacote exportado;
- execution evidence;
- link para artifacts.

### Critérios de aceite

- Cutover não deve ser módulo mental paralelo.
- Cutover deve ser uma etapa de execução do Load Plan.
- Usuário não deve conseguir exportar pacote bloqueado sem override permitido.
- Toda execução deve gerar evidência.

---

## 8.7 Jornada 7 — Evidence, Audit & Governance

### Objetivo

Consolidar evidências, artefatos, manifestos e decisões de forma rastreável, segura e consultável.

### Fluxo funcional

```text
1. Módulo fonte gera artifact/manifest/evidence.
2. Evidence Hub indexa a evidência.
3. Usuário consulta por projeto, módulo, tipo ou status.
4. Usuário baixa artefatos permitidos.
5. Admin consulta audit log quando necessário.
6. Mudanças críticas passam por decisão/rollback.
```

### Saídas esperadas

- evidence records;
- downloads;
- archive packages;
- audit log;
- decisão/rollback;
- vínculo entre artefato e módulo fonte.

### Critérios de aceite

- Reports não expõem payload bruto sensível.
- Toda evidência tem origem, status e data.
- Todo artifact aponta para o módulo fonte.
- Usuário só baixa o que tem permissão para baixar.
- Mudanças críticas têm trilha de decisão.

---

# 9. Módulos funcionais da nova aplicação

## 9.1 Home / Project Cockpit

### Objetivo funcional

Ser a tela inicial do projeto ativo, mostrando status, blockers, próximas ações e atalhos para os fluxos relevantes.

### Perguntas que a tela deve responder

```text
Em qual projeto estou?
Qual ambiente/domínio estou usando?
Qual fase está em andamento?
O que está bloqueado?
Qual é a próxima ação recomendada?
Quais evidências já existem?
Quais pacotes estão prontos?
```

### Componentes funcionais

| Componente | Função |
|---|---|
| Project Context | Mostra projeto, cliente, domínio, ambiente e perfil ativo |
| Journey Status | Mostra status das macro-jornadas |
| Next Best Action | Indica a próxima ação recomendada |
| Blockers | Lista bloqueios críticos |
| Recent Activity | Mostra ações recentes |
| Evidence Summary | Resume evidências geradas |
| Quick Links | Acesso aos módulos permitidos |

### Status possíveis

```text
NOT_STARTED
IN_PROGRESS
ATTENTION
BLOCKED
READY
COMPLETED
```

### Regras funcionais

- Cards devem ser derivados de status real.
- Não deve haver card placeholder.
- A próxima ação deve levar para tela acionável.
- Usuário comum não vê CTA administrativo.
- Admin pode ver alertas adicionais de configuração.

### Critérios de aceite

- Home mostra projeto/perfil/ambiente ativo.
- Home mostra pelo menos uma próxima ação relevante.
- Home exibe blockers quando existirem.
- Home não mostra módulos desabilitados.
- Home respeita permissões.

---

## 9.2 Project Readiness

### Objetivo funcional

Validar se o projeto possui pré-requisitos mínimos para iniciar as jornadas operacionais.

### Checklist funcional

| Área | Verificação |
|---|---|
| Projeto | Existe projeto ativo |
| Perfil | Existe perfil ativo |
| Ambiente | Ambiente definido |
| Domínio | Domínio OTM definido |
| Permissões | Usuário possui capabilities mínimas |
| OTM Connection | Configurada quando necessária |
| Data Dictionary | Disponível quando módulos dependem dele |
| Feature Flags | Módulos corretos habilitados |
| Artifact Path | Diretório local disponível |

### Regras funcionais

- Project Readiness não deve duplicar Admin Console.
- Deve explicar o bloqueio em linguagem funcional.
- Deve sugerir próxima ação.
- Ações administrativas aparecem apenas para ADMIN/DBA/MASTER.

### Exemplo de blocker

```json
{
  "code": "OTM_CONNECTION_MISSING",
  "message": "A conexão OTM ainda não foi configurada para este ambiente.",
  "next_action": "Solicite a configuração ao administrador ou configure em Admin Console.",
  "required_role": "ADMIN"
}
```

### Critérios de aceite

- Usuário entende o que está pronto e o que falta.
- Bloqueios possuem próxima ação.
- Checklist é consumido pela Home.
- Configurações sensíveis não são expostas ao usuário comum.

---

## 9.3 Data Factory / Dados Mestres

### Objetivo funcional

Centralizar preparação, intake, validação, conversão e exportação de dados mestres OTM.

### Subviews recomendadas

| Subview | Objetivo |
|---|---|
| Overview | Visão geral de packs, batches e blockers |
| Template Packs | Lista de packs e download de templates |
| Imported Batches | Histórico e reabertura de batches |
| Validation | Issues, dependências e correções |
| Conversion & OTM CSV | Conversão e geração de ZIP/manifest |
| Coordinate Quality | Validação Lat/Lon para Locations |
| Evidence | Evidências geradas pelo módulo |

### Packs prioritários

#### Regions

Objetivo:

```text
Permitir cadastro controlado de regiões e detalhes de região.
```

Objetos:

```text
REGION
REGION_DETAIL
```

Validações funcionais:

- Região possui identificador válido.
- Região possui pelo menos um detalhe quando exigido.
- Detalhes referenciam região existente no mesmo batch ou baseline.
- Dados obrigatórios estão preenchidos.
- Sequência de carga respeita dependência.

#### Items & Packaging

Objetivo:

```text
Permitir cadastro controlado de itens, especificações de unidade de embarque e embalagens.
```

Objetos:

```text
ITEM
SHIP_UNIT_SPEC
PACKAGED_ITEM
TI_HI
```

Validações funcionais:

- Item possui identificador válido.
- Packaged Item referencia Item existente.
- Ship Unit Spec existe quando exigido.
- TI/HI está coerente quando aplicável.
- Dependências são resolvidas antes da conversão.

#### Location

Objetivo:

```text
Permitir preparação de locais logísticos com dados mínimos de endereço e coordenadas.
```

Validações funcionais:

- Location possui identificador válido.
- Nome/endereço/cidade/país estão preenchidos quando obrigatórios.
- Latitude/longitude têm formato válido.
- Coordenadas fazem sentido para o país/região quando política estiver habilitada.
- Dados faltantes geram correction report.

### Lifecycle funcional do batch

```text
DRAFT
UPLOADED
STRUCTURE_VALIDATED
DATA_VALIDATED
BLOCKED
READY_TO_CONVERT
CONVERTED
EXPORTED
EVIDENCE_GENERATED
ARCHIVED
```

### Ação primária por estado

| Estado | Ação primária |
|---|---|
| `DRAFT` | Fazer upload |
| `UPLOADED` | Validar estrutura |
| `STRUCTURE_VALIDATED` | Validar dados |
| `DATA_VALIDATED` | Converter |
| `BLOCKED` | Revisar issues / gerar correction report |
| `READY_TO_CONVERT` | Converter para OTM CSV |
| `CONVERTED` | Exportar ZIP |
| `EXPORTED` | Ver evidência / enviar para Load Plan |
| `EVIDENCE_GENERATED` | Abrir Evidence Hub |
| `ARCHIVED` | Reabrir ou consultar histórico |

### Issues funcionais

| Severidade | Significado | Pode converter? |
|---|---|---|
| `ERROR` | Bloqueio real | Não |
| `WARNING` | Risco ou dado suspeito | Sim, com atenção/política |
| `INFO` | Informação ou recomendação | Sim |

### Saídas funcionais

- batch;
- validation issues;
- correction report;
- load package;
- ZIP OTM;
- `MANIFEST.json`;
- evidence;
- artifact references.

### Critérios de aceite

- Usuário consegue baixar template por pack.
- Usuário consegue importar e reabrir batch.
- Validação explica erros de forma acionável.
- Dependências são validadas.
- ZIP gerado tem ordem e manifesto.
- Evidence é gerada sem payload sensível.

---

## 9.4 Template & Mapping Studio

### Objetivo funcional

Permitir visualizar e governar como templates amigáveis ao cliente são mapeados para campos técnicos OTM.

### Escopo inicial recomendado

```text
Preview read-only versionado dentro de Data Factory.
```

### O que deve mostrar

| Área | Conteúdo |
|---|---|
| Template Field | Campo apresentado ao cliente |
| OTM Object | Objeto técnico OTM |
| OTM Field | Campo técnico de destino |
| Required | Obrigatoriedade |
| Default | Valor padrão |
| Transformation | Regra de transformação |
| Validation Rule | Regra de validação |
| Version | Versão do mapping |

### Regras funcionais

- Não permitir editor livre no MVP.
- Mudanças de mapping devem passar por governança.
- Mapping deve ser versionado.
- Preview deve explicar de forma clara o que cada campo faz.
- Data Dictionary deve validar campos técnicos.

### Critérios de aceite

- Usuário consegue visualizar mapping por pack.
- Usuário entende origem e destino do campo.
- Admin consegue saber qual versão está ativa.
- Mudanças não aprovadas não impactam batches.

---

## 9.5 Rates Studio

### Objetivo funcional

Preparar, validar, aprovar e exportar tarifas OTM a partir de planilhas.

### Subviews recomendadas

| Subview | Objetivo |
|---|---|
| Overview | Status dos batches e pendências |
| Templates | Download de template de tarifas |
| Upload | Envio do workbook |
| Validation | Issues por offering/geo/lane/custo |
| Approval | Aprovação controlada |
| Export | XML/CSV OTM e CRP package |
| Evidence | Evidências de validação e export |

### Entidades funcionais

```text
Rate Batch
Rate Offering
Rate Geo
X Lane
Rate Geo Cost
Cost Group
Condition
Accessorial
Validation Issue
Publish Target
```

### Lifecycle de batch de tarifas

```text
DRAFT
UPLOADED
NORMALIZED
VALIDATED
BLOCKED
READY_FOR_APPROVAL
APPROVED
EXPORTED_XML
EXPORTED_CSV
CRP_PACKAGE_GENERATED
EVIDENCE_GENERATED
```

### Regras funcionais

- Upload deve criar batch rastreável.
- Normalização deve separar entrada do cliente do modelo interno.
- Issues devem ser agrupadas por tipo e severidade.
- Aprovação deve exigir capability específica.
- Exportação não deve ocorrer para batch bloqueado.
- Sandbox OTM real deve ser tratado como evidência futura, não presumida.

### Critérios de aceite

- Usuário consegue baixar template.
- Usuário consegue subir workbook.
- Sistema mostra issues claras.
- Usuário autorizado consegue aprovar.
- XML/CSV são gerados quando batch está apto.
- Correction report/CRP package são gerados.
- Evidence aponta para batch e artefatos.

---

## 9.6 Load Plan & Cutover

### Objetivo funcional

Unificar preparação de carga, CSVUTIL, setup control, sequência, review, readiness e cutover.

### Subviews recomendadas

| Subview | Objetivo |
|---|---|
| Overview | Estado geral do plano |
| Load Packages | Pacotes disponíveis para carga |
| CSVUTIL Builder | Geração de CTL/CL |
| ZIP Analysis | Análise de pacotes e histórico |
| Setup Review | Fila de revisão e decisões |
| Load Sequence | Sequência e dependências |
| Cutover Readiness | Blockers e checklist |
| Execution Evidence | Evidências de execução |

### Objetos funcionais

```text
Load Plan
Load Package
CSVUTIL Script
ZIP Analysis
Review Item
Review Decision
Load Sequence Step
Cutover Package
Cutover Checklist
Execution Evidence
```

### Lifecycle do Load Plan

```text
DRAFT
PACKAGES_ATTACHED
SEQUENCE_REVIEWED
CSVUTIL_GENERATED
REVIEW_REQUIRED
REVIEW_COMPLETED
READY_FOR_CUTOVER
CUTOVER_EXPORTED
EXECUTION_EVIDENCE_GENERATED
CLOSED
```

### Review Queue

A review queue deve controlar itens incertos antes de permitir handoff para cutover.

Status possíveis:

```text
PENDING_REVIEW
CONFIRMED
REJECTED
NEEDS_MANUAL_ACTION
EXCLUDED_FROM_CUTOVER
```

### Regras funcionais

- Load Plan deve consumir pacotes gerados por Data Factory e Rates Studio.
- Itens incertos não entram automaticamente no pacote de cutover.
- Decisões de review devem ser auditáveis.
- Sequência de carga deve ser visível.
- CSVUTIL deve ter histórico e evidência.
- Cutover é etapa do Load Plan, não módulo separado.

### Critérios de aceite

- Usuário vê pacotes disponíveis.
- Usuário entende sequência sugerida.
- Usuário consegue gerar/analisar CSVUTIL.
- Review queue bloqueia itens incertos.
- Readiness mostra blockers e evidências exigidas.
- Pacote de cutover só é exportado quando elegível ou com override permitido.

---

## 9.7 Evidence Hub

### Objetivo funcional

Ser o centro canônico de evidências, artefatos, manifestos, status e rastreabilidade do projeto.

### Tipos de evidência

| Tipo | Origem |
|---|---|
| `MASTER_DATA_VALIDATION` | Data Factory |
| `LOAD_PACKAGE_EXPORT` | Data Factory |
| `RATE_VALIDATION` | Rates Studio |
| `RATE_EXPORT` | Rates Studio |
| `CSVUTIL_GENERATED` | Load Plan |
| `ZIP_ANALYSIS` | Load Plan |
| `CUTOVER_READINESS` | Load Plan & Cutover |
| `CUTOVER_EXECUTION` | Cutover Execution |
| `CLIENT_CORRECTION_REPORT` | Data Factory/Rates |
| `ADMIN_DECISION` | Admin/Governance |

### Campos funcionais mínimos

```text
evidence_id
project_id
source_module
source_entity_type
source_entity_id
evidence_type
status
summary
artifact_refs
manifest_ref
created_by
created_at
client_safe
sensitivity_level
```

### Regras funcionais

- Evidence Hub consome evidências geradas por outros módulos.
- Não deve reconstruir lógica do módulo fonte.
- Não deve expor payload técnico bruto.
- Deve permitir download somente conforme permissão.
- Deve permitir archive package por projeto/fase.

### Critérios de aceite

- Usuário consegue filtrar evidências por módulo, tipo e status.
- Cada evidência aponta para origem.
- Detalhe é client-safe.
- Artifact download respeita permissão.
- Evidence archive consolida pacote rastreável.

---

## 9.8 Admin Console

### Objetivo funcional

Concentrar configuração, governança e administração sem poluir o fluxo do consultor.

### Áreas recomendadas

| Área | Objetivo |
|---|---|
| Users & Roles | Gerenciar usuários e papéis |
| Projects & Profiles | Gerenciar projetos, perfis e contexto |
| Environments | Gerenciar ambientes e domínios |
| OTM Connections | Configurar conexão OTM |
| Feature Flags | Habilitar/desabilitar módulos e ferramentas |
| Audit Log | Consultar trilha de ações |
| Catalog Governance | Decisões, mudanças e rollback |

### Regras funcionais

- Admin Console não deve aparecer para USER comum.
- Configuração sensível deve ser mascarada.
- Mudanças críticas devem gerar audit.
- Feature flags controlam superfícies dev-only.
- Catalog changes devem ter request, decision e rollback.

### Critérios de aceite

- Admin consegue gerenciar usuário.
- Admin consegue ativar/desativar módulo.
- Admin consegue ver audit log.
- USER comum não vê Admin Console.
- Mudanças críticas são rastreadas.

---

## 9.9 Developer / DBA Tools

### Objetivo funcional

Disponibilizar ferramentas técnicas apenas para usuários autorizados, sem contaminar a experiência do consultor.

### Ferramentas candidatas

| Ferramenta | Decisão funcional |
|---|---|
| OTM Explorer | Dev/DBA-only ou arquivado |
| Data Dictionary | Dev/DBA/Admin técnico |
| FK Catalog | Usado por validações e consulta técnica |
| Environment Compare | Redesenhar como Environment Readiness ou aposentar |
| Oracle Lab / SQL Lab | Opcional, técnico, não público |
| Setup Assets | Absorver em Load Plan/Cutover |

### Regras funcionais

- Não aparecer no menu público.
- Exigir capability específica.
- Não virar dependência para execução normal do USER.
- Funcionalidades úteis devem ser absorvidas por fluxos principais.

---

# 10. Contratos funcionais transversais

## 10.1 Contrato de módulo funcional

Cada módulo deve declarar:

```text
module_id
name
description
journey
entry_points
capabilities
primary_entities
status_model
artifacts_generated
evidence_generated
events_published
events_consumed
acceptance_criteria
```

Exemplo:

```yaml
module_id: data_factory
name: Data Factory
journey: Template Factory & Data Intake
entry_points:
  - /data-factory/overview
  - /data-factory/template-packs
capabilities:
  - master_data.batch.create
  - master_data.batch.validate
  - master_data.package.export
primary_entities:
  - TemplatePack
  - Batch
  - ValidationIssue
  - LoadPackage
artifacts_generated:
  - OTM_CSV_ZIP
  - MANIFEST_JSON
  - CORRECTION_REPORT
evidence_generated:
  - MASTER_DATA_VALIDATION
  - LOAD_PACKAGE_EXPORT
```

## 10.2 Contrato de status de módulo

Todo módulo público deve conseguir responder:

```json
{
  "module_id": "data_factory",
  "status": "ATTENTION",
  "summary": "2 batches blocked by validation issues.",
  "next_action": {
    "label": "Review validation issues",
    "route": "/data-factory/validation?batch_id=bat_001"
  },
  "blockers": [
    {
      "code": "MISSING_REGION_DETAIL",
      "severity": "ERROR",
      "message": "Region ABR.SE has no region detail rows."
    }
  ]
}
```

## 10.3 Contrato de issue funcional

```json
{
  "issue_id": "iss_001",
  "severity": "ERROR",
  "category": "DEPENDENCY",
  "object_type": "REGION_DETAIL",
  "object_key": "ABR.SE",
  "message": "Region detail references a missing region.",
  "suggested_fix": "Add the missing REGION row or correct the REGION_GID.",
  "blocks_conversion": true
}
```

## 10.4 Contrato de manifesto funcional

```json
{
  "manifest_id": "man_001",
  "source_module": "data_factory",
  "source_entity_type": "batch",
  "source_entity_id": "bat_001",
  "package_type": "OTM_CSV_ZIP",
  "status": "READY",
  "files": [
    {
      "name": "REGION.csv",
      "object_type": "REGION",
      "row_count": 10,
      "load_order": 1
    }
  ],
  "validations": {
    "errors": 0,
    "warnings": 2
  },
  "generated_by": "user_001",
  "generated_at": "2026-05-16T10:00:00-03:00"
}
```

## 10.5 Contrato de evidência funcional

```json
{
  "evidence_id": "evd_001",
  "project_id": "proj_001",
  "source_module": "load_plan",
  "evidence_type": "CUTOVER_READINESS",
  "status": "BLOCKED",
  "summary": "Cutover readiness blocked by 3 unresolved review items.",
  "client_safe": true,
  "artifact_refs": ["art_001"],
  "manifest_ref": "man_001",
  "created_by": "user_001",
  "created_at": "2026-05-16T10:30:00-03:00"
}
```

---

# 11. Regras funcionais de UX

## 11.1 Regra da próxima ação

Toda tela operacional deve ter uma ação primária clara.

Exemplos:

| Contexto | Ação primária |
|---|---|
| Nenhum batch | Baixar template / Fazer upload |
| Batch com erro | Revisar issues |
| Batch válido | Converter |
| Pacote convertido | Exportar ZIP |
| Load Plan com review | Revisar fila |
| Cutover bloqueado | Resolver blockers |
| Evidência pronta | Baixar / abrir detalhe |

## 11.2 Regra de estados vazios

Tela vazia deve explicar:

```text
- o que é essa área;
- por que está vazia;
- qual primeira ação tomar;
- quem pode executar essa ação.
```

## 11.3 Regra de bloqueios

Todo blocker deve ter:

```text
- código;
- severidade;
- mensagem clara;
- impacto;
- próxima ação;
- papel necessário quando aplicável.
```

## 11.4 Regra de termos funcionais

A aplicação deve preferir termos de projeto e operação, não apenas termos técnicos.

Exemplos:

| Evitar | Preferir |
|---|---|
| `asset table import` | Importar pacote de setup |
| `raw payload` | Detalhe técnico protegido |
| `object graph` | Dependências do pacote |
| `CSVUTIL CL` | Arquivo de comando CSVUTIL |
| `validation issue` | Pendência de validação |

---

# 12. Regras funcionais de segurança e evidência

## 12.1 Dados sensíveis

Dados sensíveis incluem:

- credenciais OTM;
- payloads técnicos com endpoints;
- tokens;
- dados de cliente não mascarados;
- arquivos completos quando contêm informação confidencial;
- logs técnicos com segredos.

## 12.2 Política client-safe

Evidence client-safe deve conter:

```text
- status;
- origem;
- resumo;
- contagens;
- blockers;
- referências a artefatos;
- data e responsável;
- próximos passos.
```

Não deve conter:

```text
- senha;
- token;
- endpoint sensível;
- payload bruto;
- arquivo integral não mascarado;
- informações não necessárias ao cliente.
```

## 12.3 Download de artifact

Download deve respeitar:

```text
- papel do usuário;
- capability;
- sensibilidade do artifact;
- projeto ativo;
- origem do artifact;
- audit log.
```

---

# 13. Governança funcional

## 13.1 Mudanças que exigem governança

| Tipo de mudança | Exige governança? |
|---|---|
| Alterar sequência de carga | Sim |
| Alterar mapping de template | Sim |
| Alterar regra de validação bloqueante | Sim |
| Habilitar módulo novo para todos | Sim |
| Alterar feature flag dev-only | Sim |
| Criar batch operacional | Não |
| Gerar correction report | Não |
| Baixar evidence permitida | Não, mas auditar quando sensível |

## 13.2 Modelo de decisão

```text
REQUESTED
UNDER_REVIEW
APPROVED
REJECTED
APPLIED
ROLLED_BACK
```

## 13.3 Campos de uma decisão

```text
decision_id
request_type
requested_by
reviewed_by
status
reason
before_state
after_state
rollback_plan
created_at
applied_at
```

---

# 14. MVP funcional recomendado

## MVP 0 — Fundação funcional mínima

Objetivo: permitir que a aplicação tenha contexto funcional e navegação confiável.

Entregas:

```text
- Login
- Seleção/criação de projeto
- Seleção/criação de perfil
- Ambiente/domínio ativo
- Home com status real básico
- Project Readiness
- Module Registry funcional
- Evidence Hub básico
- Admin Console básico
```

Critério de aceite:

```text
O usuário consegue entrar, escolher projeto, entender readiness e visualizar módulos habilitados conforme permissão.
```

## MVP 1 — Data Factory

Objetivo: primeiro fluxo operacional completo.

Entregas:

```text
- Template Packs
- Upload de batch
- Validação estrutural
- Validação de dependência
- Correction report
- Conversão
- ZIP OTM + MANIFEST.json
- Evidence de load package
```

Critério de aceite:

```text
Um batch de Regions ou Items & Packaging consegue ir de upload até ZIP/evidence, ou gerar blocker claro.
```

## MVP 2 — Rates Studio

Objetivo: validar e exportar tarifas.

Entregas:

```text
- Template de tarifas
- Upload workbook
- Normalização
- Validação
- Issues
- Aprovação
- XML/CSV quando aplicável
- CRP/correction/evidence
```

Critério de aceite:

```text
Um batch de tarifas consegue ser validado, aprovado e exportado, sem simular evidência de sandbox real.
```

## MVP 3 — Load Plan & Cutover

Objetivo: consolidar preparação de carga e readiness.

Entregas:

```text
- Load Packages
- CSVUTIL Builder
- ZIP Analysis
- Review Queue
- Load Sequence
- Cutover Readiness
- Execution Evidence
```

Critério de aceite:

```text
Pacotes gerados por Data Factory/Rates entram no Load Plan, passam por review/readiness e geram evidência de cutover.
```

## MVP 4 — Colaboração e governança avançada

Objetivo: permitir operação por time.

Entregas:

```text
- Workspace compartilhado
- Sync de status/evidências
- Permissões avançadas
- Archive package
- Governança de catálogo
- Feature flags por workspace/projeto
```

Critério de aceite:

```text
Um time pequeno consegue trabalhar no mesmo projeto, compartilhando status, manifestos e evidências client-safe.
```

---

# 15. Roadmap funcional sugerido

## Fase 1 — Produto guiado por projeto

```text
Home
Project Readiness
Project/Profile/Environment
Admin básico
Evidence básico
```

## Fase 2 — Dados Mestres como fluxo completo

```text
Packs prioritários
Batch lifecycle
Validação
Conversão
ZIP/Manifest
Correction Report
Evidence
```

## Fase 3 — Tarifas e CRP

```text
Workbook
Normalização
Validação
Aprovação
Export XML/CSV
CRP Evidence
```

## Fase 4 — Plano de carga e Cutover

```text
CSVUTIL
Load Packages
ZIP Analysis
Review Queue
Load Sequence
Cutover Readiness
Execution Evidence
```

## Fase 5 — Governança e colaboração

```text
Workspace compartilhado
Sync cloud
Audit avançado
Archive package
Change requests
Feature flags
```

## Fase 6 — Dev/DBA Tools controlados

```text
OTM Explorer controlado
Data Dictionary visual
FK Catalog
Environment Readiness
Oracle Lab opcional
```

---

# 16. Critérios funcionais de aceite globais

## 16.1 Aceite geral

```text
- Todo módulo público executa fluxo real.
- Nenhum placeholder aparece para usuário comum.
- Usuário comum não vê ação administrativa.
- Cada fluxo mostra próxima ação clara.
- Todo batch pode ser reaberto.
- Toda validação leva a conversão/export ou motivo de bloqueio.
- Todo export gera artifact e manifest.
- Toda evidência é client-safe.
- Mudanças críticas têm trilha de decisão e rollback.
```

## 16.2 Aceite de Data Factory

```text
- Packs aparecem como capacidades de negócio, não tabelas soltas.
- Dependências são validadas.
- ZIP tem ordem de carga.
- Manifest descreve arquivos e contagens.
- Correction report explica correções.
- Batch possui lifecycle completo.
```

## 16.3 Aceite de Rates Studio

```text
- Workbook é normalizado.
- Issues são claras.
- Aprovação é controlada.
- Export não ocorre se batch estiver bloqueado.
- CRP package é gerado quando aplicável.
- Evidence não afirma execução sandbox sem prova.
```

## 16.4 Aceite de Load Plan & Cutover

```text
- Load Plan consome pacotes de outros módulos.
- Sequência/dependência é visível.
- Review Queue impede itens incertos no cutover.
- Readiness mostra blockers e evidências necessárias.
- Cutover é etapa de Load Plan, não módulo duplicado.
```

## 16.5 Aceite de Evidence Hub

```text
- Evidências listam origem, status e downloads.
- Detalhes não expõem payload bruto sensível.
- Artefatos apontam para módulo fonte.
- Downloads respeitam permissão.
- Archive package consolida evidências do projeto.
```

---

# 17. Riscos funcionais e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Criar telas antes de fechar lifecycle | Alto | Definir estado, ação primária e saída antes da UI |
| Expor ferramentas técnicas para consultor | Alto | Feature flags e capabilities |
| Cutover virar módulo paralelo | Alto | Tratar como etapa do Load Plan |
| Evidence expor dado sensível | Alto | Client-safe summary e artifact policy |
| Packs virarem tabelas soltas | Médio | Organizar por business load packs |
| Mapping virar editor livre cedo demais | Alto | Começar read-only/versionado |
| Sandbox OTM ser assumido sem prova | Alto | Criar status específico para piloto real |
| Usuário não entender blockers | Médio | Mensagem, impacto e próxima ação obrigatórios |
| Módulos não conversarem | Alto | Usar artifacts, manifestos e eventos funcionais |

---

# 18. O que não fazer funcionalmente

```text
- Não criar menu para cada ferramenta técnica.
- Não criar módulo público sem fluxo completo.
- Não criar editor livre de mapping no MVP.
- Não deixar Home com cards mockados.
- Não permitir export sem manifest.
- Não permitir evidence com payload sensível.
- Não duplicar Cutover fora de Load Plan.
- Não transformar Admin Console em tela operacional do consultor.
- Não acoplar lógica de permissão ao frontend.
- Não tratar planilha solta como produto final.
```

---

# 19. Prompt funcional recomendado para Codex

Use este prompt quando quiser iniciar a especificação funcional no desenvolvimento:

```text
Você é um Product Architect e Functional Lead responsável por reconstruir do zero o OTM Project Workbench.

Objetivo:
Criar a fundação funcional da nova aplicação, sem implementar ainda todos os fluxos técnicos completos, garantindo que a aplicação seja orientada por jornadas, módulos, estados, permissões, evidências e próximas ações.

Contexto do produto:
O OTM Project Workbench é uma bancada operacional para projetos Oracle Transportation Management. Ele não substitui o OTM. Ele organiza preparação de dados, validação, geração de arquivos de carga, tarifas, CSVUTIL, Load Plan, Cutover e evidências.

Princípios obrigatórios:
1. Usuário comum não deve ver ações administrativas.
2. Ferramentas técnicas não devem aparecer na navegação principal.
3. Todo módulo público deve ter fluxo real e próxima ação clara.
4. Todo batch deve ter lifecycle.
5. Todo export deve gerar artifact e manifest.
6. Toda evidência deve ser client-safe.
7. Cutover deve ser etapa do Load Plan, não módulo top-level separado.
8. Template & Mapping Studio deve começar read-only/versionado.
9. Mudanças críticas de catálogo/fluxo devem ter governança e rollback.
10. Navegação e status devem vir de contratos do backend.

Entregar inicialmente:
- Modelo funcional de Project, Profile, Environment e Workspace.
- Module Registry funcional com módulos habilitados por capability.
- Home / Project Cockpit com status e próxima ação.
- Project Readiness com checklist e blockers.
- Evidence Hub básico.
- Admin Console básico restrito.
- Contratos funcionais para ModuleStatus, BatchStatus, ValidationIssue, Manifest e Evidence.
- Um módulo funcional demo chamado Data Factory com lifecycle de batch, mas sem toda regra OTM completa ainda.

Critérios de aceite:
- O usuário consegue entrar, selecionar projeto e perfil.
- O usuário vê somente módulos permitidos.
- A Home mostra status real e próxima ação.
- Project Readiness mostra blockers com próxima ação.
- Data Factory demo possui batch lifecycle.
- Evidence Hub lista evidências client-safe.
- Admin Console não aparece para USER comum.
```

---

# 20. Decisão funcional final

A nova aplicação deve ser construída como uma **plataforma funcional modular para projetos OTM**, em que cada módulo é uma jornada operacional com:

```text
- objetivo claro;
- entrada clara;
- lifecycle claro;
- próxima ação;
- validações;
- blockers;
- artefatos;
- manifestos;
- evidências;
- permissões;
- governança.
```

A estrutura funcional recomendada é:

```text
Home / Project Cockpit
Project Readiness
Data Factory
Rates Studio
Load Plan & Cutover
Evidence Hub
Admin Console
Developer / DBA Tools controlado
```

A prioridade não é criar muitas telas. A prioridade é criar **fluxos funcionais sólidos**, com estado, rastreabilidade e saída útil.

A versão ideal do Workbench deve parecer menos com uma coleção de utilitários técnicos e mais com uma **mesa de controle de implementação OTM**, onde o consultor sabe exatamente:

```text
onde está,
o que falta,
o que está bloqueado,
o que pode exportar,
o que já foi evidenciado,
e qual é a próxima ação segura.
```
