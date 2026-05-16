# Segurança, Permissões e Governança — OTM Project Workbench

**Data de referência:** 2026-05-16  
**Documento:** diretriz de segurança, RBAC, capabilities, dados sensíveis, auditoria e governança.  
**Objetivo:** proteger a aplicação, evitar exposição de dados sensíveis e garantir que mudanças críticas sejam rastreáveis.

---

## 1. Princípios

```text
1. Usuário comum não vê ação administrativa.
2. Ferramentas técnicas não aparecem na navegação principal.
3. Dados sensíveis não aparecem crus em evidências.
4. Toda ação crítica gera audit log.
5. Toda mudança de catálogo/fluxo passa por governança.
6. Todo segredo é criptografado ou armazenado em cofre/local seguro.
7. Permissão é validada no backend, não apenas na UI.
8. Dev-only depende de capability + feature flag.
9. Evidência deve ser client-safe por padrão.
10. Produção exige confirmação explícita antes de exportar/executar ação sensível.
```

---

## 2. Papéis

| Papel | Descrição | Uso esperado |
|---|---|---|
| `USER` | Consultor/operador | Executa intake, validação, revisão, exportação e consulta evidências autorizadas. |
| `ADMIN` | Administrador funcional | Gerencia projeto, perfil, usuários, flags e configurações não técnicas. |
| `DBA` | Perfil técnico | Acessa ferramentas técnicas, Data Dictionary, OTM Explorer controlado e diagnósticos. |
| `MASTER` | Super administrador | Pode administrar tudo, aprovar mudanças críticas e habilitar dev-only. |

---

## 3. Capabilities

Permissões devem ser granulares e orientadas por capability.

Formato:

```text
{module}.{resource}.{action}
```

Exemplos:

```text
master_data.batch.read
master_data.batch.create
master_data.batch.validate
master_data.package.export
rates.batch.approve
load_plan.csvutil.generate
load_plan.cutover.export
evidence.artifact.download
admin.user.manage
otm.connection.configure
dev.otm_explorer.access
security.secret.view
```

---

## 4. Matriz inicial de permissões

| Capability | USER | ADMIN | DBA | MASTER |
|---|---:|---:|---:|---:|
| `platform.navigation.read` | Sim | Sim | Sim | Sim |
| `project.readiness.read` | Sim | Sim | Sim | Sim |
| `master_data.batch.read` | Sim | Sim | Sim | Sim |
| `master_data.batch.create` | Sim | Sim | Sim | Sim |
| `master_data.batch.validate` | Sim | Sim | Sim | Sim |
| `master_data.package.export` | Sim | Sim | Sim | Sim |
| `rates.batch.read` | Sim | Sim | Sim | Sim |
| `rates.batch.create` | Sim | Sim | Sim | Sim |
| `rates.batch.approve` | Não/Config | Sim | Sim | Sim |
| `load_plan.csvutil.generate` | Sim | Sim | Sim | Sim |
| `load_plan.review.decide` | Config | Sim | Sim | Sim |
| `load_plan.cutover.export` | Não/Config | Sim | Sim | Sim |
| `evidence.record.read` | Sim | Sim | Sim | Sim |
| `evidence.artifact.download` | Sim | Sim | Sim | Sim |
| `evidence.sensitive.view` | Não | Parcial | Sim | Sim |
| `admin.user.manage` | Não | Sim | Não/Config | Sim |
| `admin.feature_flag.manage` | Não | Sim | Sim | Sim |
| `otm.connection.configure` | Não | Sim | Sim | Sim |
| `dev.otm_explorer.access` | Não | Não | Sim | Sim |
| `dev.raw_payload.view` | Não | Não | Sim | Sim |

Observação: permissões marcadas como `Config` devem ser controladas por workspace/projeto.

---

## 5. Autenticação e sessão

### 5.1 Local-first

No modo local, a aplicação deve suportar:

```text
- Primeiro usuário bootstrap.
- Login local.
- Hash de senha com salt.
- Sessão por cookie seguro.
- Expiração de sessão.
- Rate limit em login.
- Logout e revogação de sessão.
```

### 5.2 Cloud/híbrido

No modo colaborativo, considerar:

```text
- Auth centralizado.
- Convite de usuários por workspace.
- Roles por projeto.
- Sessão cloud separada da sessão local.
- Refresh token protegido.
- Revogação centralizada.
```

---

## 6. Classificação de dados

| Nível | Descrição | Exemplos | Regra |
|---|---|---|---|
| `PUBLIC` | Pode ser exibido sem risco | Nome de módulo, status genérico | Pode aparecer em UI/evidence. |
| `INTERNAL` | Informação interna do projeto | Nome de projeto, resumo de batch | Pode aparecer para usuários autorizados. |
| `CONFIDENTIAL` | Dados de cliente ou operação | Planilhas, GIDs, endereços, tarifas | Mascarar em evidence e controlar download. |
| `SECRET` | Credenciais e tokens | Senha OTM, API keys | Nunca exibir; criptografar. |

---

## 7. Dados sensíveis por domínio

### 7.1 OTM Connection

Sensível:

```text
- URL interna
- usuário
- senha
- token
- headers de autenticação
```

