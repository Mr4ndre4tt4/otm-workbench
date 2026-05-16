# Arquitetura UI/UX e Frontend — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Documento:** Diretriz UI/UX + Frontend para reconstrução do OTM Project Workbench do zero  
**Foco:** modularidade, padronização visual, facilidade para inserir novas telas/módulos, governança de UI e integração com backend modular.

---

## 1. Objetivo do documento

Este documento define a arquitetura de UI/UX e frontend para a nova versão do **OTM Project Workbench**.

O objetivo não é apenas escolher uma biblioteca visual. O objetivo é criar uma fundação onde novas telas, módulos e jornadas possam ser adicionados de forma previsível, rápida e segura, sem recriar layout, CSS, navegação, permissões, componentes ou padrões de interação a cada nova funcionalidade.

A aplicação deve evoluir de um conjunto de telas para um **sistema de produto modular**, composto por:

- **Application Shell** único.
- **Design System** próprio.
- **Component framework interno**.
- **Templates de página reutilizáveis**.
- **Rotas e navegação governadas por contrato**.
- **Módulos frontend com manifesto próprio**.
- **Integração forte com capabilities/permissões vindas do backend**.
- **Padrões consistentes de UX para upload, validação, revisão, exportação e evidência**.

A meta é que criar uma nova tela seja parecido com preencher um contrato e compor blocos já existentes, não começar uma tela do zero.

---

## 2. Contexto funcional e técnico

A spec funcional posiciona o Workbench como uma ferramenta interna para acelerar projetos Oracle Transportation Management, apoiando preparação de dados, validação, geração de arquivos de carga, tarifas, evidências e governança de cutover.

A aplicação não substitui o OTM. Ela organiza o trabalho antes, durante e depois da carga no OTM, reduzindo planilhas soltas, erros de dependência, retrabalho com cliente e ausência de evidência auditável.

As principais entradas funcionais são:

- Project Workflow / Home.
- Project Setup.
- Dados Mestres / Templates & Intake.
- Validation & Rates.
- Plano de Carga / CSVUTIL & Setup Control.
- Cutover como readiness/execution dentro de Plano de Carga.
- Reports & Evidence.
- Project Settings apenas para administradores.

A spec técnica atual mostra uma aplicação local-first baseada em:

- Backend Python/FastAPI.
- Frontend HTML/CSS/JavaScript vanilla.
- Shell estático servido pelo FastAPI.
- Persistência local em SQLite por perfil/projeto.
- Módulos JS por domínio.
- CSS acumulado ao longo das evoluções.
- Navegação, Project Flow e Load Plan caminhando para contratos backend-owned.

Como a nova aplicação será reconstruída do zero, este documento recomenda uma arquitetura frontend moderna, modular e governada por contratos, preservando a diretriz de que o backend continua sendo dono das permissões, navegação efetiva, status de módulos e capabilities.

---

## 3. Decisão principal

A decisão recomendada é:

```text
React + TypeScript + Vite
+ Workbench Design System próprio
+ Tailwind CSS controlado por tokens
+ shadcn/ui como base de distribuição de componentes
+ Radix UI para primitives acessíveis
+ React Router para rotas
+ OpenAPI/generated API client para integração com FastAPI
+ Storybook para documentação e desenvolvimento isolado de componentes
+ Vitest + Testing Library para testes unitários/componentes
+ Playwright para testes E2E e smoke de jornadas
```

A ideia não é “usar shadcn” ou “usar Tailwind” de forma solta. A ideia é criar um **framework interno de UI**, chamado neste documento de **Workbench UI Kit**.

Esse framework interno deve entregar:

- Componentes padronizados.
- Layouts padronizados.
- Tokens de design.
- Padrões de formulário.
- Padrões de status.
- Padrões de tabela.
- Padrões de wizard.
- Padrões de evidência.
- Padrões de tela administrativa.
- Padrões de empty/loading/error states.
- Padrões de permissão e feature flag.

---

## 4. Princípios de UX

### 4.1 O consultor deve sempre saber a próxima ação

Cada tela deve responder:

```text
1. Onde estou?
2. Qual projeto/perfil está ativo?
3. Qual é o status atual?
4. O que está bloqueando?
5. Qual é a próxima ação recomendada?
6. Onde encontro a evidência ou o artefato gerado?
```

Isso é especialmente importante em módulos como Dados Mestres, Rates Studio, Load Plan e Cutover.

### 4.2 Uma ação primária por estado

Cada tela deve ter, no máximo, uma ação primária claramente destacada.

Exemplos:

```text
Estado UPLOADED        -> ação primária: Validar batch
Estado BLOCKED         -> ação primária: Ver issues / gerar correction report
Estado READY_TO_EXPORT -> ação primária: Gerar pacote OTM
Estado EXPORTED        -> ação primária: Ver evidência
Estado DRAFT           -> ação primária: Fazer upload
```

A interface deve evitar telas com muitos botões de mesma importância.

### 4.3 Menos ferramenta técnica, mais jornada guiada

O usuário funcional não deve precisar entender internamente se está usando CSVUTIL, setup asset, object pack, manifest, template mapping ou review queue.

Ele deve enxergar jornadas como:

```text
Preparar dados
Validar
Corrigir
Converter
Gerar pacote
Preparar carga
Validar readiness
Registrar evidência
```

As ferramentas técnicas podem existir, mas devem ficar atrás de Admin/DBA/Dev flags.

### 4.4 Todo módulo público precisa executar fluxo real

Não deve existir módulo público com placeholder visual.

Se uma funcionalidade ainda é técnica, experimental ou incompleta, ela deve ficar:

```text
- fora da navegação principal;
- atrás de feature flag;
- atrás de capability admin/dev;
- ou documentada como experimental em ambiente controlado.
```

### 4.5 Visual limpo, consistente e operacional

O Workbench deve parecer uma bancada de trabalho profissional, não um dashboard decorativo.

Diretrizes:

- Poucas cores, usadas semanticamente.
- Status visual consistente.
- Hierarquia clara de informação.
- Componentes densos o suficiente para trabalho técnico, mas sem poluição visual.
- Linguagem objetiva.
- Artefatos e evidências sempre rastreáveis.
- Tabelas e listas com filtros previsíveis.

---

## 5. Princípios de arquitetura frontend

### 5.1 Backend-owned navigation

O frontend não deve decidir sozinho quais módulos, menus ou ações o usuário pode ver.

O backend deve fornecer um contrato de navegação:

```http
GET /api/v1/platform/navigation
```

Exemplo:

```json
{
  "activeProject": {
    "id": "proj_001",
    "name": "Ajinomoto OTM Rollout",
    "domain": "ABR",
    "environment": "UAT"
  },
  "role": "USER",
  "modules": [
    {
      "id": "master_data",
      "label": "Dados Mestres",
      "route": "/master-data",
      "visible": true,
      "enabled": true,
      "status": "attention",
      "nextAction": "Validate imported batch",
      "requiredCapabilities": ["master_data.batch.view"]
    }
  ]
}
```

O frontend usa esse contrato para renderizar navegação, atalhos e status, mas a autorização real continua no backend.

### 5.2 Rotas locais, menus dinâmicos

As rotas da aplicação devem existir no frontend, mas o menu exibido deve vir do backend.

Isso permite:

- Ter rota pronta para o módulo.
- Ocultar módulo por role, capability ou feature flag.
- Ativar módulo por projeto/perfil.
- Não quebrar build quando um módulo estiver desabilitado.

### 5.3 Módulo frontend tem manifesto

