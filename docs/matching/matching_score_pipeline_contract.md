# Matching + Score Pipeline Contract

## 1. Estado atual

Hoje existem duas composições independentes:

```text
MatchCandidateToJob
    Candidate + JobCriteria → MatchingResult

CalculateMatchingScore
    MatchingResult → MatchingScore
```

O bootstrap constrói cada serviço separadamente por meio de builders próprios.
Não existe atualmente `MatchAndScoreCandidateToJob`, `ScoredMatchingResult`,
pipeline combinado, DTO ou outro contrato concorrente.

## 2. Pipeline combinado é necessário?

**SIM.**

Um pipeline combinado é útil como uma fronteira de aplicação para garantir que
o score seja calculado sobre exatamente o `MatchingResult` produzido pelo
matching. Isso reduz o risco de consumidores executarem as duas etapas em ordem
incorreta ou calcularem o score sobre um resultado diferente.

O pipeline não deve duplicar a matemática do score nem a lógica de matching;
deve somente orquestrar os dois serviços existentes.

## 3. Camada

**APPLICATION SERVICE.**

A composição coordena dois casos de uso já existentes e recebe uma entrada de
aplicação. Não é uma regra intrínseca de uma entidade nem uma regra matemática
do domínio. A camada de aplicação também preserva a independência dos serviços
`MatchCandidateToJob` e `CalculateMatchingScore`.

Não envolver `JobPosting`, OpenAI, Truth Gate, CLI ou configurações nessa
composição.

## 4. Entrada

A entrada recomendada é exatamente:

```text
Candidate + JobCriteria
```

O pipeline futuro deve receber esses dois objetos e executar o matching. Não
deve receber `JobPosting`, cliente de IA ou configuração, pois esses elementos
pertencem a etapas anteriores e não são necessários para o contrato de
matching+score.

## 5. Saída

A saída mínima recomendada é:

```text
tuple[MatchingResult, MatchingScore]
```

Essa forma preserva os dois value objects existentes sem criar um novo DTO ou
um agregado prematuro. O `MatchingResult` continua disponível para inspeção de
statuses e o `MatchingScore` continua representando score e coverage. A tupla
é suficiente para a primeira composição e mantém explícito que o score foi
calculado a partir daquele resultado.

Não criar `ScoredMatchingResult` nesta etapa de auditoria.

## 6. Ordem de execução

O pipeline futuro deve seguir exatamente esta ordem:

```text
1. executar MatchCandidateToJob com Candidate + JobCriteria
2. receber MatchingResult
3. executar CalculateMatchingScore com esse mesmo MatchingResult
4. retornar MatchingResult + MatchingScore
```

O pipeline não pode recalcular matching nem score. Deve passar por identidade o
`MatchingResult` produzido na primeira etapa para `CalculateMatchingScore`.

Se `MatchCandidateToJob` lançar erro, a etapa de score não deve ser executada e
o erro deve ser propagado. Se o score lançar erro, o pipeline também não deve
substituí-lo ou recalculá-lo.

## 7. Casos mínimos

### Caso 1 — matching normal

```text
Candidate + JobCriteria
→ MatchCandidateToJob
→ MatchingResult
→ CalculateMatchingScore
→ MatchingResult + MatchingScore
```

O resultado mantém os statuses produzidos pelo matching e o score é calculado
somente pelo calculator existente.

### Caso 2 — `MatchingResult` vazio

```text
MatchingResult()
→ MatchingScore(score=None, coverage=None)
```

O pipeline deve retornar o mesmo resultado vazio acompanhado do score vazio,
sem criar um valor substituto.

### Caso 3 — matching contém `UNSUPPORTED`

O pipeline não altera os statuses nem transforma `UNSUPPORTED` em
`NOT_MATCHED`. Ele passa o `MatchingResult` intacto ao
`CalculateMatchingScore`; o calculator decide score e coverage conforme seu
contrato: `UNSUPPORTED` fica fora do denominador do score e entra na cobertura
total.

### Caso 4 — matching lança erro

Se `MatchCandidateToJob` falhar:

```text
matching lança erro
→ score não é executado
→ erro é propagado
```

Não existe score parcial para um matching que não produziu `MatchingResult`.

## 8. Conclusão

```text
Pipeline combinado:
SIM

Camada:
APPLICATION SERVICE

Entrada:
Candidate + JobCriteria

Saída:
tuple[MatchingResult, MatchingScore]

Próxima implementação:
criar um serviço de aplicação fino que execute MatchCandidateToJob,
passe o mesmo MatchingResult a CalculateMatchingScore e retorne a tupla;
sem duplicar matching, score ou criar um novo DTO.
```
