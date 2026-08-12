# Experience Requirement Provenance Contract

## 1. Estado atual

O domínio atual representa `ExperienceRequirement` com três dimensões opcionais:
`role`, `company` e `minimum_duration`. `role` e `company` são strings não vazias;
`minimum_duration` é um objeto estruturado com `value` inteiro positivo e `unit`
limitada a `months` ou `years`.

O schema externo preserva essa mesma forma. O prompt atual define a preservação
literal de `evidence` e as categorias, mas ainda não define como preencher
`experience_requirement`. O extractor apenas solicita `JobCriteriaInput` e faz a
conversão para o domínio. O Truth Gate atual cobre a proveniência específica de
educação, não a de Experience.

O contrato desta auditoria trata grounding e correção semântica como garantias
distintas. A presença de um texto na evidência não prova, sozinha, que sua
interpretação estruturada esteja correta.

## 2. Role

**Decisão: A — a contenção literal em `JobCriterion.evidence` é suficiente como
grounding do role.**

Quando `role` for preenchido, seu valor deve existir literalmente em `evidence`,
com a mesma grafia, capitalização e pontuação relevante. Não há autorização para
tradução, aliases, expansão de acrônimos, correção ortográfica ou normalização
semântica. Por exemplo, `Software Eng.` não é `Software Engineer` por este
contrato.

Essa contenção prova apenas a origem textual do valor; não prova que o texto foi
classificado semanticamente como um cargo correto.

## 3. Company

**Decisão: A — a contenção literal em `JobCriterion.evidence` é suficiente como
grounding da company.**

Quando `company` for preenchido, seu valor deve existir literalmente em
`evidence`, preservando a mesma grafia e sem tradução, aliases, correções ou
normalização. O grounding não autoriza inferir uma empresa a partir de contexto
externo nem transformar uma atividade, cliente ou produto em empresa.

Assim como no role, a contenção literal comprova proveniência, mas não substitui
a validação da correção semântica da classificação.

## 4. Minimum duration

**Decisão: SIM — a duração precisa de proveniência específica adicional.**

O modelo atual conserva apenas `value` e `unit`. Depois da conversão, não é
possível saber qual frase literal da evidência originou `3 years`, por exemplo.
Logo, a presença de `3` e `years` como partes isoladas não é uma prova suficiente
da transformação semântica realizada.

A menor forma conceitual futura é adicionar, no requisito, um campo opcional:

```text
minimum_duration_evidence: str | None
```

Esse campo deve conter a menor frase suficiente copiada literalmente da
evidência, sem normalização. O gate futuro poderá verificar sua contenção literal
em `JobCriterion.evidence`; a interpretação dessa frase em `value` e `unit`
continua sendo uma garantia separada.

## 5. Provenance vs semântica

O Truth Gate deve validar proveniência literal: qualquer evidência específica
preenchida deve existir literalmente no texto-fonte do critério, com preservação
de grafia e sem texto inventado.

O Truth Gate não deve virar NLP, tradutor, catálogo aberto de sinônimos,
interpretador de LLM ou parser heurístico. Ele não deve calcular duração, somar
experiências, converter datas, resolver sobreposições ou decidir equivalências
semânticas.

A transformação de texto para `value` + `unit` deve ser responsabilidade da
camada de extração sob um contrato conservador e fechado: só estruturar uma
duração quando a quantidade e a unidade estiverem explicitamente identificadas
e puderem ser vinculadas à frase literal preservada. A validação de
proveniência permanece no gate; a correção da interpretação deve ser tratada no
contrato de extração/schema, sem ampliar o gate.

Não fazem parte deste contrato cálculo por datas do candidato, soma de empregos,
períodos sobrepostos, emprego atual, conversão automática entre anos e meses,
arredondamento ou regras de inclusão de datas.

## 6. Política futura do prompt

O prompt futuro deve usar uma política conservadora:

- Preencher `experience_requirement` somente quando pelo menos uma dimensão for
  explicitamente sustentada pelo mesmo `evidence` literal.