Cada módulo deve possuir um manifesto declarativo.

Exemplo:

```ts
export const masterDataModule: FrontendModuleManifest = {
  id: 'master_data',
  name: 'Dados Mestres',
  basePath: '/master-data',
  icon: 'database',
  requiredCapabilities: ['master_data.batch.view'],
  featureFlag: 'master_data.enabled',
  layout: 'workbench',
  routes: [
    {
      path: '/master-data',
      page: 'MasterDataOverviewPage',
      title: 'Dados Mestres'
    },
    {
      path: '/master-data/batches',
      page: 'MasterDataBatchesPage',
      title: 'Lotes importados'
    },
    {
      path: '/master-data/batches/:batchId',
      page: 'MasterDataBatchDetailPage',
      title: 'Detalhe do lote'
    }
  ],
  statusQuery: {
    endpoint: '/api/v1/modules/master-data/summary',
    refresh: 'on-focus'
  }
};
```

O manifesto não deve substituir o contrato do backend. Ele apenas declara a estrutura frontend disponível.

### 5.4 Módulo não cria CSS global próprio

Um módulo não deve criar uma ilha de CSS.

Permitido:

```text
- usar componentes do Workbench UI Kit;
- usar tokens do tema;
- usar variantes já previstas;
- criar componente local quando necessário;
- propor novo componente ao design system quando reutilizável.
```

Evitar:

```text
- arquivo CSS global por módulo;
- cores hardcoded;
- espaçamentos arbitrários;
- botões customizados;
- tabelas customizadas;
- modais customizados;
- status pill customizada;
- HTML sem componente quando já existe padrão.
```

### 5.5 Página é composição, não invenção

Uma nova tela deve ser construída a partir de templates.

Exemplo:

```tsx
<WorkbenchPage>
  <PageHeader />
  <PageToolbar />
  <StatusSummary />
  <MainContent />
  <EvidencePanel />
</WorkbenchPage>
```

O desenvolvedor não deve precisar decidir margem, espaçamento, tipografia, estado de loading, empty state, header, action bar e breadcrumbs do zero.

### 5.6 Estado dividido por responsabilidade

O frontend deve separar claramente os tipos de estado:

| Tipo de estado | Onde fica | Exemplo |
|---|---|---|
| Estado de servidor | API client + query layer | batches, status, evidências |
| Estado de sessão/app | shell store | usuário, projeto ativo, menu aberto |
| Estado de URL | rota/search params | filtros, aba ativa, página da tabela |
| Estado de formulário | React Hook Form | upload, configuração, edição |
| Estado visual temporário | componente local | modal aberto, dropdown aberto |

Evitar colocar tudo em um estado global.

---

## 6. Stack frontend recomendada

### 6.1 React + TypeScript

React é recomendado porque a aplicação precisa ser baseada em componentes reutilizáveis, composição de layouts e reaproveitamento de padrões de tela.

TypeScript é obrigatório para:

- contratos de API;
- manifestos de módulo;
- props de componentes;
- guards de permissão;
- rotas;
- modelos de status;
- redução de bugs ao incluir novas telas.

### 6.2 Vite

Vite é recomendado como ferramenta de build/dev server pela experiência de desenvolvimento rápida, boa integração com TypeScript e compatibilidade com um frontend SPA moderno.

### 6.3 React Router

React Router é recomendado como roteador principal.

Motivos:

- maturidade no ecossistema React;
- suporte a rotas aninhadas;
- possibilidade de organizar layouts por rota;
- typegen nas versões modernas;
- bom encaixe com app web-first e posterior empacotamento desktop.

A navegação visível não deve ser definida apenas no React Router. Ela deve ser renderizada a partir do contrato do backend.

### 6.4 Tailwind CSS com tokens

Tailwind pode acelerar a criação de layout e reduzir CSS manual, mas precisa ser governado.

A regra é:

```text
Tailwind para compor componentes.
Não Tailwind solto para cada tela inventar uma identidade visual própria.
```

O design system deve usar CSS variables/tokens para cores, espaçamento, bordas, sombras, tipografia e status.

### 6.5 shadcn/ui como base do Workbench UI Kit

shadcn/ui é recomendado como ponto de partida para criar uma biblioteca própria de componentes, porque ele distribui componentes copiáveis/adaptáveis, não uma dependência fechada de componentes prontos.

A estratégia recomendada:

```text
Não usar shadcn como catálogo solto.
Usar shadcn para montar o Workbench UI Kit.
```

Ou seja, os componentes devem entrar no projeto, serem adaptados, versionados e governados como parte do produto.

### 6.6 Radix UI para primitives acessíveis

Radix UI é recomendado para primitives como Dialog, Popover, Tooltip, Select, Tabs e Dropdown, porque ajuda a criar componentes acessíveis e composáveis.

A aplicação deve expor componentes próprios:

```tsx
<WorkbenchDialog />
<WorkbenchSelect />
<WorkbenchTabs />
<WorkbenchTooltip />
```

E não espalhar primitives diretamente por todas as telas.

### 6.7 Storybook

Storybook deve ser usado como laboratório e documentação viva do design system.

Ele deve conter:

- botões;
- inputs;
- cards;
- status pills;
- tabelas;
- page headers;
- issue lists;
- upload panels;
- evidence panels;
- wizards;
- layouts completos;
- estados empty/loading/error.

### 6.8 Vitest + Testing Library

Usar para testes de componentes, hooks e utilitários.

Exemplos:

```text
- PageHeader renderiza ação primária correta.
- StatusPill usa label correto para BLOCKED.
- PermissionGate esconde ação sem capability.
- BatchTimeline renderiza lifecycle na ordem correta.
- UploadDropzone mostra erro de extensão inválida.
```

### 6.9 Playwright

Usar para testes E2E e smoke das jornadas principais:

```text
- login;
- abrir Home;
- navegar para Dados Mestres;
- fazer upload mockado;
- visualizar issues;
- gerar evidence mockada;
- abrir Admin como admin;
- bloquear Admin para usuário comum.
```

### 6.10 API client gerado por OpenAPI

Como o backend FastAPI já produz OpenAPI, o frontend deve consumir um client gerado.

Objetivo:

```text
- evitar endpoints escritos manualmente em cada tela;
- reduzir erro de payload;
- alinhar frontend/backend por contrato;
- facilitar refactor de API;
- facilitar testes.
```

Exemplos de abordagem:

```text
- gerar types a partir do OpenAPI;
- criar camada platform/api;
- criar hooks por módulo;
- evitar fetch direto dentro de componente visual.
```

---

## 7. Arquitetura frontend alvo

