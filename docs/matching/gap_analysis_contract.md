# Gap Analysis Contract

## 1. Estado atual

`MatchingResult` contém uma sequência ordenada de `CriterionMatch`. Cada
`CriterionMatch` preserva o `JobCriterion` original e seu `MatchStatus`:
`MATCHED`, `NOT_MATCHED` ou `UNSUPPORTED`.

O resultado também expõe coleções derivadas para cada status. `MatchingScore`
é calculado separadamente e não altera a identidade nem a semântica dos
critérios. Ainda não existe Gap Analysis implementado.

## 2. Entrada

A menor entrada suficiente é somente:

```text
MatchingResult
```

Não é necessário receber `Candidate`, `JobCriteria` ou `MatchingScore`.
`MatchingResult` já contém o critério original, o status determinístico e a
ordem produzida pelo matching. O score é uma métrica agregada, não uma fonte
para decidir se um critério individual é gap.

## 3. Definição de gap

A política determinística é:

```text
MATCHED      -> não é gap
NOT_MATCHED  -> gap comprovado
UNSUPPORTED  -> não avaliável; não é gap
```

`NOT_MATCHED` significa que o matcher avaliou o critério e não encontrou
correspondência. `UNSUPPORTED` significa que não houve avaliação suficiente;
transformá-lo em gap afirmaria que o candidato não possui algo que o sistema
não conseguiu verificar.

Gap Analysis não deve reinterpretar `value`, `evidence`, importância ou
qualquer requisito estruturado. Deve apenas classificar o status que o
matching já produziu.

## 4. Tratamento de unsupported

A decisão é a opção **B — preservar uma coleção separada de itens não
avaliáveis**.

O futuro resultado deve manter, conceitualmente:

```text
GapAnalysisResult(
    gaps=(...),
    unsupported=(...),
)
```

`unsupported` não deve ser misturado com `gaps` nem descartado silenciosamente.
Essa separação torna explícito que o usuário não pode interpretar um item
`UNSUPPORTED` como ausência de habilidade.

## 5. Identidade e ordem

Cada item deve preservar a **referência ao `CriterionMatch` original**. Isso
mantém, por meio do mesmo objeto, o `JobCriterion` original com category,
value, evidence, importance, education requirement e experience requirement.

Não criar cópia, DTO duplicado ou reconstrução parcial do critério. Uma
estrutura que preserve `CriterionMatch` também preserva o status já validado.

Gaps e itens `unsupported` devem manter a ordem relativa em que aparecem em
`MatchingResult.matches`. Não haverá reordenação por importance, category,
score ou qualquer ranking. `REQUIRED` e `PREFERRED` não alteram a ordem nesta
etapa.

## 6. Casos obrigatórios

### Caso 1 — um MATCHED

Resultado: `gaps=()` e `unsupported=()`. O critério não é gap.

### Caso 2 — um NOT_MATCHED

Resultado: um gap contendo o `CriterionMatch` original. Nenhuma informação é
copiada ou inferida.

### Caso 3 — um UNSUPPORTED

Resultado: `gaps=()` e uma entrada em `unsupported`. O item não é convertido
em gap.

### Caso 4 — MATCHED, NOT_MATCHED, UNSUPPORTED

Resultado: um gap e um item não avaliável. O gap é o segundo `CriterionMatch`
original e `unsupported` contém o terceiro. Cada coleção preserva a ordem
relativa de origem; não há ranking entre elas.

### Caso 5 — MatchingResult vazio

Resultado: `gaps=()` e `unsupported=()`. Nenhum critério é inventado.

### Caso 6 — NOT_MATCHED com importance REQUIRED

Continua sendo somente um gap. `REQUIRED` não cria ranking, prioridade ou
recomendação automática nesta camada.

### Caso 7 — NOT_MATCHED com education_requirement estruturado

O `CriterionMatch` original é suficiente e deve ser preservado por referência.
O Gap Analysis não precisa copiar nem interpretar o requisito de educação.

### Caso 8 — NOT_MATCHED com experience_requirement estruturado

Aplica-se a mesma regra: preservar o `CriterionMatch` original por referência.
O Gap Analysis não reavalia role, company, duração ou provenance.

## 7. Contrato mínimo futuro

O menor modelo futuro é um `GapAnalysisResult` contendo:

```text
gaps: tuple[CriterionMatch, ...]
unsupported: tuple[CriterionMatch, ...]
```

Não é necessária uma nova entidade `Gap`: o `CriterionMatch` já preserva a
identidade do `JobCriterion` e o status que fundamenta a classificação. Usar
`JobCriterion` diretamente perderia o vínculo explícito com o status do
matching; criar um DTO ou entidade adicional duplicaria informação sem ganho
contratual.

O resultado vazio deve ser válido. As duas coleções devem ser imutáveis na
forma contratada e conter referências aos objetos originais.

Recomendações, cursos, frases de currículo, senioridade inferida, skills
inferidas, sugestões de alteração ou explicações por LLM não pertencem a este
contrato. São etapas posteriores e separadas, se forem necessárias.

## 8. Camada arquitetural

A regra determinística de separação por `MatchStatus` pertence ao **DOMAIN**.
Ela não depende de Candidate, JobCriteria, AI ou score.

Uma futura orquestração/use case pertence à camada **APPLICATION** e deve
apenas receber `MatchingResult`, chamar o serviço de domínio e expor o
`GapAnalysisResult`. Não deve reimplementar a classificação nem criar
recomendações.

## 9. Classificação

**B — os dados atuais são suficientes, mas é necessário um pequeno contrato de
domínio de Gap Analysis.**

`MatchingResult` já fornece tudo para decidir deterministicamente quais itens
são gaps e quais não foram avaliáveis. Porém, o sistema ainda precisa de um
resultado explícito com duas coleções, preservação de referência e ordem
contratada. Isso evita que consumidores confundam `UNSUPPORTED` com gap.

Conclusão:

```text
Classificação: B
Entrada: MatchingResult
MATCHED: excluído de gaps e unsupported
NOT_MATCHED: gap comprovado
UNSUPPORTED: preservado em coleção separada; não é gap
Ordem: preservar a ordem de MatchingResult.matches, sem ranking
Modelo mínimo: GapAnalysisResult(gaps: tuple[CriterionMatch, ...], unsupported: tuple[CriterionMatch, ...])
Camada: regra no DOMAIN; orquestração futura na APPLICATION
```

## 10. Próxima sprint

Criar somente o contrato de domínio mínimo `GapAnalysisResult` e a regra
determinística que distribui cada `CriterionMatch` entre `gaps` e
`unsupported`, preservando referência e ordem. Não adicionar recomendações,
ranking, score, Candidate, JobCriteria, AI ou LLM.
