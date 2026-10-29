# Linha de base da importação de candidato

## Estado

**PARCIAL — AGUARDANDO NOVAS AMOSTRAS**

A inspeção estática do runtime está completa para o branch atual. A avaliação empírica continua parcial: o arquivo bruto do currículo de referência não está disponível, mas dois PDFs locais e ignorados pelo Git permitiram validar a etapa de extração textual. A especificação fornece apenas uma descrição anônima das seções da referência, registrada como `S-REF-01`.

## Método

1. Preservação do estado inicial do Git e leitura do README.
2. Inventário dos schemas `CandidateResumeExtraction`, `CandidateImportDraft`, `CandidateInput` e do agregado `Candidate`.
3. Rastreamento do fluxo leitor → IA estruturada → heurísticas → Truth Gate → conversão → API → frontend.
4. Inspeção dos testes existentes como documentação executável, sem executá-los conforme a restrição da sprint.
5. Comparação por categoria com as seções descritas para `S-REF-01`, sem reproduzir conteúdo pessoal.
6. Execução isolada do `PdfResumeTextExtractor` sobre duas amostras locais, sem IA, persistência de texto extraído ou registro de valores pessoais.

## Amostras

| ID ANÔNIMO | MATERIAL DISPONÍVEL | FORMATO | USO NESTA BASELINE | LIMITAÇÃO |
| --- | --- | --- | --- | --- |
| `S-REF-01` | descrição estrutural na especificação | não informado | cobertura de categorias e aliases | sem arquivo, texto, valores ou resultado de importação |
| `S-02` | currículo local ignorado pelo Git | PDF textual, 3 páginas | validação do leitor PDF | extração concluída; importação estruturada não executada |
| `S-03` | currículo local ignorado pelo Git | PDF textual, 3 páginas | validação do leitor PDF em segunda variação de idioma/conteúdo | extração concluída; importação estruturada não executada |

Os arquivos de `S-02` e `S-03` permanecem fora do Git sob uma regra existente de `.gitignore`. Nenhum nome, contato, endereço, identificador ou trecho pessoal foi copiado para a documentação.

## Linha de base quantitativa do contrato

| MEDIDA | RESULTADO |
| --- | ---: |
| Campos folha atuais do `Candidate` inventariados | 40 |
| `SUPPORTED` | 21 |
| `PARTIAL` | 13 |
| `AMBIGUOUS` | 6 |
| Lacunas adicionais `MISSING` no mapa | 7 |
| Campos de objetivo, resumo profissional ou cargo-alvo com destino | 0 de 3 |
| Campos factuais da extração com wrapper de evidência | todos |
| Campos do rascunho/API que preservam evidência | 0 |

As 40 linhas de campos atuais se distribuem em 21 `SUPPORTED`, 13 `PARTIAL` e 6 `AMBIGUOUS`. As 7 linhas `MISSING` são lacunas adicionais e, por não existirem no `Candidate`, não integram o denominador de 40.

Esses números medem o contrato e o destino atual, não acurácia da IA. A execução isolada do leitor PDF comprova apenas que houve texto extraível; sem configuração de IA não é possível calcular taxa de campos encontrados ou corretamente mapeados.

## Baseline por categoria

| CATEGORIA | PREVISTA NO MODELO | INDICADA EM `S-REF-01` | COMPORTAMENTO ATUAL OBSERVÁVEL NO CÓDIGO | ESTADO |
| --- | --- | --- | --- | --- |
| Informações pessoais e localização | sim | não confirmável pelo resumo | quatro campos; todos obrigatórios no `Candidate`, opcionais na extração e rascunho | PARTIAL |
| Contato | sim | sim | e-mail e telefone têm destino; validação formal de e-mail ocorre no `Candidate`, não no rascunho | SUPPORTED |
| Links profissionais | sim | sim | LinkedIn, GitHub e portfólio têm destinos opcionais | SUPPORTED |
| Objetivo | não | sim | conteúdo fica sem destino | MISSING |
| Resumo profissional | não | sim | conteúdo fica sem destino | MISSING |
| Cargo-alvo | não | possível dentro de objetivo | não há campo; não pode ser tratado como cargo exercido | MISSING |
| Experiências | sim | sim | empresa, cargo, período, atividades e conquistas; datas inválidas viram issue | PARTIAL |
| Atividades e resultados | sim, separados | sim, em experiência | separação depende de interpretação; ambos preservam texto literal após extração | AMBIGUOUS |
| Formação | sim | sim | instituição, curso, status e datas; status aceita três valores canônicos | PARTIAL |
| Competências | sim | sim | destino existe, mas classificação disputa itens com tecnologias e ferramentas | AMBIGUOUS |
| Tecnologias | sim | sim | destino existe; heurística recupera uma lista fixa de termos em qualquer linha | AMBIGUOUS |
| Ferramentas | sim | sim | destino existe; heurística usa lista fixa e remove itens equivalentes de skills/technologies | AMBIGUOUS |
| Idiomas | sim | sim | nome tem destino; nível usa enum fechado | PARTIAL |
| Cursos complementares | somente na coleção de certificações | sim | heurística lê bullets sob quatro títulos; status não tem destino | PARTIAL |
| Certificações | sim | não distinguível do resumo | nome/emissor/datas/credencial; emissor é obrigatório no modelo final | PARTIAL |
| Projetos | sim | sim | nome, uma descrição literal, período, tecnologias e URL; tecnologia deve ocorrer no bloco | PARTIAL |

