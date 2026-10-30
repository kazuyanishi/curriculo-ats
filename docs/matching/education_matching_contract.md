# Contrato de matching de formação acadêmica

O matching de formação compara um `EducationRequirement` da vaga com os
registros de `Candidate.education`. A comparação é determinística e não faz
interpretação semântica de texto livre.

## Estruturas comparadas

O requisito da vaga pode informar:

- `degree_level`: nível ou tipo da formação;
- `field_of_study`: curso ou área de estudo;
- `institution`: instituição de ensino;
- `acceptable_statuses`: `completed` e/ou `in_progress`;
- `status_evidence`: trechos da vaga que sustentam cada status.

Cada formação do candidato contém:

- `course`;
- `institution`;
- `status`: `completed`, `in_progress` ou `interrupted`;
- `start_date` e `end_date`, no formato `YYYY-MM`, quando disponíveis.

## Regras de comparação

`field_of_study` é comparado com `Education.course`, e `institution` com
`Education.institution`. Os textos passam apenas por `strip().casefold()`.
Não há expansão de siglas, tradução, busca por substring, catálogo de áreas
relacionadas ou aproximação textual.

Todos os campos informados pelo requisito devem ser satisfeitos pelo mesmo
registro de formação. Dados de formações diferentes nunca são combinados.

Quando `acceptable_statuses` está vazio, o status não participa da decisão.
Quando contém valores, o registro precisa ter um dos status aceitos.

## Casos não suportados

O candidato não possui um campo estruturado equivalente a `degree_level`.
Qualquer requisito que informe esse campo retorna `UNSUPPORTED`, mesmo que o
curso ou a instituição coincidam.

Também retornam `UNSUPPORTED`:

- critérios de educação sem `education_requirement`;
- requisitos que contêm apenas status, sem curso ou instituição;
- expressões que dependem de equivalência semântica, como "área relacionada";
- alternativas entre educação e experiência que não estejam estruturadas.

## Resultados

- `MATCHED`: um registro satisfaz todos os campos comparáveis;
- `NOT_MATCHED`: o requisito é comparável, mas nenhum registro o satisfaz;
- `UNSUPPORTED`: falta estrutura suficiente para uma decisão segura.

Em um resultado positivo, `candidate_evidence_paths` identifica os campos do
candidato utilizados, por exemplo `education[0].course` e
`education[0].status`.
