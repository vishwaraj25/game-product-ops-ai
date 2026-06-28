# Backend

FastAPI service for the AI-native product operations foundation.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Health Checks

- `GET /health`
- `GET /health/db`

## Database

Run migrations:

```bash
alembic upgrade head
```

Seed the Project Eclipse simulation:

```bash
python -m app.seed.project_eclipse
```
