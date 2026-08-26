# Resume AI / Currículo ATS

Aplicação web para importar ou preencher um currículo, compará-lo com uma vaga e gerar uma versão otimizada para sistemas ATS. O projeto prioriza rastreabilidade: informações do candidato precisam ter evidência no currículo e a otimização não deve inventar experiência.

## Objetivo

Transformar os dados de um candidato e a descrição de uma vaga em uma análise clara de compatibilidade, com critérios encontrados, lacunas, critérios não avaliáveis, score, cobertura e currículo otimizado para download em DOCX ou PDF.

## Principais características

- Importa currículo em PDF ou DOCX e preenche o formulário para revisão.
- Extrai critérios da vaga, realiza matching e calcula score e cobertura.
- Separa lacunas (`NOT_MATCHED`) de critérios não avaliáveis com segurança (`UNSUPPORTED`).
- Gera currículo otimizado em DOCX e PDF a partir dos dados do candidato.
- Mantém o currículo e os avisos de revisão no armazenamento local do navegador.
- Usa gates de grounding, proveniência e Truth Gate para impedir que conteúdo sem evidência se torne experiência do candidato.

## Stack

| Camada | Tecnologias principais |
| --- | --- |
| Backend | Python 3.13, FastAPI, Uvicorn, Pydantic, OpenAI SDK |
| Documentos | python-docx, ReportLab e pypdf |
| Frontend | Next.js 16.3.3, React 19.2.8, TypeScript 5.7.2 |
| Estilos e qualidade | Tailwind CSS, PostCSS, ESLint 9.39.5 e eslint-config-next 16.3.3 |

## Arquitetura

O backend usa módulos organizados por domínio e um bootstrap como composição das dependências:

```text
src/resume_ai/
├── core/              # configuração e exceções comuns
├── integrations/      # cliente e configuração da IA
├── interfaces/        # API FastAPI e CLI
├── modules/
│   ├── candidate/     # currículo, importação e grounding
│   ├── documents/     # geração DOCX/PDF
│   ├── jobs/          # vaga, critérios e Truth Gate da vaga
│   ├── matching/      # matching, score, gaps e proveniência
│   ├── optimization/  # plano e otimização grounded
│   └── translation/   # tradução assistida por IA
└── bootstrap.py        # composição dos casos de uso
```

As regras e entidades ficam no domínio; casos de uso e orquestração ficam na aplicação; integrações externas ficam na infraestrutura; a API HTTP fica em `interfaces`. O frontend em `frontend/` é uma aplicação Next.js que expõe Route Handlers e encaminha chamadas ao FastAPI no servidor.

## Pré-requisitos

- Git;
- Python 3.13 ou compatível com `>=3.13`;
- Node.js **24.19.0**;
- npm **11.17.0**.

No frontend, `frontend/.nvmrc` é a referência operacional da versão do Node. `frontend/package.json` declara a mesma versão em `engines.node`, e `frontend/.npmrc` usa `engine-strict=true`.

## Instalação

### Backend

```powershell
git clone https://github.com/kazuyanishi/curriculo-ats.git
cd curriculo-ats

python -m venv .venv
```

Ative o ambiente virtual conforme seu terminal:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

```bash
# Linux/macOS
source .venv/bin/activate
```

Instale as dependências de desenvolvimento:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Frontend

```powershell
cd frontend
npm ci
```

`npm ci` é o caminho recomendado porque instala exatamente a árvore registrada em `package-lock.json`.

## Configuração

### OpenAI / IA

Os fluxos de importação de currículo e análise de vaga exigem estas variáveis no processo do backend:

```text
RESUME_AI_API_KEY
RESUME_AI_MODEL
```

Exemplos, sempre com valores próprios e nunca versionando chaves:

```powershell
# PowerShell
$env:RESUME_AI_API_KEY = "sua-chave"
$env:RESUME_AI_MODEL = "seu-modelo"
```

```cmd
:: Windows CMD
set RESUME_AI_API_KEY=sua-chave
set RESUME_AI_MODEL=seu-modelo
```

```bash
# Linux/macOS
export RESUME_AI_API_KEY="sua-chave"
export RESUME_AI_MODEL="seu-modelo"
```

O backend lê variáveis do processo; ele **não** carrega arquivos `.env` automaticamente. `RESUME_AI_ENV` é opcional e aceita `development`, `test` ou `production` (o padrão é `development`).

