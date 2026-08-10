# Resume AI

AI-assisted ATS resume analyzer and optimizer, organized as a modular monolith.
The project targets Python >= 3.13 and is currently in its bootstrap phase.

## Setup (Windows / PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run

```powershell
python -m resume_ai.main
```

## Tests

```powershell
python -m pytest
```

## Lint

```powershell
python -m ruff check .
```

## Roadmap

Candidate, Jobs, Matching, Optimization, Translation, and Documents will be
developed in later iterations.
