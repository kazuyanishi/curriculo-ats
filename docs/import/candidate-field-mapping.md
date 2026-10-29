# Mapeamento canônico da importação de candidato

## Escopo e fonte de verdade

Este documento registra o contrato observado no branch atual para a Sprint E1-S01. Foram inspecionados os schemas de extração e rascunho, a conversão, o pipeline, o Truth Gate, os extratores PDF/DOCX, o prompt e as heurísticas, o `Candidate` de domínio, os tipos e o formulário do frontend e os testes existentes. Nenhum comportamento de produção foi alterado.

Estados usados:

- `SUPPORTED`: há destino canônico e a informação pode ser encaminhada sem perda semântica relevante para o campo.
- `PARTIAL`: há destino, mas normalização, precisão, estado ou distinção relevante pode ser perdida.
- `MISSING`: não há destino canônico adequado.
- `AMBIGUOUS`: há destino, mas a regra de classificação entre categorias não é suficientemente determinística.

O inventário contém **40 campos folha do `Candidate`**: 21 `SUPPORTED`, 13 `PARTIAL` e 6 `AMBIGUOUS`. O mapa inclui ainda 7 lacunas `MISSING` que não entram na contagem de campos atuais do `Candidate`.

## Inventário por camada do contrato

| CAMADA | CONTRATO INSPECIONADO | CAMPOS / ESTRUTURA | OBSERVAÇÃO DE DESTINO |
| --- | --- | --- | --- |
| Extração estruturada | `CandidateResumeExtraction` | os mesmos 40 campos folha do `Candidate`, todos factuais envolvidos por `ResumeFieldEvidence { value, evidence }` | objetivo, resumo profissional, cargo-alvo, status de curso/certificação e estado explícito de item atual não fazem parte do schema |
| Rascunho de importação | `CandidateImportDraft` | 40 campos de conteúdo, `experiences[].is_current` e `issues[]` | retém valores convertidos e avisos; descarta a evidência e, quando a conversão é aceita, não mantém o valor bruto em campo próprio |
| Entrada da aplicação | `CandidateInput` e schemas aninhados | os mesmos 40 campos folha do agregado | exige os campos obrigatórios do domínio e não recebe evidência, valor bruto nem `is_current` |
| Modelo final | `Candidate` e entidades aninhadas | 40 campos folha | não representa objetivo, resumo, cargo-alvo, status de curso/certificação, evidência, valor bruto ou marcador explícito de experiência atual |

No mapa abaixo, “mesmo caminho” significa que o valor percorre o caminho homônimo da extração para o rascunho e pode ser submetido ao `CandidateInput`/`Candidate`. As exceções e perdas são indicadas na própria linha. Coleções e objetos contêineres não entram na contagem de 40; a contagem considera somente campos folha, incluindo campos dentro de itens de coleção.

## Mapa canônico

Em todas as linhas, `SIM` significa que o valor factual precisa estar sustentado por trecho literal do currículo. O Truth Gate verifica isso na extração, mas a evidência não segue para o rascunho nem para o `Candidate`.