```text
frontend/
  package.json
  vite.config.ts
  tsconfig.json
  tailwind.config.ts
  components.json
  index.html

  src/
    main.tsx
    app/
      App.tsx
      router.tsx
      providers/
        AppProviders.tsx
        QueryProvider.tsx
        ThemeProvider.tsx
        AuthProvider.tsx
      routes/
        root.tsx
        protected.tsx
        not-found.tsx

    platform/
      api/
        client.ts
        generated/
        errors.ts
        http.ts
      auth/
        auth.store.ts
        auth.hooks.ts
        PermissionGate.tsx
      navigation/
        navigation.types.ts
        navigation.service.ts
        navigation.store.ts
      permissions/
        capabilities.ts
        useCapability.ts
      shell/
        AppShell.tsx
        Sidebar.tsx
        Topbar.tsx
        Breadcrumbs.tsx
        CommandPalette.tsx
        ProjectContextSwitcher.tsx
      modules/
        module.types.ts
        module.registry.ts
        module-loader.ts
      feature-flags/
        feature-flags.ts
      jobs/
        job.types.ts
        useJobStatus.ts
      evidence/
        evidence.types.ts
        EvidenceDrawer.tsx
        EvidenceLink.tsx
      artifacts/
        artifact.types.ts
        ArtifactDownloadButton.tsx

    design-system/
      tokens/
        tokens.css
        theme.css
        status.css
      primitives/
        button.tsx
        input.tsx
        select.tsx
        dialog.tsx
        dropdown.tsx
        tabs.tsx
        tooltip.tsx
        toast.tsx
      components/
        PageHeader.tsx
        WorkbenchPage.tsx
        ActionBar.tsx
        StatusPill.tsx
        StatusSummary.tsx
        DataTable.tsx
        EmptyState.tsx
        ErrorState.tsx
        LoadingState.tsx
        UploadDropzone.tsx
        IssueList.tsx
        Checklist.tsx
        Timeline.tsx
        Stepper.tsx
        ManifestViewer.tsx
      patterns/
        OverviewPageTemplate.tsx
        ListDetailTemplate.tsx
        UploadValidateExportTemplate.tsx
        AdminTableTemplate.tsx
        EvidencePageTemplate.tsx
        WizardTemplate.tsx
      icons/
        icon-map.tsx

    modules/
      home/
        module.manifest.ts
        routes.tsx
        pages/
        components/
        hooks/
        tests/

      project-readiness/
        module.manifest.ts
        routes.tsx
        pages/
        components/
        hooks/
        tests/

      master-data/
        module.manifest.ts
        routes.tsx
        pages/
          MasterDataOverviewPage.tsx
          MasterDataPacksPage.tsx
          MasterDataBatchesPage.tsx
          MasterDataBatchDetailPage.tsx
          MasterDataValidationPage.tsx
          MasterDataConversionPage.tsx
          CoordinateQualityPage.tsx
        components/
        hooks/
        schemas.ts
        tests/

      rates/
        module.manifest.ts
        routes.tsx
        pages/
        components/
        hooks/
        schemas.ts
        tests/

      load-plan/
        module.manifest.ts
        routes.tsx
        pages/
        components/
        hooks/
        schemas.ts
        tests/

      evidence-hub/
        module.manifest.ts
        routes.tsx
        pages/
        components/
        hooks/
        tests/

      admin/
        module.manifest.ts
        routes.tsx
        pages/
        components/
        hooks/
        tests/

    shared/
      constants/
      formatters/
      validators/
      download/
      clipboard/
      date/
      files/
      otm/
      testing/
```

---

## 8. Application Shell

O **Application Shell** é a estrutura fixa da aplicação.

Ele deve conter:

- Sidebar principal.
- Topbar.
- Projeto/perfil ativo.
- Ambiente/domínio ativo.
- Breadcrumbs.
- Busca/command palette.
- Área de conteúdo.
- Painel de evidência opcional.
- Toasts globais.
- Controle de sessão.
- Feature flags.
- Permission gates.

Estrutura conceitual:

```tsx
<AppProviders>
  <AppShell>
    <Sidebar />
    <ShellMain>
      <Topbar />
      <Breadcrumbs />
      <RouteOutlet />
    </ShellMain>
    <GlobalEvidenceDrawer />
    <Toaster />
  </AppShell>
</AppProviders>
```

### 8.1 Sidebar

A sidebar deve ser renderizada a partir do contrato de navegação do backend.

Itens recomendados:

```text
- Home / Project Cockpit
- Project Readiness
- Data Factory
- Rates Studio
- Load Plan & Cutover
- Evidence Hub
- Admin Console
```

Regras:

- Não mostrar módulo sem capability.
- Não mostrar dev tools para usuário comum.
- Exibir status resumido quando útil.
- Exibir badge de atenção quando houver blockers.

### 8.2 Topbar

A topbar deve mostrar:

```text
- projeto ativo;
- perfil ativo;
- ambiente ativo;
- domínio OTM;
- usuário logado;
- acesso rápido a command palette;
- indicador de modo local/cloud, se aplicável;
- status de sincronização, se aplicável.
```

### 8.3 Command Palette

A aplicação terá muitos módulos e artefatos. Uma command palette ajuda o consultor a navegar rápido.

Exemplos de comandos:

```text
- Ir para Dados Mestres
- Abrir último batch
- Ver evidências do projeto
- Criar pacote de carga
- Baixar template de Location
- Abrir Admin Console
```

A command palette deve respeitar capabilities.

---

## 9. Workbench UI Kit

O **Workbench UI Kit** é a biblioteca interna de componentes.

Ela deve ser tratada como parte do produto, não como detalhe técnico.

### 9.1 Camadas do UI Kit

```text
1. Design tokens
2. Primitives
3. Components
4. Patterns
5. Page templates
6. Domain widgets
```

### 9.2 Design tokens

Tokens recomendados:

```css
:root {
  --wb-bg: ...;
  --wb-surface: ...;
  --wb-surface-muted: ...;
  --wb-border: ...;
  --wb-text: ...;
  --wb-text-muted: ...;

  --wb-primary: ...;
  --wb-primary-foreground: ...;

  --wb-status-success: ...;
  --wb-status-warning: ...;
  --wb-status-danger: ...;
  --wb-status-info: ...;
  --wb-status-neutral: ...;

  --wb-radius-sm: ...;
  --wb-radius-md: ...;
  --wb-radius-lg: ...;

  --wb-space-1: ...;
  --wb-space-2: ...;
  --wb-space-3: ...;
  --wb-space-4: ...;

  --wb-font-sans: ...;
  --wb-font-mono: ...;
}
```

Regras:

- Cores devem ser semânticas.
- Evitar `red-500`, `green-600` ou cores diretas dentro de páginas.
- Status deve usar tokens de status.
- Tamanho e espaçamento devem seguir escala.

### 9.3 Primitives

Primitives são componentes base:

```text
- Button
- IconButton
- Input
- Textarea
- Select
- Checkbox
- RadioGroup
- Switch
- Dialog
- Sheet
- Popover
- Tooltip
- Tabs
- DropdownMenu
- Toast
- Badge
- Card
- Separator
- ScrollArea
```

Esses componentes devem ser os únicos pontos onde Radix/shadcn são usados diretamente.

### 9.4 Components

Components são blocos reutilizáveis do Workbench:

```text
- WorkbenchPage
- PageHeader
- PageSection
- ActionBar
- FilterBar
- StatusPill
- StatusSummary
- DataTable
- EmptyState
- LoadingState
- ErrorState
- UploadDropzone
- IssueList
- Checklist
- Stepper
- Timeline
- EvidencePanel
- EvidenceDrawer
- ArtifactCard
- ManifestViewer
- DownloadButton
- CopyButton
- JsonPreview
- CodeBlock
```

### 9.5 Patterns

Patterns são composições de componentes para casos recorrentes:

```text
- Overview pattern
- List + detail pattern
- Upload + validate + export pattern
- Wizard pattern
- Review queue pattern
- Admin table pattern
- Evidence archive pattern
- Readiness checklist pattern
- Batch lifecycle pattern
```

### 9.6 Domain widgets

Domain widgets são componentes específicos de OTM Workbench, mas ainda reutilizáveis:

```text
- BatchStatusCard
- BatchLifecycleTimeline
- ValidationIssuePanel
- CorrectionReportCard
- LoadPackageCard
- CsvutilCommandPreview
- CutoverReadinessPanel
- OtmObjectBadge
- ProfileEnvironmentBadge
- EvidenceOriginBadge
- ManifestSummaryCard
```

