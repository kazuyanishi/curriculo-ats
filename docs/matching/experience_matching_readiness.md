# Cobertura do matching de experiência profissional

| Cenário | Resultado possível | Observação |
|---|---|---|
| Cargo | `MATCHED` ou `NOT_MATCHED` | Igualdade normalizada |
| Empresa | `MATCHED` ou `NOT_MATCHED` | Igualdade normalizada |
| Cargo e empresa no mesmo registro | `MATCHED` ou `NOT_MATCHED` | Todos os campos devem coincidir juntos |
| Duração de uma experiência encerrada | `MATCHED` ou `NOT_MATCHED` | Comparação em meses |
| Experiência em andamento com duração mínima | `UNSUPPORTED` | Não há data de referência implícita |
| Mais de um registro elegível para a duração | `UNSUPPORTED` | Períodos não são somados |
| Requisito não estruturado | `UNSUPPORTED` | Texto livre não é interpretado |
| Atividades ou conquistas | Fora do matching | Não são fallback de cargo ou empresa |

## Normalização de texto

Cargo e empresa passam por `strip().casefold()`. Essa regra trata apenas caixa
e espaços nas extremidades. `Software Eng.` e `Software Engineer`, por exemplo,
continuam diferentes.

## Registro único

Todas as dimensões de um requisito são avaliadas contra o mesmo objeto
`Experience`. Essa regra impede a criação de uma correspondência artificial a
partir de empregos diferentes.

## Limites temporais

O sistema trabalha com `YearMonth`, portanto a unidade mínima disponível é o
mês. Não existem dias parciais no contrato. Períodos de experiências diferentes
não são somados e sobreposições não são deduplicadas.

Se a duração mínima estiver presente, uma única experiência precisa ser
identificada por cargo e/ou empresa. Sem um registro único e encerrado, a
decisão permanece `UNSUPPORTED`.
