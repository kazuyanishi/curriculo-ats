# Contrato de matching de experiência profissional

O matching de experiência compara `ExperienceRequirement` com os registros de
`Candidate.experiences`.

## Estrutura do requisito

Um requisito pode conter:

- `role`: cargo ou função;
- `company`: empresa;
- `minimum_duration`: quantidade inteira positiva em meses ou anos;
- `minimum_duration_evidence`: trecho literal que sustenta a duração.

Pelo menos `role`, `company` ou `minimum_duration` deve estar presente.

## Cargo e empresa

Cargo e empresa usam igualdade após `strip().casefold()`. A comparação não
aceita substring, aliases, abreviações, tradução ou aproximação semântica.

Quando os dois campos estão presentes, ambos precisam coincidir no mesmo
registro de experiência. O matcher não combina o cargo de um emprego com a
empresa de outro.

## Duração

Anos são convertidos para meses por multiplicação por 12. A duração do registro
é a diferença entre os valores mensais de `start_date` e `end_date`.

Uma experiência em andamento (`end_date=None`) não tem duração fechada e
retorna `UNSUPPORTED` para requisitos temporais. Nenhuma data atual implícita é
utilizada.

Quando mais de uma experiência satisfaz cargo e empresa, o matcher não soma nem
escolhe arbitrariamente uma delas para avaliar a duração; o resultado é
`UNSUPPORTED`.

## Resultados

- `MATCHED`: um registro satisfaz cargo, empresa e duração aplicáveis;
- `NOT_MATCHED`: o requisito é avaliável, mas não há registro compatível;
- `UNSUPPORTED`: o critério não tem estrutura suficiente ou depende de uma
  combinação temporal não definida.

Critérios de experiência sem `experience_requirement` retornam `UNSUPPORTED`.
Atividades e conquistas não são usadas como fallback.

Em resultados positivos, `candidate_evidence_paths` aponta os campos usados,
como `experiences[0].role`, `experiences[0].start_date` e
`experiences[0].end_date`.