- Preencher `role` e `company` somente com o texto literal correspondente.
- Preencher `minimum_duration` somente quando quantidade e unidade forem
  determinísticas e houver `minimum_duration_evidence` literal correspondente.
- Usar `null` para a dimensão que não puder ser representada fielmente; nunca
  inventar, completar por conhecimento externo ou transformar atividade em cargo.
- Preservar `value` e `evidence` do critério; a estrutura não os substitui.
- Não transformar alternativas (`OR`) em requisitos simultaneamente obrigatórios.

O prompt deve deixar claro que frases vagas, como `several years`, não fornecem
quantidade determinística. Também deve manter a regra de que `strong experience
with customer support` descreve uma competência/atividade e não cria um
`ExperienceRequirement` de role, company ou duração.

## 7. Casos obrigatórios

### Caso 1

Entrada: `3 years of experience as Backend Developer`.

Resultado permitido: `role = "Backend Developer"` e `minimum_duration = 3 years`,
desde que o role e a duração tenham ocorrência literal suficiente em `evidence` e
a duração tenha sua proveniência específica preservada. Não traduzir nem
normalizar `Backend Developer`.

### Caso 2

Entrada: `Experience at Example Corp`.

Resultado permitido: `company = "Example Corp"`, porque o nome está literal na
evidência. `role` e `minimum_duration` permanecem nulos.

### Caso 3

Entrada: `Several years of backend experience`.

Resultado: não criar `minimum_duration`, pois não há quantidade determinística.
Um `role` só pode ser estruturado se existir um cargo explícito literal; a
palavra `backend` isolada não autoriza inventar um cargo. O requisito pode ser
nulo se nenhuma dimensão puder ser representada fielmente.

### Caso 4

Entrada: `Strong experience with customer support`.

Resultado: não criar `ExperienceRequirement`. A frase descreve uma competência
ou atividade e não fornece role, company ou duração sob este contrato.

### Caso 5

Entrada: `Bachelor's degree or 4 years of professional experience`.

Resultado: não criar dois requisitos obrigatórios a partir da alternativa. Como o
modelo atual não representa alternativas, o prompt deve usar `null` para a
estrutura não representável (ou preservar somente uma dimensão explicitamente
segura sem alterar a semântica da alternativa). Não transformar educação e
experiência em exigências simultâneas.

## 8. Classificação

**B — role/company podem ser grounded diretamente; minimum duration precisa de
proveniência adicional.**

O contrato atual é suficiente para preservar e verificar a origem literal de
`role` e `company`. Ele não é suficiente para auditar a origem textual da
conversão estruturada de duração.

## 9. Menor mudança futura

Proveniência adicional: **SIM**.

A primeira mudança futura deve ser somente no contrato de domínio:

- Classe/campo: adicionar `minimum_duration_evidence: str | None` a
  `ExperienceRequirement`.
- Local do domínio: `src/resume_ai/modules/jobs/domain/entities.py`.
- Local correspondente do schema: adicionar o campo opcional equivalente em
  `ExperienceRequirementInput`, em
  `src/resume_ai/modules/jobs/application/schemas.py`.

Essa mudança deve ocorrer em etapas separadas e não deve incluir prompt, extractor
ou Truth Gate no mesmo passo de fundação do domínio. Depois dela, uma sprint
específica poderá definir a extração da proveniência e outra poderá definir o
gate literal correspondente. Nenhum desses componentes é implementado nesta
sprint.

## 10. Próxima sprint

Definir o contrato de domínio e schema para `minimum_duration_evidence`, mantendo
`role` e `company` como strings literais grounded em `JobCriterion.evidence`.
Somente depois devem ser especificadas a política do prompt e a validação do
Truth Gate para duração.

Conclusão:

```text
Classificação: B
Role: grounding literal em JobCriterion.evidence é suficiente
Company: grounding literal em JobCriterion.evidence é suficiente
Minimum duration: proveniência adicional SIM
Proveniência adicional: SIM
Menor mudança futura: adicionar minimum_duration_evidence no domínio e no schema
```
