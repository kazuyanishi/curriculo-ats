# Cálculo de duração de experiência

O domínio do candidato representa datas profissionais com `YearMonth`, no
formato `YYYY-MM`. Por isso, a duração é calculada em meses inteiros:

```text
meses = (ano_final - ano_inicial) * 12 + (mês_final - mês_inicial)
```

Exemplos:

```text
2020-01 -> 2023-01 = 36 meses
2020-11 -> 2021-02 = 3 meses
2020-01 -> 2020-01 = 0 meses
```

Não há dias no modelo, portanto não existe arredondamento de meses parciais.

## Unidade do requisito

`ExperienceMinimumDuration` aceita um inteiro positivo e uma unidade:

- `months`: o valor é usado diretamente;
- `years`: o valor é multiplicado por 12.

O registro satisfaz o requisito quando sua duração é maior ou igual ao total
exigido.

## Experiências em andamento

`end_date=None` representa uma experiência atual. Como o contrato não recebe
uma data de referência, a duração desse registro não é calculada. Um requisito
de tempo aplicado a esse caso retorna `UNSUPPORTED`.

O sistema não usa `date.today()`, relógio global ou outra data implícita.

## Seleção do registro

Cargo e empresa, quando informados, filtram as experiências antes do cálculo.
A duração é avaliada somente quando existe um único registro compatível.

- nenhum registro compatível: `NOT_MATCHED`;
- um registro encerrado: compara a duração;
- um registro em andamento: `UNSUPPORTED`;
- mais de um registro compatível: `UNSUPPORTED`.

Períodos de empregos diferentes não são somados. Sobreposições também não são
deduplicadas. Essa política evita atribuir ao candidato uma duração que o
requisito não consegue vincular a um único registro profissional.
