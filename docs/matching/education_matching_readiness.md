# Education Matching Readiness Audit

## 1. Contrato atual do Candidate

O agregado `Candidate` possui `education: tuple[Education, ...]`. Cada registro
`Education` é imutável e contém exatamente:

```text
institution: str
course: str
status: EducationStatus
start_date: date | None
end_date: date | None
```

`EducationStatus` possui exatamente:

```text
IN_PROGRESS = "in_progress"
COMPLETED = "completed"
INTERRUPTED = "interrupted"
```

O contrato não possui `degree_level`, `qualification_level`, `degree_type` ou
`academic_level`. Portanto, o Candidate não consegue provar atualmente que um
registro é `Bachelor's`, `Master's`, `Technical`, `Associate`, `Doctorate` ou
qualquer outro nível de grau. Datas, instituição e nome do curso não podem ser
usados para inferir esse nível.

O schema de Candidate mantém os mesmos campos, converte datas e status para o
domínio e não adiciona informação de tipo de grau.

## 2. Contrato atual do EducationRequirement

`EducationRequirement` contém:

```text
degree_level: str | None
field_of_study: str | None
institution: str | None
acceptable_statuses: tuple[EducationRequirementStatus, ...]
status_evidence: tuple[EducationRequirementStatusEvidence, ...]
```

Os campos potencialmente comparáveis com Candidate são:

```text
CAMPO DE MATCHING
degree_level
field_of_study
institution
acceptable_statuses
```

`status_evidence` é campo de grounding da vaga. Ele comprova a origem textual
do status em `JobCriterion.evidence` e não é atributo do candidato nem condição
de matching.

`JobCriterion.evidence` também não deve ser usado para procurar fatos no
Candidate. É provenance da vaga. `criterion.value` não é fallback: quando
`education_requirement is None`, não se deve fazer parsing de `value` ou
`evidence`.

O `EducationRequirementTruthGate` já verifica o grounding textual antes do
matching. Isso não transforma `status_evidence` em requisito do candidato.

## 3. Mapeamento campo a campo

### `field_of_study` para `course`

O mapeamento é estruturalmente possível: `field_of_study` representa o campo
exigido e `Education.course` é o único texto acadêmico correspondente no
Candidate. A primeira implementação deve comparar os valores após uma
normalização sintática explícita:

```python
value.strip().casefold()
```

Isso não cria equivalência semântica. `Computer Science` não é automaticamente
equivalente a `Computing`, `Computer Sciences`, `Information Systems` ou
`Software Engineering`. Substring também não é aceitável: um requisito
`Science` não deve casar com `Computer Science`, pois a presença de uma palavra
não prova igualdade do campo exigido.

### `institution` para `institution`

O mapeamento é estruturalmente possível, usando a mesma normalização sintática
`strip().casefold()` dos dois lados. Isso permite tratar apenas diferenças de
espaços nas extremidades e caixa. Não autoriza aliases, abreviações, traduções
ou equivalências como `University of Example` ↔ `UOE` ou uma universidade em
português ↔ sua sigla.

### `acceptable_statuses` para `EducationStatus`

Os enums são independentes e não devem criar dependência `candidate → jobs`.
O futuro matching, que conhece os dois lados, pode usar este mapeamento por
valor:

```text
EducationRequirementStatus.COMPLETED   ↔ EducationStatus.COMPLETED
EducationRequirementStatus.IN_PROGRESS ↔ EducationStatus.IN_PROGRESS
```

`EducationStatus.INTERRUPTED` não satisfaz `COMPLETED` nem `IN_PROGRESS`.

Quando `acceptable_statuses == ()`, a política recomendada é “nenhuma
restrição de status”: o status do registro não é usado para rejeitá-lo. Isso
inclui `INTERRUPTED`; ele não deve bloquear um requisito que não estruturou
qualquer restrição de status. Essa política não transforma um requisito
genérico de grau em matchable: o caso status-only continua tratado como
`UNSUPPORTED` abaixo.

## 4. Normalização permitida

A menor política determinística para `field_of_study`/`course` e
`institution`/`institution` é:

```python
def normalize(value: str) -> str:
    return value.strip().casefold()
```

Ela é somente normalização sintática. Não implementar nesta sprint e não
confundir com equivalência semântica. NFKC/NFKD, remoção de acentos, aliases,
sinônimos, substring, fuzzy matching, embeddings e IA estão fora do contrato
atual. Assim, `Computer Science` e `computer science` podem ser equivalentes
por caixa, enquanto `Computer Science` e `Computer Sciences` não são.

## 5. Semântica de status

`COMPLETED` e `IN_PROGRESS` possuem correspondência determinística por valor
com os statuses do Candidate. `INTERRUPTED` não satisfaz nenhum dos dois.

