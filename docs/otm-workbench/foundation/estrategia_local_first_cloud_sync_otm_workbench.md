# Estratégia Local-first e Cloud Sync — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Documento:** estratégia de execução local, colaboração em cloud, sincronização, serviços pesados e baixo custo operacional.  
**Objetivo:** permitir uso individual/local e colaboração de um time pequeno sem transformar a aplicação em uma plataforma cara ou difícil de manter.

---

## 1. Decisão central

```text
Local executa; cloud coordena.
```

A aplicação deve rodar localmente para o consultor, mantendo alto desempenho e baixa dependência de internet. A nuvem deve entrar para colaboração, compartilhamento controlado, usuários, manifests, evidências e status de projeto.

---

## 2. Modos de operação

### 2.1 Local-only

Uso por uma pessoa, sem cloud.

```text
- Banco SQLite local.
- Artifacts no filesystem local.
- Jobs locais.
- Sem sync.
- Ideal para desenvolvimento, estudo, POC ou consultor individual.
```

### 2.2 Team Cloud

Uso por time com colaboração.

```text
- Backend local continua executando jobs pesados.
- Cloud mantém workspace, usuários, projetos, permissões, manifests e referências.
- Artifacts podem ser compartilhados seletivamente.
- Evidências client-safe são sincronizadas.
```

### 2.3 Hybrid Controlled

Uso com dados sensíveis.

```text
- Payloads e arquivos brutos ficam locais.
- Cloud recebe apenas metadata, manifest, status e evidence client-safe.
- Downloads compartilhados exigem autorização explícita.
```

---

## 3. O que roda localmente

```text
- Backend FastAPI local.
- SQLite local.
- Processamento de planilhas.
- Validações de dados.
- Validações de dependência/FK.
- Geração de CSV/XML/ZIP.
- Geração de MANIFEST.json.
- Geração de correction reports.
- Jobs de Lat/Lon.
- Cache de Data Dictionary.
- OTM Connector, quando configurado.
- Pelias Docker, quando habilitado.
- Oracle Lab opcional, quando habilitado.
```

---

## 4. O que vai para cloud

```text
- Workspaces.
- Usuários e roles.
- Projetos compartilhados.
- Capabilities efetivas.
- Feature flags por workspace/projeto.
- Project status.
- Module registry publicado.
- Manifests client-safe.
- Evidence client-safe.
- Artifact references.
- Sync state.
- Audit log compartilhado, quando aplicável.
```

---

## 5. O que nunca deve ir para cloud sem decisão explícita

```text
- Senhas OTM.
- Tokens/API keys.
- XMLs completos sensíveis.
- CSVs completos de cliente.
- ZIPs de carga com dados reais.
- Planilhas brutas.
- Payloads OTM completos.
- Logs com credenciais ou headers.
```

Se um artifact sensível precisar ser compartilhado, isso deve exigir:

```text
- Classificação do artifact.
- Capability de download/upload.
- Audit log.
- Confirmação do usuário.
- Registro de hash.
```

---

## 6. Arquitetura lógica

```text
┌──────────────────────────────────────────┐
│ Desktop / Web Shell                       │
│ React + TypeScript / Tauri opcional       │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│ Local Backend Runtime                     │
│ FastAPI + Pydantic + SQLAlchemy           │
├──────────────────────────────────────────┤
│ Platform Core                             │
│ Auth, RBAC, Projects, Modules, Jobs       │
│ Artifacts, Evidence, Events, Audit        │
├──────────────────────────────────────────┤
│ Business Modules                          │
│ Data Factory, Rates, Load Plan, Evidence  │
└────────────────────┬─────────────────────┘
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
┌───────────┐ ┌────────────┐ ┌─────────────┐
│ SQLite    │ │ Filesystem │ │ Docker local│
│ app state │ │ artifacts  │ │ Pelias/etc. │
└───────────┘ └────────────┘ └─────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│ Cloud Collaboration                       │
│ Postgres/Auth/Storage/Realtime opcional   │
└──────────────────────────────────────────┘
```

---

## 7. Estratégia de sincronização

### 7.1 Event log como base

Toda alteração relevante gera um evento local.

```text
domain_events
sync_outbox
sync_inbox
sync_state
```

### 7.2 Outbox

Eventos locais que devem ir para cloud:

```text
- project.created
- profile.updated
- module.status.updated
- manifest.generated
- evidence.generated
- artifact.reference.created
- load_plan.readiness.generated
```

### 7.3 Inbox

Eventos cloud que chegam ao local:

```text
- workspace.user.added
- role.changed
- feature_flag.changed
- project.shared_status.updated
- module.config.updated
```

---

## 8. Modelo de SyncState

```text
id
workspace_id
project_id
profile_id
last_pushed_event_id
last_pulled_event_id
last_sync_at
status: IDLE | SYNCING | FAILED
error_message
```

---

## 9. Estratégia de conflitos

### 9.1 Tipos de conflito

| Tipo | Exemplo | Resolução |
|---|---|---|
| Metadata simples | Nome de projeto alterado por duas pessoas | Last writer wins com audit. |
| Configuração crítica | Feature flag ou capability | Exigir admin decision. |
| Evidence | Duas evidências para mesmo batch | Manter ambas, marcar origem. |
| Artifact | Mesmo arquivo com hash diferente | Criar versões. |
| Batch operacional | Duas pessoas alteram estado | Evitar sync bidirecional do payload; usar ownership. |

### 9.2 Regras

```text
- Nunca sobrescrever artifact sem versionar.
- Nunca descartar evidence.
- Mudança crítica exige Change Request.
- Conflito de permissão é resolvido pela cloud.
- Conflito de arquivo vira nova versão.
```

---

## 10. Compartilhamento de artifacts

### 10.1 Artifact local

```text
artifact_id
file_path local
sha256
sensitivity_level
manifest_id
```

### 10.2 Artifact compartilhado

```text
artifact_id
remote_ref
sha256
sensitivity_level
uploaded_by
uploaded_at
download_policy
```

### 10.3 Políticas

```text
PUBLIC: pode sincronizar metadata e arquivo, se permitido.
INTERNAL: sincroniza metadata; arquivo opcional.
CONFIDENTIAL: sincroniza metadata; arquivo só com aprovação.
SECRET: não sincroniza.
```

---

## 11. Evidências em cloud

Evidências devem ser o principal objeto compartilhado.

```text
- Status do batch.
- Quantidade de issues.
- Link para artifact, se permitido.
- Hash do arquivo.
- Manifest summary.
- Origem do módulo.
- Data/hora e responsável.
```

A evidence deve permitir colaboração sem exigir que todos acessem payload bruto.

---

## 12. Pelias Docker local

Para validação Lat/Lon, o caminho mais seguro é:

```text
- Pelias roda localmente por Docker Compose.
- A aplicação detecta se o serviço está disponível.
- Se indisponível, Lat/Lon Quality entra como degraded/unavailable.
- Jobs que dependem de Pelias ficam bloqueados ou usam fallback.
```

### 12.1 Contrato de saúde

```text
GET /api/v1/platform/services/pelias/health
```

Resposta:

```json
{
  "service": "pelias",
  "status": "AVAILABLE",
  "mode": "LOCAL_DOCKER",
  "base_url": "http://localhost:4000"
}
```

---

## 13. Oracle Lab opcional

Oracle local não deve ser banco principal da aplicação.

Uso recomendado:

```text
- Laboratório técnico.
- Teste de SQL Oracle.
- Simulação controlada.
- Validação de query.
- Dev/DBA tools.
```

Regra:

```text
Oracle Lab é serviço opcional, não dependência obrigatória.
```

---

## 14. Baixo custo operacional

Para até 15 pessoas, evitar arquitetura pesada.

Recomendação:

```text
- Backend local para processamento pesado.
- Cloud com Postgres/Auth/Storage simples.
- Storage compartilhado apenas para artifacts permitidos.
- Sync incremental, não replicação total.
- Sem Kubernetes no início.
- Sem microserviços no início.
- Sem Oracle obrigatório no início.
```

---

## 15. Checklist de implementação do sync

```text
[ ] Criar sync_state.
[ ] Criar sync_outbox.
[ ] Criar sync_inbox.
[ ] Definir eventos sincronizáveis.
[ ] Classificar artifacts por sensitivity_level.
[ ] Definir quais evidências sobem para cloud.
[ ] Criar health de cloud.
[ ] Criar modo offline.
[ ] Criar tela de sync status.
[ ] Criar política de conflito.
[ ] Criar testes de conflito.
[ ] Criar audit de upload/download.
```

---

## 16. Critério de aceite

```text
- A aplicação funciona sem internet.
- Usuário consegue criar projeto local.
- Usuário consegue gerar batch, artifact e evidence local.
- Cloud pode estar desligada sem quebrar fluxo local.
- Evidence client-safe pode sincronizar quando cloud estiver ativa.
- Artifact sensível não sobe automaticamente.
- Conflitos não apagam dados.
- Sync status é claro para o usuário.
```