---

## 10. Templates de página

A criação de tela nova deve começar escolhendo um template.

### 10.1 OverviewPageTemplate

Uso:

```text
- Home de módulo
- Dashboard operacional
- Resumo de status
```

Estrutura:

```tsx
<OverviewPageTemplate
  header={...}
  statusSummary={...}
  primaryAction={...}
  cards={...}
  recentActivity={...}
/>
```

### 10.2 ListDetailTemplate

Uso:

```text
- Lista de batches
- Lista de pacotes
- Lista de evidências
- Lista de jobs
```

Estrutura:

```tsx
<ListDetailTemplate
  header={...}
  filters={...}
  table={...}
  detailPanel={...}
/>
```

### 10.3 UploadValidateExportTemplate

Uso:

```text
- Dados Mestres
- Tarifas
- Lat/Lon
- CSV import/export
```

Fluxo padrão:

```text
1. Upload
2. Preview
3. Validate
4. Resolve issues
5. Convert/export
6. Evidence
```

Estrutura:

```tsx
<UploadValidateExportTemplate
  steps={...}
  upload={...}
  validation={...}
  exportPanel={...}
  evidence={...}
/>
```

### 10.4 ReviewQueueTemplate

Uso:

```text
- CSVUTIL review queue
- Setup review
- Cutover decisions
```

Estrutura:

```tsx
<ReviewQueueTemplate
  summary={...}
  filters={...}
  items={...}
  decisionPanel={...}
/>
```

### 10.5 ReadinessTemplate

Uso:

```text
- Project Readiness
- Cutover Readiness
- Environment Readiness
```

Estrutura:

```tsx
<ReadinessTemplate
  checklist={...}
  blockers={...}
  requiredEvidence={...}
  primaryAction={...}
/>
```

### 10.6 EvidencePageTemplate

Uso:

```text
- Evidence Hub
- Evidências por módulo
- Evidência de batch
```

Estrutura:

```tsx
<EvidencePageTemplate
  filters={...}
  evidenceList={...}
  preview={...}
  archiveAction={...}
/>
```

### 10.7 AdminTableTemplate

Uso:

```text
- Usuários
- Perfis
- Ambientes
- Feature flags
- Configurações OTM
```

Estrutura:

```tsx
<AdminTableTemplate
  header={...}
  table={...}
  createAction={...}
  auditPanel={...}
/>
```

---

## 11. Padrões visuais por tipo de tela

### 11.1 Home / Project Cockpit

Objetivo:

```text
Dar visão de projeto ativo, status das jornadas e próximas ações.
```

Componentes obrigatórios:

- ProjectContextCard.
- JourneyStatusGrid.
- NextActionPanel.
- RecentEvidenceList.
- BlockersPanel.

Evitar:

- métricas sem ação;
- gráficos decorativos;
- cards hardcoded;
- atalhos para ferramentas admin/dev para usuário comum.

### 11.2 Project Readiness

Objetivo:

```text
Guiar pré-requisitos mínimos para iniciar o projeto.
```

Componentes obrigatórios:

- ReadinessChecklist.
- EnvironmentStatusCard.
- OtmConnectionStatus.
- BlockingIssuesPanel.
- SetupNextAction.

### 11.3 Data Factory / Dados Mestres

Objetivo:

```text
Preparar dados mestres com packs, batches, validação, conversão, exportação e evidência.
```

Subviews recomendadas:

- Overview.
- Template Packs.
- Batches.
- Batch Detail.
- Validation.
- Conversion & Export.
- Coordinate Quality.
- Evidence.

Componentes obrigatórios:

- TemplatePackCard.
- BatchStatusCard.
- BatchLifecycleTimeline.
- UploadDropzone.
- ValidationIssuePanel.
- CorrectionReportCard.
- LoadPackageCard.
- ManifestViewer.
- EvidenceLink.

### 11.4 Rates Studio

Objetivo:

```text
Transformar planilhas de tarifas em objetos/arquivos OTM validados, aprováveis e rastreáveis.
```

Subviews recomendadas:

- Overview.
- Upload Workbook.
- Validation.
- Approval.
- Export.
- Evidence/CRP.

Componentes obrigatórios:

- RateBatchCard.
- RateIssueList.
- ApprovalPanel.
- ExportTargetCard.
- CrpPackageCard.
- SandboxPilotNotice.

Regra UX importante:

```text
Não sugerir que sandbox OTM foi validado se ainda não houver evidência real.
```

### 11.5 Load Plan & Cutover

Objetivo:

```text
Ser o centro operacional de carga, CSVUTIL, setup review, sequência, cutover readiness e evidência.
```

Subviews recomendadas:

- Overview.
- Load Packages.
- CSVUTIL Builder.
- ZIP Analysis.
- Setup Review.
- Load Sequence.
- Cutover Readiness.
- Execution Evidence.

Componentes obrigatórios:

- LoadPlanSummary.
- CsvutilBuilderPanel.
- ZipAnalysisCard.
- ReviewQueue.
- DependencyGraphPreview.
- ReadinessChecklist.
- CutoverPackageCard.
- ExecutionEvidencePanel.

Regra UX importante:

```text
Cutover não deve parecer módulo paralelo. Ele deve aparecer como etapa natural dentro de Load Plan.
```

### 11.6 Evidence Hub

Objetivo:

```text
Ser o centro canônico de artefatos, evidências e rastreabilidade.
```

Componentes obrigatórios:

- EvidenceFilterBar.
- EvidenceList.
- EvidencePreviewPanel.
- ArtifactDownloadButton.
- EvidenceOriginBadge.
- ArchivePackageAction.

Regra UX importante:

```text
Mostrar resumo client-safe, origem, status e artefato. Não mostrar payload bruto sensível.
```

### 11.7 Admin Console

Objetivo:

```text
Gerenciar usuários, perfis, ambientes, conexões OTM, auditoria e feature flags.
```

Componentes obrigatórios:

- AdminSectionNav.
- AdminTable.
- AuditTimeline.
- FeatureFlagToggle.
- CapabilityMatrix.
- DangerousActionConfirmDialog.

Regra UX importante:

```text
Admin é configuração e governança. Project Readiness é checklist funcional. Não misturar os dois.
```

---

## 12. Padrão de módulo frontend

Cada módulo deve seguir a mesma estrutura.

```text
modules/{module-id}/
  module.manifest.ts
  routes.tsx
  pages/
  components/
  hooks/
  schemas.ts
  constants.ts
  module.types.ts
  tests/
  stories/
```

### 12.1 `module.manifest.ts`

Declara a identidade do módulo.

```ts
import type { FrontendModuleManifest } from '@/platform/modules/module.types';

export const loadPlanModule: FrontendModuleManifest = {
  id: 'load_plan',
  name: 'Load Plan & Cutover',
  basePath: '/load-plan',
  icon: 'workflow',
  requiredCapabilities: ['load_plan.view'],
  featureFlag: 'load_plan.enabled',
  layout: 'workbench',
  order: 40,
  routes: [
    { path: '/load-plan', page: 'LoadPlanOverviewPage' },
    { path: '/load-plan/packages', page: 'LoadPackagesPage' },
    { path: '/load-plan/csvutil', page: 'CsvutilBuilderPage' },
    { path: '/load-plan/cutover-readiness', page: 'CutoverReadinessPage' }
  ]
};
```

### 12.2 `routes.tsx`

