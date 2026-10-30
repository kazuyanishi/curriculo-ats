# Validação de evidências de formação acadêmica

`EducationRequirementTruthGate` impede que campos estruturados de formação
sejam aceitos sem suporte no trecho original da vaga.

## Fluxo de validação

`JobCriteriaTruthGate` primeiro verifica se `JobCriterion.evidence` aparece
literalmente em `JobPosting.description`. Em seguida, o gate de formação valida
o conteúdo de `education_requirement`.

Os campos textuais abaixo, quando preenchidos, precisam aparecer literalmente
em `JobCriterion.evidence`:

- `degree_level`;
- `field_of_study`;
- `institution`.

A verificação é sensível a caixa e não normaliza, traduz ou corrige o valor.
Isso preserva a relação direta entre o dado estruturado e o texto de origem.

## Evidência de status

Cada item de `acceptable_statuses` precisa ter um item correspondente em
`status_evidence`. Um item contém:

```text
status: completed | in_progress
evidence: trecho literal da vaga
```

O trecho precisa estar contido em `JobCriterion.evidence`. Assim, a conversão
de uma expressão como `currently pursuing` para `in_progress` mantém a frase
que fundamentou a decisão.

O gate verifica proveniência, não interpretação linguística. A presença do
trecho prova sua origem, mas não usa NLP nem conhecimento externo para decidir
se a classificação semântica está correta.

## Falhas

Uma inconsistência gera `DomainError`. Exemplos:

- curso estruturado que não aparece na evidência;
- instituição inferida ou abreviada;
- status aceito sem evidência associada;
- evidência de status ausente no trecho do critério.

Quando `education_requirement` é `None`, o gate específico não tem campos para
validar. A validação da evidência global do critério continua ativa.
