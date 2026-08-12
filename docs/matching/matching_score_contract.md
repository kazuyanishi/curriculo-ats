# Matching Score Contract

## 1. Estado atual

O matching atual produz `CriterionMatch` com exatamente um destes statuses:

```text
MATCHED
NOT_MATCHED
UNSUPPORTED
```

`MatchingResult` preserva os matches, expõe as coleções filtradas e fornece:

```text
total
matched_count
not_matched_count
unsupported_count
```

Não existe atualmente implementação de `score`, `percentage`, `coverage`,
`MatchingScore` ou `MatchingScoreCalculator`. Nenhum `.py` foi alterado nesta
auditoria.

## 2. Semântica dos statuses

`MATCHED` significa que o critério foi avaliado e satisfeito.

`NOT_MATCHED` significa que o critério foi avaliado, mas não foi satisfeito.

`UNSUPPORTED` significa que o critério não pôde ser avaliado com segurança
pelo contrato atual. Ele não é uma forma de `NOT_MATCHED` e não deve reduzir o
score como se fosse uma incompatibilidade comprovada.

Essa distinção é essencial para não confundir “não atende” com “não foi
possível avaliar”.

## 3. Denominador

O denominador futuro deve ser:

```text
matched_count + not_matched_count
```

Esse é o número de critérios avaliáveis. `UNSUPPORTED` fica fora do
denominador porque não representa uma decisão positiva ou negativa.

Usar `total` faria critérios não avaliáveis alterarem artificialmente o score
e misturaria `UNSUPPORTED` com `NOT_MATCHED`.

## 4. Fórmula inicial

A fórmula inicial deve ser aceita quando existir pelo menos um critério
avaliável:

```text
score = matched_count / (matched_count + not_matched_count)
```

O resultado deve ser uma proporção entre `0` e `1`. Percentual formatado não é
necessário no contrato inicial; se for exposto futuramente, deve derivar dessa
proporção sem alterar sua semântica.

## 5. Zero avaliável

Quando:

```text
matched_count = 0
not_matched_count = 0
```

o score deve ser:

```text
None
```

Isso cobre tanto o resultado vazio quanto o resultado composto somente por
`UNSUPPORTED`. Não deve ser `0`, pois `0` significa que houve critérios
avaliáveis e nenhum foi satisfeito.

Assim, `0% de compatibilidade` e `score indisponível` permanecem claramente
diferentes.

## 6. Coverage

O futuro resultado deve expor `coverage` separadamente: **SIM**.

Sua fórmula conceitual é:

```text
coverage = (matched_count + not_matched_count) / total
```

Coverage informa qual parte dos critérios pôde ser avaliada; score informa o
desempenho somente dentro da parte avaliável. Se `total == 0`, coverage deve
seguir uma política explícita própria no contrato de implementação futura, sem
ser confundida com o `score=None` de zero avaliável.

Expor os dois valores separadamente evita esconder uma grande quantidade de
`UNSUPPORTED` atrás de um score aparentemente alto.

## 7. Pesos

A primeira versão deve ser **UNWEIGHTED**.

Cada critério avaliável contribui igualmente para o numerador e o denominador.
`REQUIRED`, `PREFERRED` e `UNSPECIFIED` não recebem pesos numéricos nesta
etapa. A importância continua disponível como metadado do critério, mas não
altera a fórmula básica.

Qualquer política de pesos exigiria um contrato separado para prioridades,
critérios ausentes, critérios unsupported e interpretação do resultado. Não
criar esses pesos agora.

## 8. Casos obrigatórios

| Caso | MATCHED | NOT_MATCHED | UNSUPPORTED | Avaliáveis | Score | Coverage |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 1 | 0 | 4 | `3 / 4 = 0,75` | `4 / 4 = 1,00` |
| 2 | 3 | 1 | 5 | 4 | `3 / 4 = 0,75` | `4 / 9 ≈ 0,4444` |
| 3 | 0 | 4 | 0 | 4 | `0 / 4 = 0,00` | `4 / 4 = 1,00` |
| 4 | 0 | 0 | 4 | 0 | `None` | `0 / 4 = 0,00` |
| 5 | 0 | 0 | 0 | 0 | `None` | `None` por política explícita de total zero |

O Caso 3 é `0%` porque houve quatro critérios avaliáveis e nenhum match.
Os Casos 4 e 5 têm score indisponível porque não houve critério avaliável.

## 9. Local arquitetural

Recomenda-se um value object/serviço dedicado de score, separado de
`MatchingResult`.

Esse componente futuro deve receber um `MatchingResult` e calcular score e
coverage conforme este contrato, sem duplicar a classificação dos matches.
Essa separação mantém `MatchingResult` como resultado bruto do matching e
concentra as políticas de denominador, zero avaliável, coverage e futuros
pesos em um único local.

Não implementar o componente nesta sprint e não adicionar propriedades novas a
`MatchingResult` agora.

## 10. Conclusão

```text
Denominador:
matched_count + not_matched_count

Fórmula:
matched_count / (matched_count + not_matched_count), quando houver avaliáveis

Zero avaliável:
score = None

Coverage:
SIM; expor separadamente como avaliáveis / total

Primeira versão:
UNWEIGHTED

Arquitetura recomendada:
serviço/value object dedicado de score, separado de MatchingResult
```

Este documento define somente o contrato futuro. Score, percentage, coverage,
pesos, ranking e novas propriedades não foram implementados.
