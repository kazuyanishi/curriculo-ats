# Resume AI

Resume AI é um analisador de currículos para vagas com foco em ATS e rastreabilidade. A IA extrai critérios da vaga; o Truth Gate exige evidência literal; matching, score e coverage são determinísticos; gaps ficam separados de critérios `unsupported`; e a otimização apenas reorganiza fatos existentes. DOCX e PDF são gerados a partir dos dados reais do Candidate. O sistema não garante contratação.

## Requisitos

- Python >= 3.13
- Node.js e npm

## Instalação do backend

No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Configure as variáveis reais usadas pelo backend no mesmo terminal:

```powershell
$env:RESUME_AI_API_KEY = "your-key-here"
$env:RESUME_AI_MODEL = "gpt-5-mini"
```

A chave fica somente no backend. Nunca use `NEXT_PUBLIC_` para segredos.

## Executar

Backend:

```powershell
uvicorn resume_ai.interfaces.api.app:create_app --factory --reload
```

API: http://127.0.0.1:8000 — Swagger: http://127.0.0.1:8000/docs

Frontend, em outro terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Frontend: http://localhost:3000. O browser chama apenas os Route Handlers do Next.js (`/api/*`); eles encaminham as requisições ao FastAPI no servidor.

## Fluxo do produto

1. Preencha o Candidate.
2. Cole a descrição da vaga.
3. Analise a compatibilidade.
4. Consulte score, coverage, correspondências, lacunas e critérios não avaliáveis.
5. Baixe o currículo otimizado em DOCX ou PDF.

`MATCHED` é um critério encontrado; `NOT_MATCHED` é um critério avaliado e ausente; `UNSUPPORTED` não pôde ser avaliado com segurança e não é automaticamente uma lacuna. Score considera critérios avaliáveis; coverage mostra a proporção de critérios avaliáveis no total.

## Arquitetura

```text
Next.js / TypeScript
        ↓
Route Handlers
        ↓
FastAPI
        ↓
Application
        ↓
Domain
        ↓
Infrastructure
```

O domínio contém regras, a camada de aplicação orquestra casos de uso e a infraestrutura integra AI e documentos. A interface HTTP expõe os contratos sem colocar a chave de API no browser.

## Testes

Backend:

```powershell
python -m pytest -q
python -m ruff check src tests
python -m compileall -q src tests
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Limitações do MVP

Não há autenticação, histórico, banco de dados, upload automático ou persistência. O Candidate é preenchido manualmente, requisitos complexos podem resultar em `unsupported` e a qualidade da extração depende da descrição fornecida. A IA é usada para extrair critérios da vaga, não para inventar fatos do Candidate.

## Roteiro E2E local

Use dados fictícios, como Jane Doe, `jane@example.com`, uma experiência de Backend Developer e Python. Use uma vaga como:

```text
We are looking for a Backend Developer.
Python is required.
Docker is required.
```

Confirme o loading, resultado, score, coverage, matches, gaps separados de `unsupported`, e os downloads DOCX/PDF. Teste também descrição vazia e FastAPI desligado; a interface deve preservar o formulário e mostrar erro amigável. Confira o layout em aproximadamente 1366px e 390px.
