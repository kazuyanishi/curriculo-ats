# AI model benchmark

`resume_ai.tools.ai_model_benchmark` compara, de forma local e isolada, os três
stages de IA já existentes: extração de currículo, extração de critérios da vaga
e matching semântico grounded. O dataset é integralmente sintético.

O comando é dry-run por padrão e não exige chave nem faz chamadas de rede:

```powershell
python -m resume_ai.tools.ai_model_benchmark
```

Para executar conscientemente, configure `RESUME_AI_API_KEY` no terminal e use
`--execute`. O limite padrão é de 20 chamadas; a execução aborta antes da primeira
chamada quando o planejamento excede `--max-calls`.

```powershell
python -m resume_ai.tools.ai_model_benchmark --execute --max-calls 9
```

Modelos podem ser informados com `--models`. A lista padrão é `gpt-5.4-mini`,
`gpt-5.6-luna` e `gpt-5.6-terra`; o benchmark nunca altera `AIConfig.model` nem
escolhe modelo de produção.

Preços são opcionais e locais. Um arquivo JSON pode ser informado por `--pricing`
com `as_of` e taxas em string Decimal por milhão de tokens. Sem esse arquivo, o
custo estimado fica como `N/A`. Resultados podem ser escritos com `--output`;
eles contêm apenas modelo, IDs de casos, métricas, tokens, latência, custo e
categoria de falha — nunca prompts, respostas, currículo, evidências ou chaves.

Um hard fail elimina o caso mesmo que a métrica de qualidade seja alta. A decisão
futura recomendada é eliminar hard fails, priorizar qualidade, comparar custo em
empates e usar latência apenas como desempate.
