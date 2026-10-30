# Currículo ATS

Aplicação web para importar e editar currículos, comparar o perfil do candidato
com uma vaga e gerar documentos em DOCX ou PDF.

O matching diferencia critérios encontrados, ausentes e não avaliáveis. A
otimização preserva a origem das informações do candidato e rejeita conteúdo
sem evidência no currículo.

## Recursos

- importação de currículos em PDF e DOCX;
- formulário para revisão dos dados importados;
- extração estruturada dos critérios de uma vaga;
- matching com score, cobertura e análise de lacunas;
- geração de currículo em DOCX e PDF;
- validação de proveniência durante a extração e a otimização;
- armazenamento local do formulário no navegador.

## Tecnologias

| Componente | Tecnologias |
|---|---|
| Backend | Python 3.13, FastAPI, Pydantic e OpenAI SDK |
| Documentos | python-docx, ReportLab e pypdf |
| Frontend | Next.js 16, React 19 e TypeScript 5 |
| Qualidade | pytest, Ruff, Vitest e ESLint |

## Estrutura

```text
.
├── src/resume_ai/       # backend Python
│   ├── core/            # configuração e exceções comuns
│   ├── integrations/    # integrações externas
│   ├── interfaces/      # API HTTP e CLI
│   └── modules/         # regras organizadas por domínio
├── tests/               # testes do backend
├── frontend/            # aplicação Next.js
├── docs/                # documentação técnica
└── pyproject.toml       # pacote e ferramentas do backend
```

O backend segue uma separação entre domínio, aplicação, infraestrutura e
interfaces. O frontend possui dependências e configuração próprias em
`frontend/package.json`.

## Pré-requisitos

- Python 3.13 ou superior;
- Node.js na versão indicada em `frontend/.nvmrc`;
- npm compatível com a versão do Node.js;
- Git.

## Instalação

Depois de clonar o repositório, prepare o backend na raiz:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

No Windows PowerShell, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

Instale o frontend separadamente:

```bash
cd frontend
npm ci
```

## Configuração

Os fluxos que usam modelos externos leem estas variáveis no processo do
backend:

```text
RESUME_AI_API_KEY
RESUME_AI_MODEL
```

Não grave chaves no repositório. Defina-as somente no ambiente local ou no
gerenciador de segredos da implantação.

Exemplo para Linux e macOS:

```bash
export RESUME_AI_API_KEY="sua-chave"
export RESUME_AI_MODEL="seu-modelo"
```

Exemplo para PowerShell:

```powershell
$env:RESUME_AI_API_KEY = "sua-chave"
$env:RESUME_AI_MODEL = "seu-modelo"
```

O backend não carrega arquivos `.env` automaticamente. No frontend, copie
`frontend/.env.example` para `frontend/.env.local` quando precisar alterar a
URL do backend.

## Execução local

Inicie o backend a partir da raiz:

```bash
python -m uvicorn resume_ai.interfaces.api.app:create_app --factory --reload
```

A API estará disponível em <http://127.0.0.1:8000> e a documentação interativa
em <http://127.0.0.1:8000/docs>.

Em outro terminal, inicie o frontend:

```bash
cd frontend
npm run dev
```

A interface estará disponível em <http://localhost:3000>.

## API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/v1/health` | Verifica a disponibilidade da API |
| `POST` | `/api/v1/candidate/import` | Importa um currículo PDF ou DOCX |
| `POST` | `/api/v1/analyze` | Analisa o candidato em relação à vaga |
| `POST` | `/api/v1/documents/docx` | Gera o currículo em DOCX |
| `POST` | `/api/v1/documents/pdf` | Gera o currículo em PDF |

## Matching

Cada critério recebe um dos seguintes estados:

- `MATCHED`: o currículo contém uma correspondência comprovada;
- `NOT_MATCHED`: o critério foi avaliado e não foi encontrado;
- `UNSUPPORTED`: os dados disponíveis não permitem uma decisão segura.

O score considera apenas critérios avaliáveis. A cobertura indica qual parcela
do total pôde ser avaliada.

## Testes

Backend:

```bash
python -m ruff check .
python -m compileall -q src tests
python -m pip check
python -m pytest
```

Frontend:

```bash
cd frontend
npm test
npx tsc --noEmit
npm run lint
npm run build
npm audit
```

O workflow em `.github/workflows/ci.yml` executa as verificações principais em
pushes e pull requests para `master`.

## Dados locais

Currículos, documentos gerados, arquivos de ambiente e diretórios de trabalho
local são ignorados pelo Git. Antes de publicar qualquer alteração, confirme os
arquivos preparados com:

```bash
git diff --cached --name-only
```
