# Order Release Generator Pipeline Design

## Status

Adicionado ao roadmap. Nao aprovado para implementacao imediata.

## Contexto

Este documento define o desenho backend-first, DB-first e API-first para um modulo futuro de **Order Release Generator Pipeline**. O objetivo e transformar templates governados em payloads XML de Order Release para testes e cargas controladas no OTM, sem reutilizar diretamente o codigo de apoio recebido.

O ZIP recebido deve ser tratado apenas como referencia estrutural:

```text
C:/Users/Enzo Trabalho/Documents/Projetos/OTM General/gerador_or.zip
```

Arquivos observados:

```text
- gerador_or.py
- release_line.py
- Excel/TemplateReleasesTL_20251104.xlsx
- XML/
```

Os dados do arquivo de apoio nao devem ser copiados para o repositorio. Fixtures futuras devem usar exemplos sinteticos como `OTM1`, `PUBLIC`, `DEMO_OR_001`, `LOC_A`, `LOC_B`, `ITEM_A` e `ORDER_RELEASE_TEMPLATE_TL`.

## Fontes Oracle consultadas

Referencias oficiais usadas como base tecnica inicial:

```text
- Transmission Schema:
  https://docs.oracle.com/en/cloud/saas/transportation/26a/otmit/Chunk889275106.html
- Order Creation: XML Integration:
  https://docs.oracle.com/en/cloud/saas/transportation/26b/otmol/planning/order_manager/order_management/order_creation_xml_integration.htm
- Inbound HTTP Integration:
  https://docs.oracle.com/en/cloud/saas/transportation/25c/otmit/inbound-http-integration.html
```

Como regra permanente, detalhes funcionais de XML OTM devem ser confirmados em documentacao oficial Oracle, ambiente lab ou pergunta explicita antes de virar contrato final.

## O que o apoio mostra

O material de apoio representa um gerador procedural que:

```text
1. Le parametros operacionais de uma aba PARAMETERS.
2. Le linhas de Order Release de uma aba ORDER_RELEASE.
3. Agrupa linhas por RELEASE_GID.
4. Monta uma Transmission XML OTM com TransmissionHeader e TransmissionBody.
5. Gera um GLogXMLElement/Release por order release.
6. Gera um ou mais ReleaseLine por release.
7. Preenche referencias como source/destination location, item, packaged item, commodity, THU, incoterm, plan from/to, time window e refnums.
8. Pode salvar XML local ou postar diretamente no endpoint OTM.
```

Padroes uteis a reaproveitar conceitualmente:

```text
- template tabular editavel por usuarios;
- separacao entre parametros e dados transacionais;
- agrupamento por release;
- linhas de item como filhos do release;
- suporte a gerar arquivo XML local;
- suporte futuro a submissao direta ao OTM;
- limite de releases por payload/transmission;
- necessidade de preview/validacao antes de executar.
```

Padroes que nao devem ser copiados:

```text
- montagem de XML por concatenacao de strings;
- credenciais dentro de planilha ou payload;
- POST direto sem job, audit, approval e evidence;
- dependencia fixa de um unico Excel;
- regras hardcoded de refnum, dominio, timezone e release method;
- prints com XML ou dados sensiveis;
- uso de dados reais como fixture;
- logs contendo payload completo sem mascaramento.
```

## Objetivo

Criar um modulo governado para gerar Order Releases OTM a partir de templates configuraveis, com validacao, preview, artifacts, evidence e execucao controlada por Jobs.

O modulo deve suportar dois caminhos:

```text
1. Gerar XML/db.xml local como artifact para import manual/controlado.
2. Submeter XML ao OTM via job, somente quando conexao/perfil/capability permitirem.
```

No MVP0, o caminho local de XML artifact e mais importante que a postagem real.

## Nao objetivos do MVP0

```text
- UI final;
- editor visual completo de template;
- execucao produtiva automatica no OTM;
- armazenamento de credenciais em claro;
- motor generico de todas as transmissions OTM;
- substituicao do Integration Mapping Studio;
- import de qualquer planilha arbitraria sem template conhecido;
- suporte completo a todos os campos de Order Release;
- validacao funcional profunda de planejamento;
- uso direto do codigo Python de apoio;
- copia de valores reais do Excel recebido.
```

## Posicionamento modular

O Order Release Generator Pipeline deve ser tratado como modulo de pipeline especializado, com forte sinergia com:

```text
- Jobs / Processing Engine: parse, validate, preview, generate XML, submit OTM.
- Catalog Core: validar objetos OTM, macro-objeto ORDER_RELEASE, reference options e domain scope.
- Assets Library: armazenar templates, exemplos, XMLs gerados e specs reutilizaveis.
- Evidence Hub: registrar previews, validations, generated XMLs e submission results.
- Project/Profile/Admin: active context, capabilities, environment, domain e conexoes permitidas.
- Integration Mapping Studio: compartilhar ideias de schema tree, transformacoes e documentacao, mas sem virar mapping studio generico.
- Cutover/Load Plan: usar XML gerado em ciclos de teste/cutover quando aplicavel.
```

O modulo nao deve furar Jobs/Catalog/Profile/Admin. Pode entrar antes de Integration Mapping Studio completo se o recorte for restrito a Order Release e gerar XML local.

## Macro-objeto e contratos

Macro-objeto inicial:

```text
ORDER_RELEASE
```

Entidades conceituais:

```text
order_release_templates
order_release_template_fields
order_release_generation_batches
order_release_generation_rows
order_release_generation_issues
order_release_xml_artifacts
order_release_submission_attempts
```

Status sugeridos:

```text
DRAFT
VALIDATING
VALIDATED
PREVIEWED
GENERATED
SUBMITTED
FAILED
CANCELLED
```

Capabilities sugeridas:

```text
order_release_generator:view
order_release_generator:edit_template
order_release_generator:create_batch
order_release_generator:validate
order_release_generator:generate_xml
order_release_generator:submit_otm
order_release_generator:download_artifact
```

## Template configuravel

O template nao deve ser uma planilha fixa. O backend deve persistir definicoes versionadas:

```text
- template_code;
- version;
- scenario;
- field definitions;
- source column aliases;
- target XML path;
- data type;
- required/optional;
- default value;
- transform rule;
- reference policy;
- sample synthetic value;
- validation severity.
```

Campos iniciais inspirados no apoio, usando nomes genericos:

```text
release_gid
source_location_gid
dest_location_gid
early_pickup_date
late_delivery_date
incoterm
plan_from_location_gid
plan_to_location_gid
time_emphasis_gid
ship_with_group
item_gid
item_description
commodity_gid
transport_handling_unit_gid
package_count
declared_value
weight
volume
release_refnums[]
```

Refnums devem ser configuraveis por template, nao hardcoded.

## Validacao

Validacoes MVP0:

```text
- arquivo/template possui colunas reconhecidas;
- release_gid existe em todas as linhas;
- linhas agrupaveis por release_gid;
- location refs obrigatorias presentes;
- item/package_count presentes nas linhas;
- datas parseaveis e convertiveis para formato OTM GLogDate;
- timezone configurado no template/perfil;
- release method definido por template/contexto;
- refnum qualifiers permitidos pelo template;
- nenhum payload/valor sensivel aparece em evidence client-safe;
- tamanho de XML por artifact dentro de limite MVP0;
- quantidade de releases por transmission dentro de limite configuravel.
```

Validacoes futuras com Catalog Core:

```text
- location exists / allowed in domain;
- packaged item / item exists;
- commodity exists;
- THU exists;
- release method exists;
- refnum qualifier exists;
- domain scope PUBLIC + dominio ativo;
- bloqueio de ambientes sem capability de submit.
```

## Geracao XML

O XML deve ser construido por API estruturada de XML, nao por concatenacao livre de strings.

Envelope esperado:

```text
Transmission
  TransmissionHeader
  TransmissionBody
    GLogXMLElement
      Release
        ReleaseGid
        TransactionCode
        ReleaseHeader
        ShipFromLocationRef
        ShipToLocationRef
        TimeWindow
        ReleaseLine[]
        PlanFromLocationGid
        PlanToLocationGid
        ReleaseRefnum[]
```

Regras MVP0:

```text
- TransactionCode inicial: IU, configuravel no template.
- Datas OTM em formato GLogDate, com timezone explicito.
- Releases agrupadas por release_gid.
- ReleaseLine gerada por linha de item.
- XML gerado como artifact interno.
- Manifest e evidence nao devem expor XML completo por padrao.
- Download do XML deve ser auditado.
```

## Submissao OTM

