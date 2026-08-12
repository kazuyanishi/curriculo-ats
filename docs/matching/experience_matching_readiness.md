# Experience Matching Readiness

## 1. Estado atual

`Candidate` possui `experiences` como uma coleção de `Experience`. Cada
experiência tem `role`, `company`, `start_date`, `end_date` opcional,
`activities` e `achievements`.

`ExperienceRequirement` pode declarar `role`, `company` e
`minimum_duration`. O matching atual possui `ExactCandidateCriterionMatcher` e
um matcher dedicado para Education, mas não possui matcher dedicado para
Experience. Categorias sem matcher específico retornam `UNSUPPORTED`.

O matching existente normaliza nomes com `strip().casefold()`. Não há contrato
atual que defina cálculo determinístico de duração por datas.

## 2. Role e company

Role e company podem ser matched determinísticamente por igualdade normalizada.
O subconjunto seguro é baseado somente no campo correspondente de
`Candidate.Experience`:

```text
normalize(value) = value.strip().casefold()
```

Não são permitidos aliases, sinônimos, substring, fuzzy matching, NLP,
embeddings ou LLM. Portanto `Software Eng.` não é equivalente a
`Software Engineer`.

## 3. Normalização

A decisão é **STRIP_CASEFOLD**.

Assim, `" Backend Developer "` e `"backend developer"` são iguais para o
matching de role/company. Essa normalização serve apenas para igualdade
determinística; não traduz, corrige, expande abreviações nem cria equivalências
semânticas.

## 4. Mesmo registro

As dimensões role e company devem ser satisfeitas pelo **MESMO**
`Candidate.Experience`.

Isso evita combinar artificialmente o role de uma experiência com a company de
outra. No exemplo com `Backend Developer` em `Other Corp` e `Example Corp` em
`Support Analyst`, o resultado é **NOT_MATCHED**. O requisito descreve um único
registro de experiência com todas as dimensões declaradas.

## 5. Duration

O contrato atual não define com segurança inclusão ou exclusão das datas,
tratamento de meses parciais, anos parciais, conversão entre years/months nem
data de referência para `end_date=None`. Não deve ser criada uma fórmula nesta
auditoria.

```text
Closed experience: NÂO SUPORTADO
end_date=None: NÂO SUPORTADO
Months: NÂO SUPORTADO
Years: NÂO SUPORTADO
```

Qualquer `minimum_duration` deve permanecer fora do subconjunto seguro até que
um contrato próprio defina essas regras. Não usar `today`, `datetime.now()` ou
qualquer data implícita.

## 6. Múltiplas experiências

```text
Somar períodos de experiências diferentes: NÃO DEFINIDO
Tratar períodos sobrepostos: NÂO SUPORTADO
Duração por role: NÂO SUPORTADO
Duração por company: NÂO SUPORTADO
```

Não existe algoritmo contratado para soma, deduplicação, sobreposição ou
atribuição de duração a role/company. Esses comportamentos não devem ser
inferidos a partir das datas disponíveis.

## 7. Activities e achievements

Activities e achievements permanecem fora do matching de Experience. O matcher
não deve comparar o requisito com `Activity.description` ou
`Achievement.description`, nem usar esses textos como fallback para role,
company ou duração.

## 8. Casos obrigatórios

| Caso | Resultado | Motivo |
|---|---|---|
| role `Backend Developer` e role igual no candidato | MATCHED | Igualdade normalizada no mesmo Experience. |
| Diferença somente de case/whitespace em role | MATCHED | Aplicação de `strip().casefold()`. |
| Role e company satisfeitos no mesmo Experience | MATCHED | Todas as dimensões avaliáveis pertencem ao mesmo registro. |
| Role em um Experience e company em outro | NOT_MATCHED | Não é permitido combinar registros diferentes. |
| minimum_duration com experiência encerrada | UNSUPPORTED | Duração fechada ainda não tem fórmula contratada. |
| minimum_duration com `end_date=None` | UNSUPPORTED | Não há data de referência nem política para experiência atual. |
| Duas experiências curtas que juntas atingiriam a duração | UNSUPPORTED | Soma de experiências não está definida. |
| EXPERIENCE sem `experience_requirement` | UNSUPPORTED | Não existe dimensão segura para avaliar. |

Para um requisito com `role + minimum_duration`, o resultado do critério inteiro
é `UNSUPPORTED`, mesmo que o role coincida. O matcher não deve retornar
`MATCHED` parcialmente.

## 9. Classificação

**B — existe subconjunto seguro, mas duration deve permanecer UNSUPPORTED.**

Role e company têm campos diretos em `Experience` e podem usar igualdade
normalizada, desde que todas as dimensões declaradas sejam satisfeitas pelo
mesmo registro. Duration não possui contrato suficiente para avaliação segura.

## 10. Menor implementação segura

A menor implementação futura é criar `ExperienceCandidateCriterionMatcher`,
suportando somente:

- `role`;
- `company`;
- igualdade `strip().casefold()`;
- todas as dimensões avaliáveis no mesmo `Experience`;
- `UNSUPPORTED` quando `experience_requirement is None`;
- `UNSUPPORTED` quando `minimum_duration is not None`.

`ExactCandidateCriterionMatcher` deve delegar a categoria `EXPERIENCE` ao
serviço dedicado, como já delega Education. Não criar cálculo de duração,
soma de experiências ou fallback por activities/achievements nessa
implementação.

## 11. Próxima sprint

Implementar somente o matcher determinístico de Experience para role/company,
mantendo qualquer `minimum_duration` como `UNSUPPORTED`. A implementação deve
preservar a regra de mesmo registro e a normalização `strip().casefold()`.

Conclusão:

```text
Classificação: B
Role: STRIP_CASEFOLD
Company: STRIP_CASEFOLD
Mesmo registro: SIM
Duration: NÂO SUPORTADO
end_date=None: NÂO SUPORTADO
Soma de experiências: NÃO DEFINIDO
Activities/achievements: fora do matching
Menor implementação segura: ExperienceCandidateCriterionMatcher para role/company; duration como UNSUPPORTED
```