Essa conclusão vale somente quando o requisito contém uma restrição de status
estruturada. `status_evidence` termina seu papel no grounding da vaga; sua
string literal não é comparada com o Candidate.

O caso de status ausente é diferente: `acceptable_statuses == ()` significa
que a vaga não estruturou restrição de status. A decisão recomendada é ignorar
o status do registro para requisitos que tenham outras dimensões matchable.

O caso somente-status não é considerado seguro. Uma estrutura com apenas
`acceptable_statuses=(COMPLETED,)` pode ter vindo de “Degree required”, mas o
Candidate não possui tipo ou nível de credential. Um `Education` com status
`COMPLETED` prova que existe um registro acadêmico concluído, não que ele seja
o degree exigido. Portanto não deve produzir `MATCHED`.

## 6. Regra por registro educacional

As dimensões aplicáveis devem ser satisfeitas por um único registro de
`Candidate.education`:

```text
ANY Education record
WHERE every applicable requirement dimension matches that same record
```

Uma formação que satisfaça integralmente o requisito é suficiente, mesmo que o
Candidate possua outras formações.

É proibido combinar `course` de Education A com `institution` de Education B e
`status` de Education C. Por exemplo, com:

```text
Education A: course = Computer Science, institution = University A
Education B: course = Business,          institution = University B
Requirement: field = Computer Science, institution = University B
```

não existe um registro que satisfaça as duas dimensões; o resultado não pode
ser um `MATCHED` artificial.

## 7. Dimensões não suportadas

`degree_level` é não suportado enquanto Candidate não possuir campo explícito
para nível/tipo de grau. Não inferir por nome de curso, duração, datas,
instituição ou status. Um requisito com `degree_level` permanece
`UNSUPPORTED`, ainda que `field_of_study` coincida.

Também permanecem fora do matching:

- `status_evidence`, que é grounding da vaga;
- `criterion.evidence`, que é provenance da vaga;
- `criterion.value`, que não é fallback estruturado;
- `CriterionImportance`, que não muda a decisão básica nesta etapa;
- `start_date` e `end_date`, pois `EducationRequirement` não possui requisito
  temporal;
- `related field`, aliases e education OR experience, que não devem ser
  reinterpretados pelo matcher.

## 8. Política de `UNSUPPORTED`

Recomendo a Política A — **strict unsupported**:

```text
se qualquer dimensão exigida não puder ser avaliada
→ UNSUPPORTED
```

Essa política é mais previsível e explicável que retornar `NOT_MATCHED` por uma
dimensão falsa enquanto outra dimensão obrigatória permanece desconhecida. Ela
evita que um candidato seja rejeitado ou aprovado com base em uma decisão
parcial e preserva o significado de `UNSUPPORTED`.

Com essa política:

- `degree_level != None` força `UNSUPPORTED`;
- `education_requirement is None` força `UNSUPPORTED`, sem fallback para
  `value`/`evidence`;
- requisito somente-status/genérico força `UNSUPPORTED`;
- requisitos compostos com uma dimensão não suportada também forçam
  `UNSUPPORTED`;
- somente depois de todas as dimensões serem avaliáveis o matcher pode produzir
  `MATCHED` ou `NOT_MATCHED`.

## 9. Cenários obrigatórios

### Campo, instituição e status

`field_of_study`, `institution` e `acceptable_statuses` são matchable quando
não há `degree_level`, o requisito tem pelo menos uma dimensão estruturada
além de um status-only, e todas as dimensões são avaliadas no mesmo registro.

### Requisito somente field

É matchable por `field_of_study ↔ course`. O status é ignorado quando a vaga
não especificou `acceptable_statuses`.

### Requisito somente institution

É matchable por `institution ↔ institution`, com a mesma regra de
normalização sintática.

### Field + institution

É matchable somente quando curso e instituição coincidem no mesmo `Education`.

### Field + status / institution + status

São matchable quando o mesmo registro satisfaz texto e status, e não existe
`degree_level`.

### Todos os campos avaliáveis

`field_of_study + institution + acceptable_statuses` é matchable por um único
registro, porque cada dimensão possui contraparte no Candidate.

### `education_requirement = None`

Permanece `UNSUPPORTED`. Isso inclui education legada sem estrutura; não há
parsing de `criterion.value` nem de `criterion.evidence`.

### Generic degree / status-only

Permanece `UNSUPPORTED`: Candidate não prova que um registro acadêmico
concluído é o tipo de degree exigido.

### Related field e Education OR Experience

Permanecem `UNSUPPORTED` ou sem requisito estruturado conforme o contrato de
extração. O matcher não cria equivalências nem transforma uma alternativa em
duas condições.

## 10. Matriz de prontidão

