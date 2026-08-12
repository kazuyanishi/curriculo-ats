# Experience Matching Contract Audit

## 1. Estado atual

Não existe `ExperienceRequirement` nem contrato equivalente no domínio Jobs.
Também não existe matcher específico de Experience.

No `ExactCandidateCriterionMatcher`, somente skill, technology, tool, language
e certification são encaminhados para coleções do Candidate. As categorias
`EXPERIENCE` e `OTHER` caem no retorno genérico:

```text
CriterionMatch(criterion=criterion, status=UNSUPPORTED)
```

Esse comportamento é confirmado pelos testes do matcher. Nenhum matching de
Experience é feito hoje por `value`, `evidence`, activities ou achievements.

## 2. Candidate Experience

O Candidate possui `experiences: tuple[Experience, ...]`. Cada `Experience`
imutável contém exatamente:

```text
company: str
role: str
start_date: date
end_date: date | None
activities: tuple[Activity, ...]
achievements: tuple[Achievement, ...]
```

`company` e `role` são textos não vazios. `start_date` é obrigatório,
`end_date` é opcional e não pode ser anterior ao início. Activities e
achievements também são coleções estruturadas, mas seus textos descrevem
responsabilidades/resultados e não possuem relação formal com um requisito da
vaga.

O contrato não define soma de experiências, cálculo de duração, tratamento de
períodos sobrepostos ou agrupamento por role/company.

## 3. JobCriterion

`JobCriterion` contém somente:

```text
category: CriterionCategory
value: str
evidence: str
importance: CriterionImportance
education_requirement: EducationRequirement | None
```

Não há campos específicos para role, company, quantidade de tempo, unidade de
tempo ou área relacionada à duração. `value` é uma string curta genérica e
`evidence` é provenance literal da vaga; nenhum dos dois declara qual parte
representa uma empresa, um cargo ou uma duração.

Não é seguro fazer parsing de `value` ou `evidence` para recuperar essa
intenção. Isso criaria semântica não presente no contrato.

## 4. Role

**NÃO SEGURO.**

Embora `Experience.role` exista, um `JobCriterion` com:

```text
value = "Backend Developer"
category = EXPERIENCE
```

não informa formalmente que `value` deve ser comparado a `Experience.role`.
O mesmo valor poderia ser uma descrição livre do requisito, uma função
relacionada à empresa ou parte de uma exigência mais ampla.

Logo, o Caso 1 — “Backend Developer experience required” versus role igual —
não pode produzir match seguro com o contrato atual. Igualdade textual só seria
permitida depois de um campo estruturado declarar explicitamente a dimensão
`role`; a normalização sintática futura poderia então ser limitada a
`strip().casefold()`, sem aliases ou substring.

## 5. Company

**NÃO.**

Para:

```text
value = "Example Corp"
category = EXPERIENCE
```

o contrato atual não identifica que o valor representa empresa, em vez de role
ou outro texto do requisito. Portanto não é possível comparar com
`Experience.company` de forma determinística.

No Caso 3, a igualdade entre `Example Corp` e `Experience.company` pode ser
textualmente verdadeira, mas a intenção do campo da vaga continua ambígua.
Não usar parsing, evidence ou convenções linguísticas para resolver essa
ambiguidade.

## 6. Duration

**NÃO SUPORTADO.**

O Candidate possui datas, mas `JobCriterion` não representa:

```text
quantidade
unidade
área/role relacionada à duração
```

Assim, “3 years of backend experience” não pode ser convertido
deterministicamente em um requisito com os contratos atuais. Não calcular
duração nesta auditoria.

O Caso 2 também não autoriza somar duas experiências: o contrato atual não
define soma, períodos sobrepostos, vínculo da duração a um role ou company,
datas inclusivas/exclusivas, nem a interpretação de `end_date=None`. Qualquer
dessas regras exigiria contrato próprio.

## 7. Activities e achievements

`Activity.description` e `Achievement.description` são textos estruturados do
Candidate, mas não existe no `JobCriterion` uma dimensão que declare que um
requisito de Experience deve ser comparado a esses campos.

No Caso 4, “Experience with customer support” não pode ser comparado
deterministicamente com `Activity("Provided ERP technical support")`. Não usar
substring, NLP, embeddings, sinônimos ou interpretação semântica. Activities e
achievements permanecem **NÃO SUPORTADOS** para esse matching até existir
contrato explícito.

## 8. Casos obrigatórios

### Caso 1 — role

```text
Vaga: Backend Developer experience required
Candidate: role = Backend Developer
```

O contrato atual não sabe que `JobCriterion.value` representa role. Resultado
seguro: `UNSUPPORTED`.

### Caso 2 — duração e múltiplas experiências

```text
Vaga: 3 years of backend development experience
Candidate: duas experiências com datas diferentes
```

JobCriterion não possui quantidade, unidade ou vínculo com role. Também não
define se experiências podem ser somadas. Resultado seguro: `UNSUPPORTED`;
nenhuma soma deve ser feita.

### Caso 3 — company

```text
Vaga: Experience at Example Corp
Candidate: company = Example Corp
```

O valor da vaga não declara estruturalmente a dimensão company. A coincidência
textual não resolve a intenção. Resultado seguro: `UNSUPPORTED`.

### Caso 4 — activities

```text
Vaga: Experience with customer support
Candidate: Activity("Provided ERP technical support")
```

Não existe contrato para comparar o requisito com Activity.description, e a
semelhança não pode ser estabelecida por substring ou NLP. Resultado seguro:
`UNSUPPORTED`.

## 9. Classificação A/B/C

**C — JobCriterion precisa de estrutura específica de EXPERIENCE antes do
matching real.**

O Candidate possui dados acadêmicos/profissionais suficientes para armazenar
role, company, datas, activities e achievements, mas o requisito da vaga só
possui texto genérico. Sem declarar a dimensão exigida, qualquer matcher teria
que interpretar `value`/`evidence` ou assumir que toda categoria EXPERIENCE é
role, company ou duração. Essas alternativas não são determinísticas.

## 10. Menor contrato futuro

O menor `ExperienceRequirement` futuro deve representar somente:

```text
role: str | None
company: str | None
minimum_duration: quantidade + unidade | None
```

`role` e `company` devem ser dimensões distintas, para impedir que o matcher
confunda cargo com empresa. `minimum_duration` precisa preservar pelo menos
quantidade e unidade; também deve declarar como se relaciona ao role/company
quando essa restrição existir.

O contrato futuro deve definir quais campos são opcionais e como um requisito
sem qualquer dimensão estruturada é classificado. Não adicionar seniority,
industry, activities, achievements, skills ou technologies nesta etapa.

O contrato também precisará decidir, em sprint própria, datas inclusivas ou
exclusivas, `end_date=None`, soma de experiências, períodos sobrepostos,
duração por role e duração por company. Nenhuma dessas regras está sendo
definida aqui.

## 11. Próxima sprint

A próxima sprint deve criar somente o contrato de domínio
`ExperienceRequirement`, se essa direção for aprovada. Ela não deve incluir
schema, prompt, Truth Gate ou matcher no mesmo passo.

Até esse contrato existir, `CriterionCategory.EXPERIENCE` deve permanecer
`UNSUPPORTED`. Não usar `JobCriterion.value`, `JobCriterion.evidence`,
Activity.description ou Achievement.description como fallback de matching.

```text
Classificação:
C

Role:
NÃO SEGURO

Company:
NÃO

Duration:
NÃO SUPORTADO

Activities/achievements:
NÃO SUPORTADOS

Menor contrato futuro:
ExperienceRequirement com role, company e minimum_duration estruturados
```