Regra:

```text
- Criptografar localmente.
- Nunca retornar senha/token pela API.
- Retornar apenas metadata mascarada.
```

### 7.2 Artifacts

Sensível:

```text
- CSVs de dados mestres
- XMLs de tarifas
- ZIPs de carga
- Planilhas de cliente
- Correction reports com dados reais
```

Regra:

```text
- Classificar por sensitivity_level.
- Download exige capability.
- Evidence deve apontar para referência, não despejar payload.
```

### 7.3 Evidências

Regra:

```text
- Client-safe por padrão.
- Payload bruto técnico não deve aparecer.
- Exibir resumo, status, origem, hash, artifact_id, manifest_id e issues agregadas.
```

---

## 8. Criptografia e armazenamento de segredos

### 8.1 Local

Usar criptografia local para segredos.

Itens criptografados:

```text
- Senhas OTM
- Tokens/API keys
- Credenciais de cloud sync
- Headers sensíveis
```

### 8.2 Regras

```text
1. Segredo nunca vai para log.
2. Segredo nunca vai para evidence.
3. Segredo nunca é exportado em ZIP.
4. Segredo nunca retorna em endpoint de detalhe.
5. Segredo só pode ser sobrescrito, não visualizado em claro.
```

---

## 9. Auditoria

Toda ação crítica deve registrar audit log.

### 9.1 Ações auditáveis

```text
- Login/logout
- Criação/alteração de usuário
- Alteração de role/capability
- Criação/alteração de projeto/perfil/ambiente
- Configuração OTM
- Habilitação de feature flag
- Aprovação/rejeição de tarifas
- Exportação de artifact
- Download de artifact sensível
- Decisão de review queue
- Aprovação de change request
- Rollback de change request
- Geração de readiness/cutover package
```

### 9.2 Modelo de audit log

```json
{
  "id": "aud_001",
  "actor_user_id": "usr_001",
  "action": "rates.batch.approve",
  "resource_type": "rate_batch",
  "resource_id": "rbat_001",
  "project_id": "prj_001",
  "before": {"approval_status": "PENDING"},
  "after": {"approval_status": "APPROVED"},
  "metadata": {
    "ip": "127.0.0.1",
    "client": "desktop"
  },
  "created_at": "2026-05-16T12:00:00Z"
}
```

---

## 10. Governança de mudanças

Mudanças críticas não devem ser editor livre.

### 10.1 O que exige Change Request

```text
- Alterar Project Flow padrão.
- Alterar catálogo de Load Plan.
- Alterar taxonomia de macro-objetos.
- Alterar template pack ativo.
- Alterar mapeamento de Template & Mapping Studio após publicado.
- Alterar permissões globais.
- Habilitar dev-only tools em workspace compartilhado.
- Alterar regra de mascaramento/evidence.
```

### 10.2 Lifecycle

```text
DRAFT
SUBMITTED
APPROVED
REJECTED
APPLIED
ROLLED_BACK
```

### 10.3 Campos mínimos

```text
id
source_module
change_type
requested_by
status
request_json
decision_json
rollback_json
created_at
updated_at
```

---

## 11. Feature flags

Feature flags controlam superfícies opcionais, experimentais ou técnicas.

Exemplos:

```text
master_data.enabled
master_data.latlon_quality.enabled
rates.csv_export.enabled
load_plan.cutover_readiness.enabled
evidence.archive_package.enabled
dev.otm_explorer.enabled
dev.environment_compare.enabled
oracle_lab.enabled
cloud_sync.enabled
```

Regras:

```text
- Flag não substitui capability.
- Capability não substitui flag.
- Dev-only exige ambos.
- Flag deve ter escopo: global, workspace, project, profile ou user.
- Alteração de flag crítica gera audit log.
```

---

## 12. Guardrails de produção

Ambiente marcado como produção deve ter proteções adicionais.

```text
- Confirmar antes de exportar pacote.
- Exibir banner de ambiente PROD.
- Exigir capability elevada para ação destrutiva.
- Impedir execução automática com item incerto.
- Registrar audit log com nível alto.
- Gerar evidence obrigatória.
```

---

## 13. Checklist de segurança por módulo

```text
[ ] Todas as rotas validam usuário autenticado.
[ ] Rotas sensíveis validam capability.
[ ] Dados sensíveis são mascarados na resposta.
[ ] Segredos não aparecem em logs.
[ ] Evidence é client-safe.
[ ] Artifact tem sensitivity_level.
[ ] Download exige capability.
[ ] Ações críticas geram audit log.
[ ] Dev-only está atrás de feature flag.
[ ] Mudança crítica usa Change Request.
[ ] Testes cobrem permissão e mascaramento.
```

---

## 14. Anti-patterns

```text
- Verificar role apenas no frontend.
- Exibir botão escondido por CSS, mas endpoint aberto.
- Retornar senha OTM mascarada com valor real escondido.
- Gravar planilha inteira dentro de evidence.
- Permitir download de artifact sem audit.
- Criar endpoint admin sem require_admin/capability.
- Misturar Project Setup funcional com Project Settings administrativo.
- Exibir OTM Explorer para USER.
- Criar editor livre para catálogo sem governança.
```
