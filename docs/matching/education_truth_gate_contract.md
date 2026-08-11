# Education Structured Truth Gate Audit

## 1. Estado atual

O fluxo atual é:

```text
JobPosting.description
        ↓
AI extraction
        ↓
JobCriterion
        ├── value
        ├── evidence
        └── education_requirement
                ├── degree_level
                ├── field_of_study
                ├── institution
                └── acceptable_statuses
```

`JobCriterion.evidence` continua sendo uma cópia literal da vaga. O
`JobCriteriaTruthGate` atual garante somente:

```text
criterion.evidence in job.description
```

Ele não valida nenhum campo interno de `education_requirement`.

O contrato da Sprint 3.13 instrui a extração a preencher os campos somente
quando forem explicitamente sustentados e a deixar o requisito como `null`
quando a semântica não puder ser representada fielmente. O schema atual aceita
os quatro campos e converte status externos para os dois enums permitidos,
mas não mantém evidência individual para cada campo.

## 2. Degree level

Para:

```text
evidence: "Bachelor's degree in Computer Science is required."
degree_level: "Bachelor's"
```

`degree_level in evidence` é uma validação sintática conservadora neste
contrato, porque o prompt exige preservar o texto explicitamente informado e
proíbe conversões como `BSc` para `Bachelor's`. Ela prova que a expressão
retornada está presente na evidência.

Ela não prova sozinha que a IA atribuiu corretamente o papel semântico de
número de nível à expressão. Essa limitação é aceitável apenas enquanto o
contrato do prompt continuar exigindo extração conservadora e textual.

Para:

```text
evidence: "BSc in Computer Science"
degree_level: "Bachelor's"
```

o containment falha, como deve falhar: a Sprint 3.13 proíbe essa alteração
textual. Se o retorno for `degree_level = "BSc"`, o containment passa e a
representação preserva o texto da vaga.

## 3. Field of study

Para:

```text
evidence: "Bachelor's degree in Computer Science is required."
field_of_study: "Computer Science"
```

`field_of_study in evidence` é uma verificação determinística de grounding
textual e é suficientemente conservadora para rejeitar um campo que não
apareça na evidência. Ela não autoriza equivalências: `Information Systems`
não passa a ser `Computer Science`, e `related field` não é transformado em um
campo específico.

Como em qualquer containment, a presença literal não prova toda a interpretação
gramatical do trecho. A garantia disponível é a mais limitada definida pelo
contrato atual: o valor estruturado não pode introduzir texto ausente.

## 4. Institution

Para:

```text
evidence: "Degree from Example University required."
institution: "Example University"
```

o containment literal fornece uma validação sintática conservadora. O prompt
também restringe `institution` a uma instituição específica explicitamente
exigida, portanto expressões genéricas como `accredited university` não devem
ser transformadas em um nome.

A presença de `University` isoladamente não prova uma instituição específica.
Por isso o prompt deve continuar impedindo que qualificadores genéricos sejam
estruturados como nomes. O gate não deve adicionar conhecimento externo sobre
universidades.

## 5. Acceptable statuses

### `IN_PROGRESS`

Para:

```text
evidence: "Currently pursuing a degree in Computer Science."
acceptable_statuses: (in_progress,)
```

a string `in_progress` não aparece na evidência. O retorno depende da
transformação semântica de `currently pursuing` para o enum. Portanto um
containment literal não valida esse campo.

### `COMPLETED`

`Completed degree in Computer Science required.` contém uma expressão explícita
de conclusão e justifica semanticamente `completed`, mas `Must hold a
Bachelor's degree.` usa outra construção. Ambas podem justificar o mesmo enum
por interpretação linguística, não por igualdade textual.

O contrato atual não possui uma tabela fechada e completa de frases, nem
evidência da expressão que originou cada status. Logo não é possível provar de
forma geral que todo `completed` foi extraído corretamente sem uma regra
linguística adicional.

### Ambos os statuses