Declara rotas do módulo.

```tsx
export const loadPlanRoutes = [
  {
    path: '/load-plan',
    element: <LoadPlanOverviewPage />
  },
  {
    path: '/load-plan/packages',
    element: <LoadPackagesPage />
  },
  {
    path: '/load-plan/csvutil',
    element: <CsvutilBuilderPage />
  },
  {
    path: '/load-plan/cutover-readiness',
    element: <CutoverReadinessPage />
  }
];
```

### 12.3 `hooks/`

Hooks do módulo devem consumir APIs por meio da camada `platform/api`.

Exemplo:

```ts
export function useLoadPlanSummary(projectId: string) {
  return useApiQuery({
    key: ['load-plan', 'summary', projectId],
    endpoint: () => api.loadPlan.getSummary({ projectId })
  });
}
```

### 12.4 `components/`

Componentes locais só devem existir quando forem específicos daquele domínio.

Exemplo aceitável:

```text
CsvutilCommandPreview
RateGeoCostSummary
BatchDependencyWarnings
```

Exemplo que deve ir para o UI Kit:

```text
Button
StatusPill
DataTable
UploadDropzone
PageHeader
EmptyState
Dialog
```

### 12.5 `pages/`

Páginas devem ser composição de templates e componentes.

Exemplo:

```tsx
export function LoadPlanOverviewPage() {
  const summary = useLoadPlanSummary();

  return (
    <OverviewPageTemplate
      header={{
        title: 'Load Plan & Cutover',
        description: 'Prepare, review and govern load execution readiness.'
      }}
      statusSummary={<LoadPlanStatusSummary summary={summary.data} />}
      primaryAction={<GenerateCsvutilAction />}
      sections={[
        <LoadPackagesSection />,
        <CutoverReadinessSection />,
        <ExecutionEvidenceSection />
      ]}
    />
  );
}
```

---

## 13. Como adicionar nova tela sem bagunçar a aplicação

Fluxo recomendado:

```text
1. Confirmar se a tela pertence a um módulo existente ou se é um módulo novo.
2. Escolher um Page Template existente.
3. Definir quais dados vêm do backend.
4. Criar/atualizar capability no backend.
5. Criar/atualizar navigation contract no backend.
6. Criar rota no módulo frontend.
7. Criar página compondo templates existentes.
8. Usar hooks de API; não fazer fetch direto no componente.
9. Usar componentes do Workbench UI Kit.
10. Criar Storybook story se houver componente novo.
11. Criar teste de componente ou smoke E2E.
12. Validar usuário sem permissão.
13. Validar empty/loading/error states.
```

Critério para considerar uma tela pronta:

```text
- Tem rota.
- Tem título e breadcrumb.
- Tem ação primária clara.
- Respeita capability.
- Usa layout padrão.
- Usa componentes do UI Kit.
- Tem loading state.
- Tem empty state.
- Tem error state.
- Tem teste mínimo.
- Não criou CSS global desnecessário.
- Não acessa API fora da camada padrão.
```

---

## 14. Contratos UI com backend

A modularidade frontend depende de contratos claros com backend.

### 14.1 Navigation contract

Responsável por menu, visibilidade e status de módulos.

```json
{
  "modules": [
    {
      "id": "data_factory",
      "label": "Data Factory",
      "route": "/master-data",
      "icon": "database",
      "visible": true,
      "enabled": true,
      "status": "attention",
      "badgeCount": 3,
      "nextAction": "Review validation issues"
    }
  ]
}
```

### 14.2 Module summary contract

Cada módulo deve ter um endpoint de resumo.

```http
GET /api/v1/modules/{moduleId}/summary
```

Exemplo:

```json
{
  "moduleId": "master_data",
  "status": "blocked",
  "nextAction": "Review validation issues",
  "counters": {
    "batches": 12,
    "blocked": 2,
    "readyToExport": 3
  },
  "lastUpdatedAt": "2026-05-16T10:32:00Z"
}
```

### 14.3 Action contract

Ações devem ser descritas pelo backend quando dependerem de estado/permissão.

```json
{
  "actions": [
    {
      "id": "validate_batch",
      "label": "Validar batch",
      "type": "primary",
      "enabled": true,
      "reasonDisabled": null,
      "requiresConfirmation": false,
      "capability": "master_data.batch.validate"
    }
  ]
}
```

### 14.4 Validation issue contract

Issues devem seguir padrão único.

```json
{
  "issues": [
    {
      "id": "iss_001",
      "severity": "error",
      "code": "MISSING_REGION_DETAIL",
      "message": "Region has no region detail rows.",
      "objectType": "REGION",
      "rowNumber": 12,
      "field": "REGION_GID",
      "recommendedAction": "Add at least one REGION_DETAIL row for this region."
    }
  ]
}
```

### 14.5 Evidence contract

Evidências devem ser client-safe.

```json
{
  "evidence": {
    "id": "ev_001",
    "sourceModule": "master_data",
    "sourceEntityType": "batch",
    "sourceEntityId": "bat_001",
    "status": "generated",
    "summary": {
      "generatedFiles": 4,
      "blockedItems": 0,
      "clientSafe": true
    },
    "artifactRef": "art_001"
  }
}
```

---

## 15. Padrões de status

A aplicação precisa de uma linguagem visual única de status.

### 15.1 Status de módulo

```text
not_started
ready
attention
blocked
completed
experimental
admin_only
```

### 15.2 Status de batch

```text
DRAFT
UPLOADED
VALIDATING
VALIDATED
BLOCKED
READY_TO_CONVERT
CONVERTED
READY_TO_EXPORT
EXPORTED
EVIDENCE_GENERATED
ARCHIVED
```

### 15.3 Status de job

```text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

### 15.4 Status de evidência

```text
PENDING
GENERATED
ARCHIVED
FAILED
CLIENT_SAFE
RESTRICTED
```

### 15.5 Exibição visual

Todo status deve ser renderizado por um único componente:

```tsx
<StatusPill status="BLOCKED" />
```

Não criar status manual em cada tela.

---

## 16. Data tables e listas

A aplicação terá muitas tabelas. Por isso, `DataTable` deve ser um componente central.

Funcionalidades mínimas:

```text
- colunas configuráveis;
- loading state;
- empty state;
- error state;
- sort;
- filtros;
- paginação;
- seleção;
- ação por linha;
- bulk actions quando permitido;
- persistência de preferência por usuário/projeto quando necessário;
- export quando aplicável;
- renderização consistente de status/date/id/actions.
```

Exemplo de uso:

```tsx
<DataTable
  columns={batchColumns}
  data={batches}
  getRowId={(row) => row.id}
  emptyState={{
    title: 'Nenhum lote importado',
    description: 'Faça upload de um template para iniciar a validação.'
  }}
  actions={(row) => [
    { label: 'Abrir', href: `/master-data/batches/${row.id}` },
    { label: 'Ver evidência', disabled: !row.evidenceId }
  ]}
