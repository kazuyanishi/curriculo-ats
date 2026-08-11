# Education Matching Contract Audit

## 1. Contrato atual do Candidate

O agregado `Candidate` possui a coleção `education: tuple[Education, ...]`.
Cada `Education` é imutável e contém exatamente:

- `institution: str`
- `course: str`
- `status: EducationStatus`
- `start_date: date | None = None`
- `end_date: date | None = None`

`EducationStatus` possui os valores:

- `in_progress`
- `completed`
- `interrupted`

O modelo não possui um campo explícito para nível do grau, como `bachelor`,
`master` ou `doctorate`. Também não há uma distinção estruturada entre área de
estudo e curso além do próprio campo `course`.

## 2. Contrato atual de JobCriterion

`JobCriterion` é uma entidade imutável com:

- `category: CriterionCategory`
- `value: str`
- `evidence: str`
- `importance: CriterionImportance = unspecified`

Para `category == education`, não existe um tipo específico nem campos
estruturados para nível do grau, campo de estudo, instituição ou status exigido.
`value` continua sendo somente uma string não vazia.

## 3. Contrato atual da extração por IA

`JobCriterionInput` possui o mesmo contrato externo de `JobCriterion`:

- `category: CriterionCategory`
- `value: str`
- `evidence: str`
- `importance: CriterionImportance = unspecified`

O schema rejeita campos extras, exige textos não vazios e converte para
`JobCriterion` por `to_domain()`.

O prompt permite as categorias `education`, `experience` e `other`, mas não
define uma representação estruturada para requisitos de educação. Ele apenas
instrui a extrair critérios apoiados pela descrição, manter `value` curto e
preservar `evidence` literalmente. Assim, todos estes resultados continuam
compatíveis com o contrato atual:

- `Computer Science`
- `Bachelor's degree in Computer Science`
- `Bachelor's degree`
- `Degree in Computer Science or related field`

Não há garantia determinística sobre qual dessas formas a IA escolherá, nem
campos separados para comparar cada parte.

## 4. Lacunas semânticas

O contrato atual não informa, de modo estruturado e obrigatório, os elementos
que aparecem nos requisitos reais:

- nível do grau (`Bachelor's`, `Master's`, técnico etc.);
- campo ou curso exigido;
- instituição exigida;
- status exigido, como concluído ou em andamento;
- semântica de expressões como `or related field`.

O candidato possui `course`, mas não possui `degree_level`. O candidato possui
`institution` e `status`, porém o critério da vaga não os separa de `value`.
Também não existe contrato para dizer se uma ausência de um desses elementos
significa requisito irrelevante, desconhecido ou obrigatório.

## 5. Análise dos cenários A-E

### Caso A

Vaga: `Bachelor's degree in Computer Science required.`

Candidate: `course = "Computer Science"`, `status = COMPLETED`.

Não é possível afirmar `MATCHED` deterministicamente. O critério pode conter
somente texto livre e o candidato não informa se o curso é um bacharelado.
Comparar apenas `course` ignoraria uma parte material do requisito.

### Caso B

Vaga: `Bachelor's degree required.`

Candidate: `course = "Computer Science"`, `status = COMPLETED`.

`Bachelor's` não está representado em nenhum campo do Candidate. `course` não
é equivalente a nível do grau e `status = COMPLETED` informa conclusão, não o
tipo de formação concluída.

### Caso C

Vaga: `Computer Science degree or related field.`

Candidate: `course = "Information Systems"`.

O contrato atual não define `related field`, não possui catálogo de áreas
relacionadas e não autoriza inferência ou sinônimos. Portanto não há decisão
determinística segura.

### Caso D

Vaga: `Currently pursuing a degree in Computer Science.`

Candidate: `course = "Computer Science"`, `status = IN_PROGRESS`.

O Candidate possui status estruturado, mas `JobCriterion` não possui status
exigido estruturado. A frase pode ser extraída como qualquer texto em `value`,
sem garantia de que `IN_PROGRESS` seja o requisito identificado. O contrato
atual não permite uma comparação determinística formal.

### Caso E

Vaga: `Degree from Example University.`

Candidate: `institution = "Example University"`, `course = "Computer Science"`.

O critério atual não diferencia instituição de curso. A instituição do
candidato pode coincidir, mas não há um campo no critério que declare que esse
é o atributo a ser comparado. Uma string única em `value` não fornece essa
intenção com segurança.

## 6. Abordagens rejeitadas

Substring não é contrato suficiente. Por exemplo, procurar o valor da vaga no
curso poderia produzir um falso positivo para `Computer Science` quando a vaga
exige `Bachelor's degree in Computer Science`; o candidato poderia ter um
curso com esse nome, mas nenhum nível de grau compatível. O inverso também
pode gerar falsos negativos quando a redação do curso é mais específica que a
da vaga.

Também não é seguro procurar palavras em `evidence`. `evidence` é a cópia
literal da descrição da vaga para rastreabilidade; ela não separa nível, campo,
instituição ou status e não foi definida como contrato de matching.

Não são autorizadas nesta auditoria normalização adicional, aliases,
sinônimos, catálogo de áreas relacionadas ou interpretação heurística de texto.

## 7. Classificação A/B/C

**C — JobCriterion atual é insuficiente e precisa ganhar estrutura específica
para education antes do matching real.**

Essa conclusão decorre dos contratos encontrados: `JobCriterion.value` é texto
livre, não há garantia de representação, e os cinco cenários exigem decisões
sobre informações que não estão separadas no critério.

## 8. Menor mudança necessária

### OBRIGATÓRIO

Antes de implementar matching de `education`, o contrato da vaga precisa
representar explicitamente, conforme aplicável ao requisito:

- `degree_level`, para distinguir bacharelado, mestrado e outros níveis;
- `field_of_study`, para representar o curso ou área exigida;
- `institution`, quando a instituição fizer parte do requisito;
- `completion_status`, quando a vaga exigir concluído ou em andamento.

Também será necessário definir quais campos são opcionais, como ausência é
interpretada e quais valores são aceitos. O contrato correspondente deve chegar
à extração e à conversão de domínio sem depender de parsing posterior de
`evidence`.

### DESEJÁVEL / FUTURO

- um vocabulário controlado para `degree_level`;
- uma política explícita para `related field`;
- regras de normalização e equivalência, somente após serem aprovadas;
- rastreabilidade entre os campos estruturados e a evidência literal.

Esses itens não devem ser implementados nesta sprint.

## 9. Arquivos que provavelmente seriam afetados

Somente como identificação para uma sprint futura:

- `src/resume_ai/modules/jobs/domain/entities.py`
- `src/resume_ai/modules/jobs/application/schemas.py`
- `src/resume_ai/modules/jobs/infrastructure/ai_prompts.py`
- testes correspondentes do módulo Jobs

`candidate/domain/entities.py` somente seria afetado se a modelagem futura
confirmar a necessidade de adicionar `degree_level` ao Candidate. Isso ainda
não está sendo proposto como implementação nesta sprint.

## 10. Recomendação para a próxima sprint

Definir primeiro o contrato estruturado do requisito de educação na camada
Jobs, incluindo os campos obrigatórios, opcionais e seus valores permitidos.
Depois atualizar schema, conversão e prompt de forma coordenada, mantendo a
evidência como rastreabilidade literal. Somente após esse contrato existir deve
ser criada uma regra determinística para `education`.

Até lá, `education` deve permanecer `UNSUPPORTED` no Matching. Nenhuma chamada
real à OpenAI, heurística ou alteração de código foi necessária nesta auditoria.
