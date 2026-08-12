# Experience Duration Matching Contract

## 1. Estado atual

`Experience` possui `start_date` obrigatório e `end_date` opcional. O domínio
representa `minimum_duration` com um inteiro positivo e unidade `months` ou
`years`.

O matcher de Experience atualmente suporta somente role/company com igualdade
`strip().casefold()`. Qualquer `minimum_duration` permanece `UNSUPPORTED`.
Esta sprint define o contrato futuro, mas não implementa o cálculo nem altera o
matcher.

## 2. Experiência encerrada

O subconjunto futuro suportado será uma única experiência encerrada, com
`start_date` e `end_date` presentes e `end_date >= start_date`.

A duração será contada em **meses calendáricos completos**, sem aproximação por
`dias / 30` ou `dias / 365`. Um mês completo termina quando a data alcança o
mesmo dia do mês de início. Se o dia final for anterior ao dia inicial, o mês
parcial não será contado.

Conceitualmente, para uma experiência encerrada:

```text
months = (end.year - start.year) * 12 + (end.month - start.month)
if end.day < start.day:
    months -= 1
```

Essa fórmula é apenas a especificação desta auditoria; não deve ser
implementada nesta sprint.

Exemplos:

```text
2020-01-01 -> 2023-01-01 = 36 meses
2020-01-15 -> 2023-01-14 = 35 meses
2020-01-15 -> 2023-01-15 = 36 meses
2020-01-01 -> 2020-01-01 = 0 meses
2020-11-01 -> 2021-02-01 = 3 meses
2020-11-15 -> 2021-02-14 = 2 meses
2020-11-15 -> 2021-02-15 = 3 meses
```

Não há arredondamento de mês parcial. Uma experiência com `start_date ==
end_date` tem duração zero e não satisfaz qualquer `minimum_duration`, que é
sempre positivo.

## 3. Conversão months/years

O cálculo interno será feito em meses inteiros:

```text
YEARS -> value * 12 meses: SIM
MONTHS -> value meses: SIM
```

Não serão usados números decimais, conversões aproximadas ou arredondamentos.
O valor de `minimum_duration` deve ser comparado com a quantidade de meses
calendáricos completos da experiência.

## 4. end_date=None

Experiência com `end_date=None` permanece **UNSUPPORTED**.

Não será usada data implícita, `date.today()`, `datetime.now()` ou relógio
global. Uma futura evolução poderia receber uma `reference_date` explícita,
mas esse contrato não será introduzido agora; até sua eventual aprovação,
experiências abertas não podem participar do matching de duração.

```text
Reference date: não existe no contrato atual
```

## 5. Mesmo registro

Role, company e minimum_duration devem ser satisfeitos pelo mesmo objeto
`Candidate.Experience`.

Assim, uma experiência como `Backend Developer` por 24 meses e outra como
`Support Analyst` por 24 meses não satisfazem um requisito de `Backend
Developer` por 36 meses. O resultado é `NOT_MATCHED`, não uma soma implícita.

Essa regra mantém a conjunção já definida para role/company e impede que a
duração seja atribuída a um registro diferente daquele que satisfez o restante
do requisito.

## 6. Soma de experiências

```text
Somar experiências diferentes: AINDA NÃO SUPORTADO
```

Não será definido algoritmo de soma nesta etapa. Para suportá-la seria
necessário especificar quais registros entram, filtragem por role/company,
períodos simultâneos, sobreposição e deduplicação temporal. Até existir esse
contrato, qualquer caso que dependa de somar experiências retorna
`UNSUPPORTED`.

Períodos sobrepostos entre experiências diferentes também são
**NÃO SUPORTADOS**. Não serão somados nem deduplicados por inferência.

## 7. Casos obrigatórios

| Caso | Resultado | Regra aplicada |
|---|---|---|
| `2020-01-01 -> 2023-01-01`, requisito `3 years` | MATCHED | 36 meses completos satisfazem 36 meses. |
| Período menor que `3 years` | NOT_MATCHED | A experiência fechada é avaliável, mas não alcança 36 meses. |
| Diferença somente de mês parcial | NOT_MATCHED | O mês parcial não é contado; o total fica abaixo do requisito. |
| `start_date == end_date` | NOT_MATCHED | Duração zero não satisfaz requisito positivo. |
| `end_date=None` | UNSUPPORTED | Não há data de referência explícita. |
| Role + duration no mesmo Experience | MATCHED ou NOT_MATCHED | Depende de role e meses completos do mesmo registro. |
| Role em um Experience e duração em outro | NOT_MATCHED | Não é permitido combinar registros. |
| Duas experiências que só juntas atingem a duração | UNSUPPORTED | Soma de experiências ainda não é suportada. |
| Períodos sobrepostos | UNSUPPORTED | Não há regra de sobreposição ou deduplicação. |

Um requisito que contenha duration junto com role/company será `UNSUPPORTED`
quando a experiência não estiver no subconjunto fechado de registro único. Não
deve retornar `MATCHED` parcialmente apenas porque role ou company coincidem.

## 8. Classificação final

**B — existe subconjunto seguro de duration.**

O subconjunto é:

```text
uma única Candidate.Experience
start_date presente
end_date presente
meses calendáricos completos
minimum_duration em meses inteiros
role/company, quando presentes, no mesmo registro
sem soma ou tratamento de sobreposição
```

Experiências abertas, soma, sobreposição e qualquer dependência de data
implícita permanecem `UNSUPPORTED`.

## 9. Menor próxima mudança

A menor implementação segura é adicionar um helper puro e determinístico para
calcular meses calendáricos completos entre `start_date` e `end_date`, sem
relógio e sem efeitos externos. Em seguida, estender
`ExperienceCandidateCriterionMatcher` para avaliar duration somente no
subconjunto definido aqui.

Essa implementação deve manter:

- `end_date=None` como `UNSUPPORTED`;
- experiências diferentes sem soma;
- períodos sobrepostos sem suporte;
- role/company e duration no mesmo `Experience`;
- anos convertidos para meses inteiros.

Nenhum helper, cálculo ou alteração de produção é criado nesta sprint.

Conclusão:

```text
Classificação: B
Regra de meses: meses calendáricos completos, sem aproximação por dias
YEARS -> months: SIM, value * 12
Meses parciais: não são contados
end_date=None: UNSUPPORTED
Reference date: não definida; nenhuma data implícita
Mesmo registro: SIM
Soma de experiências: AINDA NÃO SUPORTADO
Overlap: NÃO SUPORTADO
Menor implementação segura: helper puro de meses completos e extensão do matcher
```
