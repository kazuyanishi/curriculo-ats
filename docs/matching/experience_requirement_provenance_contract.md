# Proveniência de requisitos de experiência

`ExperienceRequirementTruthGate` valida se os dados estruturados de experiência
têm origem no trecho literal da vaga armazenado em `JobCriterion.evidence`.

## Cargo e empresa

`role` e `company`, quando preenchidos, precisam aparecer literalmente em
`evidence`. A validação não altera caixa, não expande siglas e não aplica
aliases ou tradução.

Essa regra comprova a origem textual do valor. Ela não tenta determinar, por
NLP ou conhecimento externo, se a expressão foi classificada semanticamente no
campo correto.

## Duração mínima

Quando `minimum_duration` está presente, `minimum_duration_evidence` é
obrigatório. Esse campo guarda a menor frase suficiente que originou a duração,
por exemplo:

```text
minimum_duration: 3 years
minimum_duration_evidence: "3 years"
```

O trecho precisa aparecer literalmente em `JobCriterion.evidence`. Uma duração
sem evidência ou com evidência ausente no critério gera `DomainError`.

O gate não recalcula a conversão entre o texto e `value`/`unit`; ele apenas
preserva e verifica a proveniência.

## Limites da validação

O gate não:

- interpreta sinônimos ou paráfrases;
- calcula tempo a partir do currículo;
- soma experiências;
- resolve períodos sobrepostos;
- transforma atividades em cargos;
- converte alternativas em requisitos simultâneos.

`JobCriteriaTruthGate` também exige que o próprio `JobCriterion.evidence`
apareça na descrição completa da vaga. Dessa forma, a cadeia de proveniência é:

```text
campo estruturado -> evidência do critério -> descrição da vaga
```
