# Cobertura do matching de formação acadêmica

Esta matriz resume quais partes de `EducationRequirement` podem ser avaliadas
com os dados atuais de `Candidate.education`.

| Requisito | Suporte | Campo do candidato | Regra |
|---|---|---|---|
| `field_of_study` | Sim | `course` | Igualdade após `strip().casefold()` |
| `institution` | Sim | `institution` | Igualdade após `strip().casefold()` |
| `acceptable_statuses` com curso ou instituição | Sim | `status` | Correspondência pelo valor do enum |
| `degree_level` | Não | — | O candidato não armazena nível da formação |
| Somente status | Não | — | Status não prova o tipo de formação exigido |
| Requisito ausente | Não | — | Não há fallback para texto livre |

## Composição dos campos

Curso, instituição e status são avaliados no mesmo objeto `Education`. Se um
curso coincide em um registro e a instituição em outro, o resultado é
`NOT_MATCHED`.

Um campo não suportado torna o critério inteiro `UNSUPPORTED`. O matcher não
produz resultado parcial nem usa uma coincidência conhecida para ocultar uma
dimensão que não pode avaliar.

## Normalização

A normalização remove espaços nas extremidades e ignora diferenças de caixa:

```python
value.strip().casefold()
```

Ela não remove acentos e não aplica aliases, traduções, stemming, fuzzy
matching, embeddings ou modelos de linguagem. Por exemplo, `Computer Science`
e `computer science` coincidem; `Computer Sciences` e `Information Systems`
não.

## Proveniência

`status_evidence` e `JobCriterion.evidence` comprovam a origem do requisito da
vaga. Esses campos são validados antes do matching, mas não são comparados com
o currículo.

Datas de formação também não participam da decisão, pois
`EducationRequirement` não define restrições temporais.