/>
```

Regra importante:

```text
Nenhum módulo deve implementar sua própria tabela visual do zero.
```

---

## 17. Upload, validação e exportação

Como vários fluxos usam upload/validação/exportação, deve existir um padrão único.

### 17.1 Upload

Componente:

```tsx
<UploadDropzone />
```

Deve suportar:

```text
- tipos aceitos;
- tamanho máximo;
- drag and drop;
- seleção manual;
- validação visual;
- progresso;
- erro;
- preview básico;
- reprocessamento;
- link para baixar template.
```

### 17.2 Validação

Componente:

```tsx
<ValidationIssuePanel />
```

Deve suportar:

```text
- agrupamento por severidade;
- agrupamento por objeto/tabela;
- busca;
- filtro;
- cópia de códigos técnicos;
- recomendação de correção;
- link para correction report;
- estado bloqueante ou não bloqueante.
```

### 17.3 Exportação

Componente:

```tsx
<ExportPackagePanel />
```

Deve mostrar:

```text
- tipo de pacote;
- arquivos gerados;
- ordem de carga;
- manifest;
- hash/checksum;
- status;
- download;
- evidência gerada.
```

---

## 18. Evidência como padrão transversal de UX

Evidência não deve ser apenas uma tela isolada. Ela deve aparecer como camada transversal.

Qualquer tela que gera artefato deve exibir:

```text
- status da evidência;
- link para visualizar;
- link para download;
- origem;
- data/hora;
- usuário;
- indicação client-safe;
- restrição quando houver dado sensível.
```

Componente padrão:

```tsx
<EvidencePanel
  sourceModule="master_data"
  sourceEntityType="batch"
  sourceEntityId={batchId}
/>
```

---

## 19. Permissões e feature flags na UI

### 19.1 PermissionGate

A UI deve ter um componente padrão de permissão.

```tsx
<PermissionGate capability="admin.users.manage">
  <Button>Gerenciar usuários</Button>
</PermissionGate>
```

Mas isso é apenas UX. O backend continua sendo a autoridade real.

### 19.2 FeatureFlagGate

```tsx
<FeatureFlagGate flag="dev.otm_explorer.enabled">
  <OtmExplorerEntry />
</FeatureFlagGate>
```

### 19.3 Regras

```text
- Nunca mostrar CTA administrativo para usuário comum.
- Nunca depender apenas do frontend para bloquear ação sensível.
- Nunca exibir ferramenta dev-only na navegação pública.
- Sempre mostrar motivo quando ação estiver desabilitada.
```

Exemplo:

```tsx
<Button disabled tooltip="Você precisa aprovar o batch antes de exportar.">
  Exportar pacote
</Button>
```

---

## 20. Acessibilidade

Regras mínimas:

```text
- Componentes interativos devem ser navegáveis por teclado.
- Dialogs, dropdowns e popovers devem seguir padrões acessíveis.
- Estados de erro devem ser legíveis por texto, não só por cor.
- Status deve ter label textual.
- Inputs devem ter label.
- Tabelas devem ter cabeçalhos semânticos.
- Foco deve ser visível.
- Toasts críticos devem ter alternativa persistente na tela.
```

Primitives como Radix ajudam, mas não substituem revisão de UX.

---

## 21. Responsividade e densidade

A aplicação será usada principalmente em desktop/notebook.

Prioridade:

```text
1. Desktop operacional.
2. Notebook com tela média.
3. Tablet apenas leitura/consulta.
4. Mobile não é prioridade para fluxos técnicos.
```

Diretrizes:

- Sidebar colapsável.
- Tabelas com scroll horizontal controlado.
- Painéis de detalhe em drawer/split view.
- Modais apenas para confirmação ou ação curta.
- Evitar layouts que dependem de tela muito larga.

---

## 22. Internacionalização e linguagem

A aplicação pode começar em português, mas deve preparar estrutura para inglês/espanhol.

Recomendação:

```text
- não escrever labels diretamente em componentes complexos;
- criar dicionário por módulo;
- manter códigos técnicos OTM sem tradução;
- traduzir explicação funcional e mensagens ao usuário;
- permitir copiar valor técnico original.
```

Exemplo:

```text
Label funcional: Região sem detalhe configurado
Código técnico: MISSING_REGION_DETAIL
Objeto OTM: REGION_DETAIL
```

---

## 23. Microfrontend: usar ou não?

Não recomendado no início.

Motivo:

```text
O problema atual não é falta de isolamento extremo entre times. O problema é padronização, contratos, UI Kit e modularidade interna.
```

Microfrontend aumentaria:

- complexidade de build;
- versionamento;
- dependências duplicadas;
- governança de design system;
- custo de manutenção.

Recomendação:

```text
Fase 1: Modular SPA única.
Fase 2: Packages internos por módulo, se necessário.
Fase 3: Microfrontend apenas se houver times independentes publicando módulos de forma autônoma.
```

---

## 24. Integração com Tauri/Desktop

A UI deve nascer web-first e poder ser empacotada depois.

Regra:

```text
Módulos funcionais não devem chamar APIs Tauri diretamente.
```

Criar camada adapter:

```text
platform/desktop/
  desktop-api.ts
  file-dialog.ts
  local-process.ts
  shell.ts
```

Assim, o mesmo módulo pode rodar:

```text
- no navegador durante desenvolvimento;
- dentro do Tauri no desktop;
- com backend local FastAPI;
- futuramente com cloud/híbrido.
```

---

## 25. Governança de dependências frontend

Como a aplicação terá foco operacional e poderá lidar com dados sensíveis, dependências precisam ser governadas.

Regras:

```text
- usar pnpm ou npm com lockfile obrigatório;
- evitar instalar biblioteca para resolver problema simples;
- revisar dependências transitivas;
- usar audit/SCA no pipeline;
- pin de versões em releases;
- atualizar dependências em janelas controladas;
- não expor biblioteca externa diretamente em todos os módulos quando puder criar wrapper interno.
```

Exemplo:

```text
Em vez de espalhar imports de uma lib de tabela por todos os módulos,
criar WorkbenchDataTable.
Se a lib mudar, só o wrapper muda.
```

Observação:

```text
Bibliotecas do ecossistema JavaScript podem sofrer incidentes de supply chain.
Por isso, a arquitetura deve minimizar dependências diretas espalhadas e manter lockfile/revisão ativa.
```

---

## 26. Testes e qualidade UI

### 26.1 Tipos de teste

```text
- Typecheck: garante tipos e contratos.
- Unit tests: funções, formatters, guards.
- Component tests: componentes do UI Kit.
- Storybook: documentação e revisão visual.
- E2E/Smoke: jornadas críticas.
- A11y checks: acessibilidade básica.
```

### 26.2 Testes mínimos por nova tela

Toda nova tela deve ter:

```text
- renderização com dados mockados;
- loading state;
- empty state;
- error state;
- permission state, quando aplicável;
- uma navegação smoke no Playwright se for tela pública.
```

### 26.3 Testes mínimos por novo componente do UI Kit

```text
- renderiza com props básicas;
- suporta disabled/loading, quando aplicável;
- respeita variant;
- possui story no Storybook;
- não quebra navegação por teclado quando interativo.
```

---

## 27. CI/CD frontend

Pipeline mínimo:

```bash
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm storybook:build
pnpm e2e:smoke
```

Onde:

```text
lint              -> ESLint
format            -> Prettier
style validation  -> tokens/classes/policy quando possível
typecheck         -> TypeScript
test              -> Vitest
storybook:build   -> garante UI Kit documentado
e2e:smoke         -> Playwright nas rotas públicas principais
```

---

## 28. Regras de CSS

### 28.1 Permitido

```text
- tokens globais;
- theme variables;
- Tailwind utilities dentro de componentes;
- variants controladas;
- CSS module/local apenas quando tecnicamente necessário;
- classes utilitárias padronizadas.
```

### 28.2 Evitar

```text
- CSS global por tela;
- uso excessivo de !important;
- cor hardcoded;
- padding/margin arbitrário fora da escala;
- componentes visualmente iguais implementados de formas diferentes;
- styles inline para layout comum;
- criar novo botão/card/tabela sem passar pelo UI Kit.
```

### 28.3 Política de componente novo

Um componente novo deve responder:

```text
1. Ele é específico de um módulo ou reutilizável?
2. Ele usa tokens?
3. Ele tem variant definida?
4. Ele tem story?
5. Ele respeita acessibilidade?
6. Ele substitui algo já existente?
```

---

## 29. Ícones

Recomendação:

```text
Lucide React ou pacote equivalente de ícones consistentes.
```

Mas a aplicação não deve importar ícones aleatoriamente nas telas.

Criar mapa central:

```ts
export const iconMap = {
  home: HomeIcon,
  database: DatabaseIcon,
  rates: BadgeDollarSignIcon,
  workflow: WorkflowIcon,
  evidence: FileCheckIcon,
  admin: SettingsIcon,
  warning: TriangleAlertIcon,
  success: CheckCircleIcon
};
```

Uso:

```tsx
<WorkbenchIcon name="database" />
```

---

## 30. Fluxo UX padrão de batch

Como batch é um conceito recorrente, a UX deve ser padronizada.

```text
1. Criado / Draft
2. Upload realizado
3. Estrutura validada
4. Dados validados
5. Issues encontradas
6. Correção solicitada
7. Pronto para converter
8. Convertido
9. Pacote gerado
10. Evidência gerada
```

Componente:

```tsx
<BatchLifecycleTimeline status={batch.status} events={batch.events} />
```

Esse padrão deve ser usado em:

- Dados Mestres.
- Rates.
- Lat/Lon.
- Load Packages.
- Correction Reports.

---

## 31. UX de erros

Erros não devem ser exibidos apenas como stack trace ou toast técnico.

Padrão:

```text
Título: O que aconteceu.
Descrição: Por que importa.
Ação recomendada: O que o usuário pode fazer.
Detalhe técnico: expansível/copiável.
```

Exemplo:

```text
Título: Não foi possível gerar o ZIP OTM
Descrição: O batch ainda possui dependências bloqueantes.
Ação recomendada: Revise os erros de validação antes de converter.
Detalhe técnico: MISSING_REGION_DETAIL at row 12
```

Componente:

```tsx
<ErrorState
  title="Não foi possível gerar o ZIP OTM"
  description="O batch ainda possui dependências bloqueantes."
  action={<Button>Revisar issues</Button>}
  technicalDetails="MISSING_REGION_DETAIL at row 12"