| CANONICAL FIELD | DISPLAY LABEL | SECTION ALIASES | SOURCE PATTERN | CURRENT DESTINATION | STATUS | NORMALIZATION | EVIDENCE REQUIRED | REVIEW CONDITION |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal_info.full_name` | Nome completo | cabeçalho, contato, dados pessoais | linha de identificação nominal | mesmo caminho | SUPPORTED | remover apenas espaços de apresentação; não corrigir | SIM | ausente, múltiplos nomes ou texto que pareça título |
| `personal_info.city` | Cidade | localização, contato, dados pessoais | componente explícito de localização | mesmo caminho | SUPPORTED | nenhuma expansão geográfica | SIM | localização composta não separável |
| `personal_info.state` | Estado | localização, contato, dados pessoais | estado/UF explícito | mesmo caminho | SUPPORTED | não expandir nem inferir UF | SIM | sigla com mais de um significado |
| `personal_info.country` | País | localização, contato, dados pessoais | país explícito | mesmo caminho | SUPPORTED | não inferir pelo idioma, cidade ou telefone | SIM | ausente ou apenas implícito |
| `contact_info.email` | E-mail | contato, dados pessoais, cabeçalho | endereço com estrutura de e-mail | mesmo caminho | SUPPORTED | preservar valor literal | SIM | formato inválido ou mais de um endereço sem prioridade |
| `contact_info.phone` | Telefone | contato, dados pessoais, cabeçalho | número explicitamente apresentado como contato | mesmo caminho | SUPPORTED | preservar valor literal; não completar DDI/DDD | SIM | formato incompleto ou múltiplos números |
| `professional_links.linkedin` | LinkedIn | links, contato, redes profissionais | URL ou identificador explícito do LinkedIn | mesmo caminho | SUPPORTED | não construir URL a partir de nome | SIM | rótulo sem destino legível |
| `professional_links.github` | GitHub | links, contato, portfólio | URL ou identificador explícito do GitHub | mesmo caminho | SUPPORTED | não construir URL a partir de nome | SIM | rótulo sem destino legível |
| `professional_links.portfolio` | Portfólio | links, contato, portfólio, site | outra URL profissional declarada | mesmo caminho | SUPPORTED | preservar URL literal | SIM | tipo do link incerto ou vários links não classificados |
| `experiences[].company` | Empresa | experiência profissional, histórico profissional, atuação | organização associada ao mesmo bloco da experiência | mesmo caminho | SUPPORTED | preservar grafia | SIM | empresa e cliente/projeto não distinguíveis |
| `experiences[].role` | Cargo | experiência profissional, histórico profissional, atuação | cargo associado ao mesmo bloco da experiência | mesmo caminho | SUPPORTED | preservar grafia; não promover objetivo a cargo exercido | SIM | cargo ausente ou vários cargos no mesmo período |
| `experiences[].start_date` | Início | experiência profissional, histórico profissional | início literal do período da experiência | mesmo caminho | PARTIAL | aceita `YYYY-MM`, `YYYY-MM-DD` e `MM/YYYY`; dia é descartado | SIM | só ano, texto livre, intervalo não reconhecido ou data inválida |
| `experiences[].end_date` | Fim | experiência profissional, histórico profissional | fim literal ou marcador atual no mesmo período | mesmo caminho; `null` no `Candidate` | PARTIAL | marcadores atual/present/current viram `null`; dia é descartado | SIM | `null` não distingue trabalho atual de data ausente no modelo final |
| `experiences[].activities[].description` | Responsabilidade | experiência profissional, responsabilidades, atividades | ação/tarefa realizada no contexto da experiência | mesmo caminho | AMBIGUOUS | preservar texto literal | SIM | frase também expressa resultado ou não está ligada a uma experiência |
| `experiences[].achievements[].description` | Resultado / conquista | experiência profissional, resultados, conquistas | efeito ou resultado explicitamente alcançado | mesmo caminho | AMBIGUOUS | preservar texto literal; não calcular métricas | SIM | não há resultado explícito ou a frase é apenas atividade |
| `education[].institution` | Instituição | formação, educação, formação acadêmica | instituição no mesmo item da formação | mesmo caminho | SUPPORTED | preservar grafia | SIM | instituição e emissor de curso não distinguíveis |
| `education[].course` | Curso | formação, educação, formação acadêmica | graduação/curso acadêmico no mesmo item | mesmo caminho | SUPPORTED | preservar grafia | SIM | item pode ser curso complementar, não formação acadêmica |
| `education[].status` | Status da formação | formação, educação, formação acadêmica | status explicitamente declarado | mesmo caminho | PARTIAL | somente em andamento, concluído ou interrompido e aliases fechados | SIM | status ausente ou rótulo fora do mapa, como trancado |
| `education[].start_date` | Início da formação | formação, educação, formação acadêmica | início literal do item | mesmo caminho | PARTIAL | mês nos formatos aceitos; dia é descartado | SIM | somente ano ou data não reconhecida |
| `education[].end_date` | Fim da formação | formação, educação, formação acadêmica | fim literal do item | mesmo caminho | PARTIAL | mês nos formatos aceitos; dia é descartado | SIM | previsão não identificada como tal, somente ano ou data não reconhecida |
| `skills[].name` | Competência | competências, habilidades, competências funcionais, soft skills | capacidade profissional, comportamental ou funcional | mesmo caminho | AMBIGUOUS | preservar item literal | SIM | item também puder ser tecnologia ou ferramenta |
| `skills[].level` | Nível da competência | competências, habilidades | nível autodeclarado junto da competência | mesmo caminho | PARTIAL | básico/intermediário/avançado/expert e aliases fechados | SIM | nível implícito, desconhecido ou fora do mapa |
| `technologies[].name` | Tecnologia | competências técnicas, tecnologias, conhecimentos técnicos | linguagem, framework, biblioteca, banco, runtime ou plataforma técnica | mesmo caminho | AMBIGUOUS | lista heurística pode reclassificar itens conhecidos | SIM | item fora da lista ou fronteira com ferramenta/capacidade |
| `technologies[].level` | Nível da tecnologia | competências técnicas, tecnologias | nível autodeclarado junto da tecnologia | mesmo caminho | PARTIAL | mapa fechado de proficiência | SIM | nível inferido por tempo/experiência ou fora do mapa |
| `tools[].name` | Ferramenta | ferramentas, competências técnicas, ambiente | software, serviço ou produto usado para executar trabalho | mesmo caminho | AMBIGUOUS | lista heurística pode reclassificar itens conhecidos | SIM | fronteira com tecnologia/plataforma não definida |
| `tools[].level` | Nível da ferramenta | ferramentas, competências técnicas | nível autodeclarado junto da ferramenta | mesmo caminho | PARTIAL | mapa fechado de proficiência | SIM | nível inferido ou fora do mapa |
| `languages[].name` | Idioma | idiomas, línguas, conhecimentos linguísticos | nome explícito de idioma | mesmo caminho | SUPPORTED | preservar nome literal | SIM | idioma sem item separável |
| `languages[].level` | Proficiência no idioma | idiomas, línguas | nível explicitamente associado ao idioma | mesmo caminho | PARTIAL | básico/intermediário/avançado/fluente/nativo e aliases fechados | SIM | termos como conversacional não estão no mapa |
| `certifications[].name` | Curso / certificação | certificações, cursos, cursos complementares, certifications | nome do item listado | mesmo caminho | AMBIGUOUS | cursos e certificações compartilham a mesma coleção | SIM | nome, provedor e status aparecem concatenados ou tipo é incerto |
| `certifications[].issuer` | Emissor / instituição | certificações, cursos, cursos complementares | provedor explicitamente associado ao item | mesmo caminho | SUPPORTED | heurística reconhece conjunto limitado de provedores | SIM | ausente; status confundido com emissor; provedor fora da lista |
| `certifications[].issue_date` | Data de emissão | certificações, cursos | data completa explicitamente associada ao item | mesmo caminho | PARTIAL | aceita somente `YYYY-MM-DD` | SIM | apenas mês/ano ou ano; não inventar dia |
| `certifications[].expiration_date` | Validade | certificações | data completa de expiração explicitamente associada | mesmo caminho | PARTIAL | aceita somente `YYYY-MM-DD` | SIM | validade ausente, mês/ano ou texto como “sem expiração” |
| `certifications[].credential_id` | ID da credencial | certificações | identificador explicitamente rotulado | mesmo caminho | SUPPORTED | preservar literal | SIM | código sem rótulo ou associação incerta |
| `certifications[].credential_url` | URL da credencial | certificações | URL explicitamente associada à credencial | mesmo caminho | SUPPORTED | preservar literal | SIM | URL genérica do emissor ou associação incerta |
| `projects[].name` | Nome do projeto | projetos, projetos de desenvolvimento, projetos pessoais | título do bloco de projeto | mesmo caminho | SUPPORTED | preservar grafia | SIM | título não separável da descrição |
| `projects[].description` | Descrição do projeto | projetos, projetos de desenvolvimento | uma frase ou bullet literal do projeto | mesmo caminho | SUPPORTED | não resumir, combinar ou reescrever bullets | SIM | ausência de descrição ou texto ligado a outro projeto |
| `projects[].start_date` | Início do projeto | projetos, projetos de desenvolvimento | início literal no bloco | mesmo caminho | PARTIAL | mês nos formatos aceitos; dia é descartado | SIM | só ano ou data não reconhecida |
| `projects[].end_date` | Fim do projeto | projetos, projetos de desenvolvimento | fim literal ou marcador atual no bloco | mesmo caminho | PARTIAL | mês nos formatos aceitos; atual vira `null` | SIM | `null` pode ser atual ou ausente |
| `projects[].technologies[]` | Tecnologias do projeto | projetos, projetos de desenvolvimento | tecnologia citada literalmente dentro do bloco do projeto | mesmo caminho | SUPPORTED | heurística procura apenas lista conhecida no bloco delimitado | SIM | tecnologia aparece apenas em seção global ou limite do bloco é incerto |
| `projects[].url` | URL do projeto | projetos, links, portfólio | URL explicitamente associada ao projeto | mesmo caminho | SUPPORTED | preservar literal | SIM | URL genérica ou associação a projeto incerta |
| `GAP.experiences[].is_current` | Trabalho atual | experiência profissional | marcador literal atual/present/current | `ExperienceDraft.is_current`; não existe no `Candidate` | MISSING | derivado apenas de marcador explícito | SIM | modelo final perde distinção entre atual e fim ausente |
| `GAP.objective` | Objetivo | objetivo, objetivo profissional | texto explicitamente declarado como objetivo | nenhum | MISSING | nenhuma | SIM | não encaminhar para cargo exercido ou resumo |
| `GAP.professional_summary` | Resumo profissional | resumo profissional, perfil, sobre mim, apresentação | parágrafo declarativo sobre o perfil | nenhum | MISSING | nenhuma | SIM | não decompor automaticamente em fatos sem destino |
| `GAP.target_role` | Cargo-alvo | objetivo, cargo pretendido, área de interesse | cargo desejado explicitamente declarado | nenhum | MISSING | nenhuma | SIM | não confundir com cargo já exercido |
| `GAP.certifications[].status` | Status do curso / certificação | cursos, cursos complementares, certificações | concluído, cursando ou equivalente ligado ao item | nenhum | MISSING | nenhuma | SIM | status pode ser confundido com emissor ou descartado |
| `GAP.raw_value` | Valor bruto | todas | valor literal antes da normalização | `ResumeFieldEvidence.value`, depois descartado | MISSING | deve coexistir com o normalizado | SIM | toda conversão que altere formato |
| `GAP.evidence` | Evidência de origem | todas | trecho literal que sustenta o valor | validado em `ResumeFieldEvidence.evidence`, depois descartado | MISSING | normalização apenas de espaços para validação alternativa | SIM | evidência ausente, não literal ou não localizada no texto |

## Regras de mapeamento

1. **Títulos equivalentes.** Comparar rótulo sem diferença de caixa e com espaços periféricos removidos. Aliases ajudam a localizar blocos, mas nunca substituem o significado literal do conteúdo. Um item sob “competências” ainda pode ser tecnologia ou ferramenta.
2. **Experiência.** Manter juntos empresa, cargo, período e bullets do mesmo bloco e preservar a ordem original. Não mover conteúdo entre experiências sem vínculo textual claro.
3. **Atividade versus conquista.** Atividade descreve ação ou responsabilidade; conquista exige efeito explicitamente declarado. Números, causalidade ou impacto não podem ser calculados nem completados. Em dúvida, marcar `AMBÍGUO` para revisão.
4. **Competência, tecnologia e ferramenta.** Competência é capacidade; tecnologia é linguagem, framework, biblioteca, banco, runtime ou plataforma técnica; ferramenta é software, serviço ou produto operacional. A lista heurística atual é limitada e não constitui taxonomia completa.
5. **Cursos e certificações.** Nome, emissor e status só podem ser separados quando cada parte estiver explícita. Status não é emissor. O modelo atual reúne curso e certificação e não tem campo de status.
6. **Tecnologias de projeto.** Associar somente itens presentes no bloco do próprio projeto. Citação apenas em uma lista global não prova uso no projeto.
7. **Datas.** Preservar o valor bruto fora do destino normalizado em uma evolução futura. Atualmente, datas mensais aceitam `YYYY-MM`, `YYYY-MM-DD` e `MM/YYYY`; certificações exigem `YYYY-MM-DD`. Não completar mês ou dia. Formatos não reconhecidos geram revisão e destino `null`.
8. **Ordem e relação.** Preservar ordem de experiências, formações, listas e projetos e manter itens aninhados com seu bloco de origem.
9. **Repetições.** Não deduplicar ocorrências legítimas em experiências ou projetos diferentes. Deduplicação só é segura quando o mesmo item e a mesma evidência representam a mesma ocorrência.
10. **Estados de ausência.** `NÃO ENCONTRADO` significa sem evidência após inspeção; `NÃO APLICÁVEL` exige que a categoria realmente não se aplique; `AMBÍGUO` significa conteúdo presente sem classificação segura; `REVISAR` significa valor extraído com conversão, vínculo ou completude pendente.

## Normalização segura

- O valor bruto deve ser imutável e separado do valor normalizado. O runtime atual não cumpre esse contrato depois da conversão.
- `MM/YYYY` pode virar `YYYY-MM` porque mês e ano estão explícitos.
- `YYYY-MM-DD` pode virar `YYYY-MM` para campos mensais, com registro de que a precisão foi reduzida.
- Atual/present/current pode sinalizar experiência atual; não usar ausência de data final para inferir esse estado.
- Mapas fechados de status e nível podem normalizar apenas aliases documentados. Valores desconhecidos permanecem sem normalização e exigem revisão.
- Não traduzir, corrigir, expandir abreviações, inferir localização, proficiência, conclusão, período, emissor ou tecnologia.

## Contrato de evidência

Estado: **PARTIAL**.

Cada fato extraído usa `{value, evidence}`; o prompt exige literalidade e o Truth Gate confirma que `value` ocorre em `evidence` e que `evidence` ocorre no texto, aceitando uma segunda tentativa com espaços normalizados. O modo best-effort remove valores não sustentados e cria `unsupported_grounding` sem registrar o conteúdo sensível no issue. Porém, a conversão conserva somente o valor e a resposta da API não contém evidência. Assim, revisão posterior não consegue rastrear o campo até o trecho de origem.

## Decisões pendentes para E1-S02

- Definir destino de objetivo, resumo profissional e cargo-alvo sem confundi-los com experiência.
- Definir como preservar valor bruto, valor normalizado e evidência até a revisão.
- Representar explicitamente “trabalho atual” no modelo final ou manter estado equivalente não ambíguo.
- Decidir se cursos e certificações permanecem juntos e como representar status de curso.
- Tornar extensível a taxonomia de competência/tecnologia/ferramenta e a delimitação de blocos de projeto.
- Definir tratamento de datas com apenas ano ou mês/ano para certificações sem inventar precisão.