Submissao direta ao OTM deve ser posterior ao gerador local e sempre mediada por Job.

Regras:

```text
- credenciais nunca em planilha;
- conexao vem de ambiente/perfil governado;
- submit exige capability especifica;
- dry-run/preview obrigatorio antes;
- response OTM salvo como artifact/evidence client-safe;
- falhas devem mascarar endpoint, usuario e payload;
- retry automatico fora do MVP0.
```

## APIs MVP0 sugeridas

Base:

```text
/api/v1/modules/order-release-generator
```

Endpoints:

```text
GET  /health
GET  /templates
POST /templates
GET  /templates/{template_id}
POST /batches
GET  /batches
GET  /batches/{batch_id}
POST /batches/{batch_id}/rows
POST /batches/{batch_id}/validate
GET  /batches/{batch_id}/issues
POST /batches/{batch_id}/preview-xml
POST /batches/{batch_id}/generate-xml
GET  /batches/{batch_id}/artifacts
GET  /batches/{batch_id}/evidence
POST /batches/{batch_id}/submit
```

No primeiro recorte, `submit` pode existir apenas como contrato rejeitando ambientes sem conexao/capability.

## Jobs

Job types sugeridos:

```text
ORDER_RELEASE_PARSE_TEMPLATE
ORDER_RELEASE_VALIDATE_BATCH
ORDER_RELEASE_PREVIEW_XML
ORDER_RELEASE_GENERATE_XML
ORDER_RELEASE_SUBMIT_OTM
```

Cada job deve:

```text
- carregar project/profile/environment/domain;
- respeitar limite de input/result do Jobs MVP0;
- produzir artifact/evidence quando gerar XML ou relatorio;
- emitir job events com contexto;
- registrar audit logs client-safe.
```

## Artifacts e Evidence

Artifacts:

```text
- source_template_upload;
- normalized_rows_json;
- validation_report_json;
- xml_preview;
- order_release_transmission_xml;
- otm_submission_response_json.
```

Evidence client-safe:

```text
- batch_id;
- template_id/version;
- release_count;
- line_count;
- issue_summary;
- artifact ids;
- sha256;
- generated_at;
- submitted_at;
- target environment label, sem credenciais;
- status e correlation id quando houver.
```

## Relacao com db.xml

O termo `db.xml` deve ser tratado como modo de empacotamento/export local, nao como formato hardcoded no core.

Contrato sugerido:

```text
artifact_type = order_release_transmission_xml
file_name default = db.xml ou order_release_<batch>.xml conforme modo escolhido
content_type = application/xml
```

## Primeiro recorte recomendado

```text
1. Registrar modulo no backend registry.
2. Criar health endpoint.
3. Criar modelo/API de templates versionados.
4. Criar template seed sintetico para TL Order Release.
5. Criar batches e rows normalizados.
6. Validar colunas obrigatorias e agrupamento por release_gid.
7. Gerar preview XML com fixture sintetica.
8. Persistir XML como artifact.
9. Criar evidence client-safe.
10. Integrar preview/generate com Jobs. [ENTREGUE primeira fatia backend OTM-37]
11. Documentar que submit OTM fica bloqueado no MVP0 sem capability/conexao.
```

## Fora do primeiro recorte

```text
- UI de edicao de template;
- upload real para OTM;
- credenciais/conexoes produtivas;
- suporte completo a todos os campos OTM Release;
- mapeamento visual;
- parser XSD completo;
- rules engine complexo;
- retry/reprocessamento automatico;
- geracao em massa sem limites;
- validacao em OTM real.
```

## Perguntas abertas

```text
1. O primeiro template deve ser TL-only ou deve nascer generico por scenario?
2. O arquivo local padrao deve se chamar db.xml ou usar nome por batch com opcao de exportar como db.xml?
3. A submissao direta ao OTM deve ficar totalmente fora do MVP0 ou exposta como contrato bloqueado?
4. Quais refnums sao padrao do produto e quais devem ser configuracao do template?
5. Quais campos devem ser obrigatorios no primeiro template sintetico?
```

## Recomendacao

Adicionar o modulo ao roadmap sem furar a fila. O melhor momento e depois de Jobs MVP0 e Catalog Core minimo, com uma primeira fatia limitada a template versionado, batch, validacao e XML artifact local. A postagem direta ao OTM deve vir depois de Project/Profile/Admin, capabilities e conexoes governadas.