/>
```

---

## 32. UX de loading e jobs longos

Fluxos pesados devem ser exibidos como jobs.

Exemplo:

```text
- validando planilha;
- geocodificando localidades;
- gerando pacote ZIP;
- analisando CSVUTIL;
- preparando evidência.
```

Componente:

```tsx
<JobProgressPanel jobId={jobId} />
```

Deve mostrar:

```text
- status;
- progresso;
- etapa atual;
- logs resumidos;
- erro, se houver;
- link para resultado/evidência.
```

---

## 33. Design de informação

O Workbench trabalha com muita informação técnica. A UI precisa organizar isso por prioridade.

Hierarquia recomendada:

```text
Nível 1: Status e próxima ação.
Nível 2: Resumo e blockers.
Nível 3: Tabela/lista de itens.
Nível 4: Detalhe técnico.
Nível 5: Payload/log cru, restrito e expansível.
```

Não iniciar telas mostrando payload bruto, JSON ou detalhes técnicos de baixo nível.

---

## 34. Padrão de documentação de tela

Cada tela pública deve ter uma mini documentação interna.

Exemplo:

```ts
export const pageMeta = {
  id: 'master_data.batch_detail',
  title: 'Detalhe do lote',
  purpose: 'Revisar status, issues, conversão, pacote e evidência de um batch.',
  primaryUser: 'USER',
  primaryAction: 'Depende do status do batch',
  requiredCapabilities: ['master_data.batch.view'],
  backendContracts: [
    'GET /api/v1/modules/master-data/batches/{batchId}',
    'GET /api/v1/modules/master-data/batches/{batchId}/issues'
  ]
};
```

Isso ajuda Codex/devs a criarem novas telas sem perder padrão.

---

## 35. Mapa de módulos e rotas recomendado

```text
/
├── /login
├── /home
├── /project-readiness
├── /master-data
│   ├── /packs
│   ├── /batches
│   ├── /batches/:batchId
│   ├── /validation
│   ├── /conversion
│   ├── /coordinate-quality
│   └── /evidence
├── /rates
│   ├── /batches
│   ├── /batches/:batchId
│   ├── /validation
│   ├── /approval
│   ├── /export
│   └── /evidence
├── /load-plan
│   ├── /packages
│   ├── /csvutil
│   ├── /zip-analysis
│   ├── /setup-review
│   ├── /sequence
│   ├── /cutover-readiness
│   └── /execution-evidence
├── /evidence
│   ├── /reports
│   ├── /artifacts
│   └── /archive
├── /admin
│   ├── /users
│   ├── /profiles
│   ├── /environments
│   ├── /otm-connections
│   ├── /feature-flags
│   └── /audit
└── /dev-tools
    ├── /otm-explorer
    ├── /environment-compare
    └── /dictionary