Em:

```text
Graduates and currently enrolled students are eligible.
```

os dois statuses dependem de reconhecer duas expressões semânticas diferentes.
O tuple `(completed, in_progress)` preserva o resultado, mas não preserva qual
trecho sustentou cada item. O contrato atual não permite validar essa relação
deterministicamente.

### Status ausente

Para `Education in Computer Science.`, `acceptable_statuses == ()` representa
corretamente que nenhum status foi estruturado. Não há um status inventado para
validar e nenhum gate adicional é necessário apenas pela tuple vazia. O objeto
continua válido porque `field_of_study` fornece conteúdo ao requisito.

## 6. Casos de teste conceituais

### Invenção explícita

Com:

```text
evidence: "Bachelor's degree required."
degree_level: "Bachelor's"
field_of_study: "Computer Science"
```

um futuro gate que faça containment deve aceitar o nível e rejeitar
`Computer Science`, pois esse texto não aparece na evidência. A evidência
global passa pelo Gate 1, mas o campo inventado falha no Gate 2.

### Caso parcialmente correto

Com:

```text
evidence: "Bachelor's degree required."
degree_level: "Bachelor's"
field_of_study: null
```

o nível possui grounding textual e o campo ausente não faz uma afirmação
indevida. Esse caso deve ser distinguido do objeto que inventa
`field_of_study`.

### Alteração textual e caso preservado

`BSc` não deve ser silenciosamente convertido para `Bachelor's`. O caso
`degree_level = "Bachelor's"` com evidence `BSc in Computer Science` deve ser
rejeitado por containment; o caso `degree_level = "BSc"` e
`field_of_study = "Computer Science"` pode passar a verificação textual.

### `related field`

Para `Degree in Computer Science or related field.`, a política atual exige
`education_requirement = null`. O Truth Gate não deve tentar interpretar a
expressão, criar um catálogo de equivalências ou escolher um curso do
candidato.

### Education OR Experience

Para `Bachelor's degree or 4 years of professional experience.`, o requisito
educacional deve permanecer `null` pela política atual. O gate não pode
transformar uma alternativa em dois requisitos obrigatórios.

## 7. Abordagens avaliadas

### Abordagem A — containment literal

```python
structured_value in criterion.evidence
```

Vantagens:

- é determinística;
- não usa IA, rede ou conhecimento externo;
- rejeita valores inventados ou normalizados que não estejam presentes;
- é compatível com a política de preservação textual do prompt para nível,
  campo e instituição.

Limitações:

- não valida a transformação semântica de frases para statuses;
- não prova sozinha o papel gramatical de uma substring;
- não representa `related field`, alternativas ou qualificadores genéricos;
- não deve ser usada para inferir um campo a partir de texto semelhante.

Assim, containment é uma condição necessária e conservadora para os campos
textuais, não um validador universal de toda a estrutura educacional.

### Abordagem B — dicionário de frases para status

Um mapa como `currently pursuing → IN_PROGRESS` e `graduated → COMPLETED`
seria uma regra linguística fechada somente se o vocabulário, os idiomas, as
variações e os limites fossem definidos formalmente. No contrato atual, ele
seria uma heurística incompleta: a vaga pode estar em português ou outro
idioma, pode usar paráfrases e pode combinar condições.

Esse dicionário não deve ser tratado como Truth Gate suficiente nesta sprint.
`currently pursuing → IN_PROGRESS` é transformação semântica, não
`strip()`/`casefold()`.

### Abordagem C — evidência por campo

Uma estrutura futura que associe cada valor estruturado à sua própria evidência
literal resolveria o principal problema dos statuses e tornaria explícita a
origem de cada atributo, por exemplo:

```text
degree_level: value="Bachelor's", evidence="Bachelor's"
field_of_study: value="Computer Science", evidence="Computer Science"
status: value=IN_PROGRESS, evidence="currently pursuing"
```

