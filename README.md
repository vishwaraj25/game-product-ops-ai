# Game Product Ops AI

Autonomous AI product operations foundation for game Product Managers.

This repository is organized as an AI-native product foundation:

- `frontend/` - Next.js product console
- `backend/` - FastAPI service for future AI orchestration and workflows
- `docs/` - product and architecture notes
- `data/` - future synthetic source data

Sprint 1 only sets up the runnable development environment. It does not include
AI logic, investigation workflows, planners, tools, or business logic.

## Prerequisites

- Docker
- Node.js 20+
- pnpm
- Python 3.10+

## Environment

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

## Start PostgreSQL

```bash
docker compose up -d postgres
```

## Start Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health checks:

- `http://localhost:8000/health`
- `http://localhost:8000/health/db`

## Start Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000`.