| Requirement | Avaliável? | Resultado possível | Justificativa |
|---|---|---|---|
| `field_of_study` | MATCHABLE | `MATCHED`/`NOT_MATCHED` | Comparável a `Education.course` por igualdade após normalização sintática. |
| `institution` | MATCHABLE | `MATCHED`/`NOT_MATCHED` | Comparável ao campo `Education.institution`; sem aliases. |
| `acceptable_statuses` com field/institution | MATCHABLE | `MATCHED`/`NOT_MATCHED` | Statuses `completed`/`in_progress` têm correspondência direta. |
| `field + institution` | MATCHABLE | `MATCHED`/`NOT_MATCHED` | As duas dimensões devem coincidir no mesmo registro. |
| `field + status` | MATCHABLE | `MATCHED`/`NOT_MATCHED` | Curso e status existem no mesmo `Education`. |
| `institution + status` | MATCHABLE | `MATCHED`/`NOT_MATCHED` | Instituição e status existem no mesmo `Education`. |
| `field + institution + status` | MATCHABLE | `MATCHED`/`NOT_MATCHED` | Todas as dimensões são avaliáveis no mesmo registro. |
| `degree_level` | UNSUPPORTED | `UNSUPPORTED` | Candidate não possui nível/tipo de grau. |
| `degree_level + field` | UNSUPPORTED | `UNSUPPORTED` | Uma dimensão obrigatória permanece não avaliável. |
| `education_requirement=None` | UNSUPPORTED | `UNSUPPORTED` | Não há contrato estruturado; não usar fallback textual. |
| generic degree / status-only | UNSUPPORTED | `UNSUPPORTED` | Status concluído não prova tipo de degree. |

## 11. Local arquitetural do matcher

Education não deve ser forçado dentro da lógica de igualdade simples do
`ExactCandidateCriterionMatcher`. As categorias atuais comparam um nome
normalizado contra uma coleção de itens; Education exige selecionar um registro
e validar múltiplas dimensões com `UNSUPPORTED` parcial.

Recomendo um serviço dedicado conceitualmente chamado
`EducationCandidateCriterionMatcher`, composto no fluxo de matching. O
`ExactCandidateCriterionMatcher` pode delegar `CriterionCategory.EDUCATION` a
esse serviço sem alterar a porta pública `CandidateCriterionMatcher`. O serviço
dedicado deve retornar apenas os `MatchStatus` existentes:
`MATCHED`, `NOT_MATCHED` e `UNSUPPORTED`.

Nenhuma classe é criada nesta sprint.

## 12. Classificação A/B/C

**B — Candidate atual é suficiente para um subconjunto determinístico; os
requisitos fora desse subconjunto devem permanecer `UNSUPPORTED`.**

O subconjunto seguro é composto por requisitos sem `degree_level`, sem
semântica genérica de degree/status-only e com dimensões de field, institution
e/ou status avaliadas no mesmo registro. A classificação A ignoraria a ausência
de nível/tipo de grau; C ignoraria os mapeamentos estruturais seguros que já
existem.

## 13. Menor implementação segura

A menor implementação futura deverá:

1. retornar `UNSUPPORTED` para `education_requirement is None`,
   `degree_level != None` e generic degree/status-only;
2. normalizar somente `strip().casefold()` para field/course e
   institution/institution;
3. verificar igualdade, nunca substring, aliases ou fuzzy matching;
4. avaliar todas as dimensões aplicáveis em um único `Education`;
5. mapear apenas `COMPLETED` e `IN_PROGRESS`, ignorando status quando a tupla
   de statuses aceitáveis for vazia;
6. retornar `MATCHED` se um registro satisfizer tudo, caso contrário
   `NOT_MATCHED`, desde que o requisito inteiro seja avaliável.

## 14. Mudanças futuras necessárias

Para suportar `degree_level`, provavelmente serão necessários, após contrato
próprio:

- `src/resume_ai/modules/candidate/domain/entities.py`;
- `src/resume_ai/modules/candidate/application/schemas.py`;
- testes de domínio e schema de Candidate;
- contrato de dados JSON/resume master e exemplos correspondentes.

O lado Jobs não deve ser alterado nesta sprint. Também não há motivo para
acoplar enums do Candidate aos enums de Jobs; a tradução pertence ao futuro
matching.

## 15. Recomendação para a próxima sprint

Recomendo o **Caminho 1**: implementar primeiro somente o subconjunto
comprovadamente seguro, mantendo strict `UNSUPPORTED` para degree level,
generic degree/status-only e qualquer requisito não estruturado. Isso preserva
explicabilidade e evita falsos `MATCHED` enquanto o contrato Candidate ainda
não prova o tipo de grau.

Depois, uma sprint separada pode auditar e, se aprovado, adicionar
`degree_level` ao Candidate e aos contratos de dados. Essa mudança não deve
ser antecipada para desbloquear o subconjunto seguro.

Durante toda esta sprint, Education permanece `UNSUPPORTED` no Matching; este
documento é somente análise e não implementa matcher.
