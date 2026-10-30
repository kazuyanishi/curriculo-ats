# Benchmark de modelos de IA

`resume_ai.tools.ai_model_benchmark` compara os modelos configurados nos três
estágios que usam IA: extração de currículo, extração de critérios da vaga e
matching semântico com evidências. Os casos do benchmark são sintéticos.

## Execução segura

Sem argumentos, o comando apenas apresenta o plano. Ele não exige chave de API
e não faz chamadas de rede:

```bash
python -m resume_ai.tools.ai_model_benchmark
```

Para executar as chamadas, defina `RESUME_AI_API_KEY` no ambiente e informe
`--execute`:

```bash
python -m resume_ai.tools.ai_model_benchmark --execute --max-calls 9
```

O limite padrão é de 20 chamadas. O programa interrompe antes da primeira
chamada quando o plano excede `--max-calls`.

## Modelos e preços

`--models` substitui a lista padrão: `gpt-5.4-mini`, `gpt-5.6-luna` e
`gpt-5.6-terra`. O benchmark não altera `AIConfig.model` nem escolhe o modelo
usado em produção.

O parâmetro `--pricing` aceita um arquivo JSON local com a data de referência e
as taxas por milhão de tokens. Sem esse arquivo, o custo estimado é exibido
como `N/A`.

## Resultados

`--output` grava o relatório do benchmark. O arquivo contém modelo, IDs dos
casos, métricas, tokens, latência, custo e categoria de falha. Prompts,
respostas, currículos, evidências e chaves não são incluídos.

Falhas classificadas como `hard fail` invalidam o caso, independentemente da
métrica de qualidade. Qualidade, custo e latência permanecem métricas separadas
para permitir comparação explícita entre os modelos.