## Fluxo e comportamento atuais

1. A API aceita somente extensão PDF ou DOCX e no máximo 5 MiB.
2. PDF usa `pypdf` e DOCX usa `python-docx`; texto vazio ou documento ilegível retorna 422.
3. O texto integral é enviado ao cliente estruturado de IA com schema fechado (`extra=forbid`).
4. O prompt proíbe inferência, tradução, correção e resumo e exige valor e evidência literais.
5. Heurísticas posteriores reclassificam termos de listas fixas, recuperam cursos em bullets e tecnologias de projetos.
6. O Truth Gate valida grounding; no modo best-effort remove o campo não sustentado e inclui issue sem expor o valor.
7. A conversão normaliza datas, status e níveis; valor não suportado vira `null` e issue com `raw_value`.
8. A API retorna rascunho sem evidência. O frontend preenche strings vazias para campos obrigatórios ausentes e apresenta issues para revisão.
9. `ExperienceDraft.is_current` diferencia marcador atual de data final ausente, mas o `Candidate` reduz ambos a data final vazia/nula após a edição.

## Conteúdo sem destino ou com risco de perda

- Objetivo, resumo profissional e cargo-alvo.
- Status de curso/certificação.
- Valor bruto depois que uma normalização é aceita.
- Evidência e proveniência após o Truth Gate.
- Precisão de dia em datas mensais.
- Distinção persistente entre experiência atual e fim não encontrado.
- Datas expressas apenas por ano e datas de certificação sem dia.

## Riscos de classificação incorreta

- Listas fixas podem classificar um termo encontrado fora da seção apropriada como tecnologia/ferramenta global.
- A heurística de cursos considera bullets e pode escolher a segunda parte como emissor quando o provedor não é conhecido.
- O limite de bloco de projeto reconhece poucos cabeçalhos e pode abranger conteúdo adjacente.
- Atividade e conquista não possuem regra determinística no runtime além da orientação ao modelo.
- Curso complementar e certificação são agregados na mesma coleção.
- A normalização de espaços permite validar evidência equivalente após mudanças de quebra de linha, mas essa relação não é exposta ao revisor.

## Limitações dos leitores

### PDF

- Não há OCR; PDF escaneado sem camada de texto retorna “sem texto extraível”.
- Ordem de leitura, colunas, cabeçalhos/rodapés, ligaduras e tabelas dependem do `pypdf`.
- PDF criptografado é rejeitado.

### DOCX

- São lidos parágrafos e tabelas na ordem de `iter_inner_content`.
- Células são concatenadas por linha, sem preservar estrutura tabular ou associação de colunas.
- Conteúdo em imagens não tem OCR; relações complexas de layout não são representadas.

### Ambos

- Não há modelo explícito de página, posição, coluna ou bloco visual.
- Imagens e currículos escaneados estão fora do escopo desta sprint.

## Importação automática

**NÃO EXECUTADA — CONFIGURAÇÃO INDISPONÍVEL.** As variáveis de IA necessárias não estavam disponíveis. Nenhuma configuração ou credencial foi criada, alterada ou registrada. Somente o leitor PDF foi executado localmente sobre `S-02` e `S-03`; o pipeline estruturado, as heurísticas, o Truth Gate e a conversão não foram executados com essas amostras. O arquivo bruto de `S-REF-01` segue indisponível.

## Condição para completar a baseline empírica

Fornecer ao menos uma amostra anonimizável em DOCX e amostras com layout em colunas/tabela e variações de datas, cursos, níveis e projetos. Quando houver configuração segura de IA, executar o pipeline completo sobre amostras locais. Para cada amostra, registrar apenas presença, destino, estado e motivo de revisão; nunca armazenar o arquivo ou conteúdo identificável no Git.
