# Cálculo de score do matching

`MatchingScoreCalculator` calcula duas métricas independentes a partir de
`MatchingResult`: `score` e `coverage`.

## Score

O score considera somente critérios avaliados:

```text
avaliados = matched_count + not_matched_count
score = matched_count / avaliados
```

Critérios `UNSUPPORTED` ficam fora do denominador. Se nenhum critério foi
avaliado, `score` é `None`; isso distingue “nenhuma avaliação possível” de um
score igual a zero.

## Coverage

Coverage informa a proporção de critérios que puderam ser avaliados:

```text
coverage = avaliados / total
```

Se `total == 0`, `coverage` é `None`. Quando existem critérios, mas todos são
`UNSUPPORTED`, coverage é `0.0`.

## Exemplos

| Matched | Not matched | Unsupported | Score | Coverage |
|---:|---:|---:|---:|---:|
| 3 | 1 | 0 | `0.75` | `1.0` |
| 3 | 1 | 5 | `0.75` | `4/9` |
| 0 | 4 | 0 | `0.0` | `1.0` |
| 0 | 0 | 4 | `None` | `0.0` |
| 0 | 0 | 0 | `None` | `None` |

## Propriedades do resultado

`MatchingScore` é imutável. Seus valores são `float | None` e, quando
presentes, precisam estar entre `0.0` e `1.0`.

O cálculo não aplica pesos por importância. `REQUIRED`, `PREFERRED` e
`UNSPECIFIED` permanecem metadados do critério e não alteram a fórmula.
