# Análise de lacunas do matching

`DeterministicGapAnalyzer` separa os resultados do matching sem reinterpretar
o currículo ou os requisitos da vaga.

## Entrada e saída

A entrada é um `MatchingResult`. A saída é um `GapAnalysisResult` com duas
coleções:

```text
gaps: tuple[CriterionMatch, ...]
unsupported: tuple[CriterionMatch, ...]
```

## Classificação

| Status do critério | Destino |
|---|---|
| `MATCHED` | Não aparece no resultado da análise |
| `NOT_MATCHED` | `gaps` |
| `UNSUPPORTED` | `unsupported` |

Um item não suportado não é tratado como lacuna. `UNSUPPORTED` informa que o
sistema não conseguiu avaliar o critério com segurança; não demonstra ausência
no currículo.

## Identidade e ordem

As coleções preservam os objetos `CriterionMatch` originais e sua ordem
relativa em `MatchingResult.matches`. Não há cópia parcial, reconstrução de
evidência ou ordenação por importância.

Requisitos estruturados de educação e experiência também são preservados por
meio do `JobCriterion` original. A análise não reexecuta o matcher nem altera
`candidate_evidence_paths`.

## Responsabilidades

A regra de separação pertence ao domínio e é exposta pela aplicação através de
`AnalyzeMatchingGaps`. Score, recomendações, cursos, alterações de currículo e
conteúdo gerado por modelo não fazem parte desta etapa.

Um `MatchingResult` vazio produz `gaps=()` e `unsupported=()`.