Para múltiplos statuses, cada status precisaria ter sua própria evidência, ou
um contrato equivalente que preserve as duas expressões independentes. Essa é
uma direção de modelagem, não uma implementação nesta sprint. A evidência
global de `JobCriterion` continuaria necessária como evidência literal do
critério completo; as evidências por campo seriam rastreabilidade adicional,
não substituição automática.

## 8. Local arquitetural do gate

O Gate 1 atual pertence ao `JobCriteriaTruthGate` e verifica a presença da
evidência completa na descrição da vaga.

Um Gate 2 para campos educacionais deve ser uma responsabilidade separável do
mesmo fluxo de validação, mas a semântica específica e a necessidade de
evidência por campo sugerem um serviço dedicado como
`EducationRequirementTruthGate`, composto pelo gate de Jobs. Isso evita
misturar a regra literal geral com regras futuras específicas de education.

Nenhuma classe é criada nesta sprint. Qualquer implementação futura deve
permanecer no domínio Jobs, sem depender de Pydantic, OpenAI, Candidate,
Matching ou infraestrutura.

## 9. Classificação A/B/C

**B — o contrato atual permite validar deterministicamente apenas parte dos
campos.**

- `degree_level`: containment literal é aplicável sob a regra de preservação
  textual do prompt, mas não valida uma transformação semântica não autorizada.
- `field_of_study`: containment literal é aplicável como grounding conservador;
  não autoriza related fields ou equivalências.
- `institution`: containment literal é aplicável para um nome explicitamente
  exigido, sem validar qualificadores genéricos ou conhecimento externo.
- `acceptable_statuses`: não é validável de forma geral pelo contrato atual,
  porque os enums resultam de interpretação semântica e não têm evidência por
  status.

Portanto A é forte demais e C ignora que os três campos textuais possuem uma
condição de grounding útil e determinística. A classificação correta é B.

## 10. Menor mudança necessária

### OBRIGATÓRIO

Para fechar a validação de `acceptable_statuses`, preservar a origem textual de
cada status estruturado. A menor mudança conceitual é adicionar, ao contrato de
education, evidência literal por status — uma evidência para `completed` e uma
para cada ocorrência de `in_progress` — e validar essa evidência contra o
`JobCriterion.evidence`. O formato exato deve ser definido em uma sprint de
contrato própria.

Também será obrigatório definir uma política fechada para os idiomas e frases
aceitos antes de chamar a transformação de regra de domínio, em vez de
apresentar um dicionário parcial como prova universal.

### DESEJÁVEL / FUTURO

- evidência por campo para `degree_level`, `field_of_study` e `institution`,
  para melhorar rastreabilidade e rejeitar ambiguidades de papel;
- vocabulário controlado ou regra formal para expressões de status;
- contrato explícito para múltiplos statuses e suas evidências independentes;
- testes de idioma e de casos alternativos.

Esses itens não devem ser implementados nesta auditoria.

## 11. Arquivos provavelmente afetados

Somente como identificação futura:

- `src/resume_ai/modules/jobs/domain/entities.py`
- `src/resume_ai/modules/jobs/application/schemas.py`
- `src/resume_ai/modules/jobs/infrastructure/ai_prompts.py`
- `src/resume_ai/modules/jobs/domain/services.py`
- testes correspondentes do módulo Jobs

Não há necessidade de alterar Candidate, Matching, bootstrap ou CLI para este
gate conceitual.

## 12. Recomendação para a próxima sprint

Definir primeiro o contrato de proveniência dos statuses educacionais e, se
necessário, a proveniência dos demais campos. Depois implementar um Gate 2
determinístico que mantenha o Gate 1 global, rejeite campos estruturados sem
evidência suficiente e preserve `education_requirement = null` para related
fields, alternativas education/experience e qualquer semântica não
representável.

Até essa definição, `education` deve continuar `UNSUPPORTED` no Matching. Não
executar heurística, dicionário aberto ou chamada real à OpenAI para validar
esta auditoria.
