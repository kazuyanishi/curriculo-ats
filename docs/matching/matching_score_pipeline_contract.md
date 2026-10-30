# Pipeline de matching e score

`MatchAndScoreCandidateToJob` coordena o matching do candidato e o cálculo das
métricas.

## Entrada e saída

```text
Entrada: Candidate + JobCriteria
Saída: tuple[MatchingResult, MatchingScore]
```

O pipeline executa as etapas nesta ordem:

1. chama `MatchCandidateToJob.execute(candidate, criteria)`;
2. recebe o `MatchingResult`;
3. passa o mesmo resultado para `CalculateMatchingScore.execute()`;
4. retorna o resultado e o score.

A composição não duplica as regras dos matchers nem as fórmulas de score.

## Tratamento dos resultados

O pipeline não altera `MATCHED`, `NOT_MATCHED` ou `UNSUPPORTED`. Critérios não
suportados permanecem no resultado e são considerados normalmente no cálculo
de coverage.

Um `MatchingResult` vazio produz `MatchingScore(score=None, coverage=None)`.

Se o matching falhar, o score não é executado e o erro é propagado. Se o
cálculo do score falhar, o pipeline também propaga o erro sem fabricar um valor
substituto.

## Composição

O serviço fica na camada de aplicação. Ele recebe componentes já construídos:

```text
MatchCandidateToJob
CalculateMatchingScore
```

O bootstrap determinístico expõe essa composição por
`build_match_and_score_candidate_to_job()`. O fluxo completo de análise pode
usar a mesma classe com o matcher híbrido, mantendo o contrato de saída.