```

`/dev-tools` deve ser invisível para usuário comum.

---

## 36. Matriz de padrões por módulo

| Módulo | Template principal | Componentes-chave | Observação |
|---|---|---|---|
| Home | OverviewPageTemplate | JourneyStatusGrid, NextActionPanel | Sem dashboard decorativo |
| Project Readiness | ReadinessTemplate | Checklist, BlockersPanel | Checklist funcional, não Admin |
| Master Data | UploadValidateExportTemplate | BatchTimeline, IssueList, ManifestViewer | Primeiro módulo funcional prioritário |
| Rates | UploadValidateExportTemplate | RateIssueList, ApprovalPanel | Não simular evidência de sandbox |
| Load Plan | ReviewQueueTemplate + ReadinessTemplate | CsvutilPreview, ReviewQueue, DependencyPreview | Cutover dentro da jornada |
| Evidence | EvidencePageTemplate | EvidenceList, EvidencePreview | Client-safe sempre |
| Admin | AdminTableTemplate | CapabilityMatrix, AuditTimeline | Restrito por capability |
| Dev Tools | Admin/Dev Template | TechnicalPreview, JsonViewer | Feature flag obrigatória |

---

## 37. Fases de implementação UI/UX

### Fase 0 — Decisões e bootstrap

Entregas:

```text
- criar projeto React + TypeScript + Vite;
- configurar lint, format, typecheck e testes;
- configurar Tailwind;
- configurar aliases;
- configurar estrutura de pastas;
- configurar API client base;
- configurar roteador;
- configurar Storybook;
- configurar Playwright smoke.
```

### Fase 1 — Workbench UI Kit mínimo

Entregas:

```text
- tokens;
- tema claro/escuro, se desejado;
- Button;
- Input;
- Select;
- Dialog;
- Card;
- Badge;
- StatusPill;
- PageHeader;
- WorkbenchPage;
- DataTable básico;
- EmptyState;
- LoadingState;
- ErrorState;
- UploadDropzone;
- IssueList;
- EvidencePanel.
```

### Fase 2 — Application Shell

Entregas:

```text
- Login layout;
- AppShell;
- Sidebar por navigation contract;
- Topbar;
- Breadcrumbs;
- ProjectContextSwitcher;
- PermissionGate;
- FeatureFlagGate;
- Toaster;
- route guards.
```

### Fase 3 — Module framework

Entregas:

```text
- FrontendModuleManifest;
- ModuleRegistry;
- module routes;
- module summary hooks;
- module status cards;
- page templates;
- padrão para nova tela.
```

### Fase 4 — Primeiro módulo real: Master Data

Entregas:

```text
- Overview;
- Template Packs;
- Batches;
- Batch Detail;
- Validation Issues;
- Conversion/Export;
- Evidence integration.
```

### Fase 5 — Rates, Load Plan e Evidence Hub

Entregas:

```text
- Rates Studio seguindo os mesmos templates;
- Load Plan & Cutover seguindo ReviewQueue/Readiness;
- Evidence Hub consumindo evidências de todos os módulos.
```

### Fase 6 — Admin Console e Dev Tools controladas

Entregas:

```text
- Users;
- Profiles;
- Environments;
- OTM Connections;
- Feature Flags;
- Audit;
- Dev Tools atrás de capability/flag.
```

---

## 38. Critérios de aceite da arquitetura UI/UX

A fundação UI/UX será considerada pronta quando:

```text
1. Existe AppShell funcional.
2. Existe Design System inicial documentado no Storybook.
3. Existe ModuleRegistry frontend.
4. A sidebar vem do backend navigation contract.
5. Existe PermissionGate e FeatureFlagGate.
6. Existe pelo menos um módulo demo seguindo manifest + routes + pages.
7. Existe pelo menos um Page Template reutilizável.
8. Existe DataTable padrão.
9. Existe UploadValidateExportTemplate.
10. Existe EvidencePanel padrão.
11. Nenhuma tela pública depende de CSS global próprio.
12. Nova tela pode ser criada copiando um template e preenchendo contratos.
13. TypeScript impede props/contratos inválidos básicos.
14. Playwright consegue navegar por Login -> Home -> módulo demo.
15. Usuário comum não vê Admin/Dev Tools.
```

---

## 39. Decisões que devem ser evitadas

### 39.1 Evitar continuar com vanilla JS para a nova versão

A versão atual usou vanilla JS com módulos estáticos. Isso funcionou para evolução inicial, mas para reconstrução do zero com modularidade, o custo de manter estado, componentes, rotas, permissões e contratos tende a crescer demais.

### 39.2 Evitar CSS acumulado sem design system

CSS acumulado é um dos principais motivos para telas ficarem inconsistentes.

A nova versão deve começar com tokens e componentes.

### 39.3 Evitar microfrontend cedo demais

Microfrontend só resolve um problema que ainda não existe: times independentes publicando módulos isolados.

Para o momento, modular SPA é suficiente e mais simples.

### 39.4 Evitar MUI como identidade final, salvo decisão de velocidade

MUI pode acelerar muito, mas tende a puxar a aplicação para uma identidade visual Material Design. Se a prioridade for uma bancada própria, elegante e customizada, shadcn/Radix/Tailwind com UI Kit interno dá mais controle.

MUI ainda pode ser avaliado se a prioridade absoluta for velocidade de implementação sobre identidade visual.

### 39.5 Evitar tabela, modal e botão customizados por módulo

Esses três elementos são os primeiros a destruir consistência visual.

Devem existir como componentes únicos do UI Kit.

---

## 40. Recomendação final

A nova aplicação deve ser construída com uma arquitetura frontend de **modular SPA**, orientada por contratos do backend e sustentada por um **Workbench UI Kit** próprio.

Stack recomendada:

```text
React + TypeScript + Vite
React Router
Tailwind CSS com design tokens
shadcn/ui como base de componentes próprios
Radix UI para primitives acessíveis
Storybook para documentação e desenvolvimento isolado
Vitest + Testing Library para testes de componentes
Playwright para testes E2E/smoke
OpenAPI generated client para integração com FastAPI
```

Filosofia:

```text
1. O backend decide navegação, permissões e status.
2. O frontend compõe telas a partir de templates.
3. O Design System define identidade e consistência.
4. Módulos declaram manifestos, rotas e capabilities.
5. Telas novas não criam CSS solto.
6. Tabelas, modais, botões, status e evidências são componentes únicos.
7. Cutover, Evidence, Upload, Validation e Export seguem padrões reutilizáveis.
8. Dev tools ficam fora da navegação pública.
9. Storybook documenta componentes e padrões.
10. Playwright protege as jornadas críticas.
```

Essa abordagem permite que a aplicação cresça sem virar uma coleção de telas isoladas.

---

## 41. Prompt sugerido para iniciar no Codex

```text
Você é um arquiteto frontend sênior e deve criar a fundação UI/UX e frontend do OTM Project Workbench do zero.

Objetivo:
Criar uma aplicação frontend modular, padronizada e preparada para receber novos módulos/telas com baixo esforço, usando React + TypeScript + Vite.

Stack obrigatória:
- React
- TypeScript
- Vite
- React Router
- Tailwind CSS com design tokens
- shadcn/ui como base para componentes próprios
- Radix UI para primitives acessíveis
- Storybook
- Vitest
- Playwright

Princípios obrigatórios:
1. Criar um Application Shell único.
2. Criar um Workbench UI Kit interno.
3. Criar Page Templates reutilizáveis.
4. Criar FrontendModuleManifest para módulos.
5. Criar ModuleRegistry frontend.
6. A sidebar deve ser renderizada por navigation contract vindo do backend.
7. O frontend não deve decidir permissões sozinho; deve usar capabilities vindas do backend.
8. Criar PermissionGate e FeatureFlagGate.
9. Nenhum módulo deve criar CSS global próprio.
10. Toda tela deve usar componentes do UI Kit.
11. Criar estados padronizados de loading, empty e error.
12. Criar padrão de StatusPill para módulos, batches, jobs e evidências.
13. Criar EvidencePanel padrão.
14. Criar UploadValidateExportTemplate.
15. Criar um módulo demo chamado master-data com manifest, routes e uma página overview usando o template padrão.

Estrutura esperada:
frontend/
  src/
    app/
    platform/
    design-system/
    modules/
    shared/

Entregáveis:
1. Projeto Vite configurado.
2. Tailwind configurado com tokens.
3. AppShell funcional.
4. UI Kit mínimo: Button, Input, Card, Dialog, StatusPill, PageHeader, WorkbenchPage, DataTable básico, EmptyState, LoadingState, ErrorState, UploadDropzone, EvidencePanel.
5. ModuleRegistry e FrontendModuleManifest.
6. Sidebar consumindo mock de navigation contract.
7. Rotas protegidas por PermissionGate.
8. Storybook com stories dos componentes principais.
9. Vitest com testes básicos de componentes.
10. Playwright com smoke: login mock -> home -> master-data.
11. README explicando como adicionar uma nova tela e um novo módulo.

Critério de aceite:
- Consigo adicionar uma nova tela sem criar novo CSS global.
- Consigo adicionar um novo módulo com manifest + routes + page.
- Consigo ocultar módulo por capability.
- Consigo trocar o menu apenas alterando navigation contract.
- Componentes principais aparecem no Storybook.
- Testes básicos passam.
```

---

## 42. Referências oficiais úteis

- React: https://react.dev/
- Vite: https://vite.dev/
- React Router: https://reactrouter.com/
- Tailwind CSS: https://tailwindcss.com/
- shadcn/ui: https://ui.shadcn.com/
- Radix UI: https://www.radix-ui.com/primitives
- Storybook: https://storybook.js.org/
- Vitest: https://vitest.dev/
- Playwright: https://playwright.dev/
- Lucide: https://lucide.dev/