Para o frontend, `RESUME_AI_API_URL` é opcional e define a URL do FastAPI; o padrão é `http://127.0.0.1:8000`. O Next.js carrega `frontend/.env.local`, portanto é possível criar esse arquivo a partir do exemplo:

```powershell
cd frontend
Copy-Item .env.example .env.local
```

## Executando localmente

Use dois terminais, ambos a partir da raiz do repositório.

**Terminal 1 — backend**

```powershell
.venv\Scripts\Activate.ps1
$env:RESUME_AI_API_KEY = "sua-chave"
$env:RESUME_AI_MODEL = "seu-modelo"
python -m uvicorn resume_ai.interfaces.api.app:create_app --factory --reload
```

O backend inicia em <http://127.0.0.1:8000>. A documentação interativa está em <http://127.0.0.1:8000/docs>.

**Terminal 2 — frontend**

```powershell
cd frontend
npm ci
npm run dev
```

Abra <http://localhost:3000>.

## API HTTP

O FastAPI expõe os endpoints sob o prefixo `/api/v1`:

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Verifica se a API está disponível. |
| `POST` | `/api/v1/candidate/import` | Recebe um PDF ou DOCX (até 5 MiB), extrai e estrutura um rascunho de Candidate. |
| `POST` | `/api/v1/analyze` | Executa extração de critérios, matching, score, gaps e otimização grounded. |
| `POST` | `/api/v1/documents/docx` | Gera um currículo DOCX. |
| `POST` | `/api/v1/documents/pdf` | Gera um currículo PDF. |

O frontend chama seus Route Handlers em `/api/*`; eles encaminham as requisições ao FastAPI. Erros de configuração da IA retornam `503`; falhas de integração externa retornam `502`; e conteúdo ou dados que não passam pela validação necessária retornam `422` quando aplicável.

## Fluxo da aplicação

1. Importe um currículo PDF/DOCX ou preencha o Candidate manualmente.
2. Revise os dados importados e eventuais avisos.
3. Informe a descrição da vaga.
4. A IA estrutura critérios da vaga; o pipeline executa matching, score, cobertura e análise de gaps.
5. A otimização grounded reorganiza apenas conteúdo sustentado por evidência do Candidate.
6. Consulte correspondências, lacunas e critérios não avaliáveis; então baixe o Candidate otimizado em DOCX ou PDF.

`MATCHED` representa um critério encontrado. `NOT_MATCHED` representa um critério avaliado e ausente. `UNSUPPORTED` significa que a avaliação não é segura com os dados disponíveis e não é tratado automaticamente como lacuna. O score usa critérios avaliáveis; a cobertura mostra a parcela de critérios avaliáveis sobre o total.

## Grounding e Truth Gates

O projeto não usa informações da vaga como prova de experiência do candidato. Evidências vêm do Candidate, o matching preserva a proveniência dessas evidências e a otimização só utiliza conteúdo vinculado a elas. Truth Gates rejeitam extrações ou propostas sem suporte suficiente, protegendo o currículo contra afirmações inventadas.

## Testes e qualidade

Backend:

```powershell
python -m ruff check .
python -m compileall -q src tests
python -m pip check
python -m pytest
```

A baseline atual é **1245 testes passando**.

Frontend:

```powershell
cd frontend
npm ci
npm audit
npm audit --omit=dev
npx tsc --noEmit
npm run lint
npm run build
```

A árvore atual deve retornar **0 vulnerabilities** nos dois comandos de audit.

## CI e segurança

O GitHub Actions executa em `ubuntu-24.04`:

- backend: Ruff, compileall, `pip check` e pytest;
- frontend: verificação da toolchain, `npm ci`, security audit, TypeScript, ESLint e build;
- etapa final: `CI Success` após backend e frontend.

O Node 24.19.0 é baixado da distribuição oficial com verificação SHA-256. As actions usadas pelo workflow são pinadas por SHA e o checkout não mantém credenciais persistentes. Dependabot verifica semanalmente dependências de GitHub Actions e npm do frontend; não há auto-merge configurado.

## Estado atual

Estão implementados matching factual com proveniência, otimização grounded de activities e achievements de experiências com proveniência própria, Truth Gates semânticos, vínculo entre fontes e alvos da otimização e priorização grounded de itens independentes. O projeto não inclui autenticação, banco de dados, histórico de análises, candidatura automática a vagas ou ranking externo.

## Licença

Ainda não há um arquivo de licença definido no repositório.
