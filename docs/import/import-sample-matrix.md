# Matriz de amostras da importação

## Estado da cobertura

**PARCIAL — AGUARDANDO NOVAS AMOSTRAS**

Esta matriz separa o que foi observado na descrição da amostra de referência, o que foi encontrado apenas no código e o que foi exercitado em documento real. “Coberto pelo código” não equivale a “validado empiricamente”, e extração textual bem-sucedida não equivale a importação estruturada correta.

## Registro de amostras

| ID | ORIGEM | FORMATO | MATERIAL ANALISADO | SEÇÕES / PADRÕES DISPONÍVEIS | RESULTADO |
| --- | --- | --- | --- | --- | --- |
| `S-REF-01` | referência descrita na especificação | não informado | somente inventário anônimo de seções | objetivo; resumo profissional; competências técnicas e funcionais; experiência; formação e idiomas; projetos; cursos complementares; contato e links | cobertura estrutural parcial; sem validação por campo |
| `S-02` | arquivo local ignorado pelo Git | PDF textual, 3 páginas | somente saída agregada do leitor, sem persistir texto | títulos reconhecidos de objetivo, resumo, experiência, competências, projetos e cursos/certificações | texto extraído; pipeline estruturado não executado |
| `S-03` | arquivo local ignorado pelo Git | PDF textual, 3 páginas | somente saída agregada do leitor, sem persistir texto | títulos reconhecidos de resumo, experiência e competências | texto extraído; pipeline estruturado não executado |

Os arquivos originais de `S-02` e `S-03` permanecem locais e ignorados por `output/`; seus nomes e conteúdos não foram incorporados à documentação. O arquivo original de `S-REF-01` não foi localizado.

## Variações cobertas

| VARIAÇÃO | OBSERVADA EM AMOSTRA | COBERTA NO CÓDIGO | SITUAÇÃO |
| --- | --- | --- | --- |
| Objetivo | sim, por descrição | não | GAP confirmado |
| Resumo profissional | sim, por descrição | não | GAP confirmado |
| Competências técnicas e funcionais separadas | sim, por descrição | parcialmente | classificação precisa de amostra real |
| Experiência com empresa/cargo/período/bullets | categoria indicada | sim | valores e layouts não avaliados |
| Formação e idiomas próximos | categoria indicada | sim | associação visual não avaliada |
| Projetos de desenvolvimento | sim, por descrição | sim | limites de bloco não avaliados na amostra |
| Cursos complementares | sim, por descrição | sim, com heurística específica | emissores e status não avaliados na amostra |
| Contato e links profissionais | sim, por descrição | sim | formatos concretos não avaliados |
| Datas `YYYY-MM`, `YYYY-MM-DD`, `MM/YYYY` | não | sim | somente inspeção estática |
| Intervalo `MM/YYYY - Atual/Present/Current` | não | sim | somente inspeção estática |
| Níveis PT/EN previstos nos mapas fechados | não | sim | somente inspeção estática |
| PDF textual | sim, em `S-02` e `S-03` | sim | leitor executado com extração não vazia nas duas amostras |
| DOCX com parágrafos e tabelas | não | sim | leitor inspecionado, sem amostra executada |

## Aliases registrados

| CATEGORIA CANÔNICA | ALIASES OBSERVADOS NA DESCRIÇÃO | ALIASES ADICIONAIS PRESENTES NO CÓDIGO/CONTRATO |
| --- | --- | --- |
| objetivo | objetivo | objetivo profissional; cargo pretendido; área de interesse (pendentes de confirmação empírica) |
| resumo | resumo profissional | perfil; sobre mim; apresentação (pendentes de confirmação empírica) |
| competências | competências técnicas e funcionais | competências; habilidades; soft skills; conhecimentos técnicos |
| experiência | experiência profissional | histórico profissional; atuação; responsabilidades; atividades; resultados; conquistas |
| formação | formação | educação; formação acadêmica |
| idiomas | idiomas | línguas; conhecimentos linguísticos |
| projetos | projetos de desenvolvimento | projetos; projetos pessoais; `PROJETO:` |
| cursos/certificações | cursos complementares | cursos; certificações; certifications |
| contato/links | contato e links profissionais | dados pessoais; links; portfólio; site |

Aliases não observados diretamente em `S-REF-01` são hipóteses de contrato e devem ser confirmados com novas amostras antes de orientar heurísticas de produção.

## Casos ainda não cobertos

- PDF textual com layout conhecido de uma coluna e de múltiplas colunas; as amostras locais não tiveram o layout classificado.
- PDF escaneado (limitação conhecida; OCR fora do escopo).
- DOCX com texto simples, tabelas, cabeçalho/rodapé e caixas de texto.
- Currículo sem títulos de seção ou com títulos em inglês.
- Mais de um cargo na mesma empresa e períodos sobrepostos.
- Datas somente com ano, períodos abertos e datas previstas.
- Atividades e conquistas misturadas no mesmo bullet.
- Competências que podem ser simultaneamente tecnologia, ferramenta ou capacidade.
- Curso sem emissor, certificação com credencial, curso em andamento e item com status concatenado.
- Vários projetos, tecnologias globais versus locais e URLs compartilhadas.
- Campos repetidos, múltiplos contatos/links e ocorrências legítimas duplicadas.
- Idiomas e níveis fora do mapa fechado.
- Conteúdo ausente, não aplicável e presente porém impossível de classificar.

## Protocolo para novas amostras

1. Atribuir identificador sequencial anônimo (`S-02`, `S-03`, ...); não usar nome ou hash reversível do arquivo como identificador público.
2. Registrar apenas formato, estrutura, categorias presentes, resultado por campo e motivo de revisão.
3. Não copiar arquivo, nome, contato, endereço, identificadores, texto integral de experiências/projetos ou dados de terceiros.
4. Distinguir `ENCONTRADO`, `REVISAR`, `NÃO ENCONTRADO` e `AMBÍGUO`; usar `NÃO APLICÁVEL` somente com justificativa.
5. Preservar ordem, vínculo entre itens e valor bruto durante a análise; qualquer exemplo documental deve ser sintético.
6. Atualizar esta matriz e a baseline sem alterar o extrator até que uma sprint posterior autorize implementação.
