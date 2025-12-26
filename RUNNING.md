# Running the Curious Concierge Backend (Day 1–2 Build)

Follow these steps to set up and run the stack from a clean Windows machine.

## 1. Prerequisites
1. **Install Docker Desktop** and ensure it is running.
2. **Install Python 3.11+** and add it to your PATH.

## 2. Clone / Extract

(Adjust paths if needed, but keep the relative structure.)

## 3. Environment Setup
In terminal navigate to the project directory and run:
```powershell
copy .env.example .env
```
Edit `.env` to fill in API keys later (OPENAI, ASSEMBLYAI, etc.). For local testing keep `POSTGRES_HOST=localhost`.

## 4. Virtual Environment & Dependencies
In terminal navigate to the project directory and run:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Infrastructure (Postgres, Redis, Qdrant)
```powershell
docker compose -f docker\docker-compose.yml up -d
```
This pulls and starts all services. Verify with `docker ps`.

## 6. Database Migration
Ensure the venv is active, then:
```powershell
alembic upgrade head
```
This creates the `rss_feeds`, `episodes`, and `documents` tables in Postgres.

## 7. Run FastAPI Backend
```powershell
uvicorn app.main:app --reload --port 8000
```
If port 8000 is blocked, pick another port (`--port 8100`). Visit:
```
http://127.0.0.1:8000/health
```
You should see JSON similar to:
```json
{
  "status": "ok",
  "environment": "development",
  "services": {
    "postgres": "localhost",
    "redis": "redis",
    "qdrant": "qdrant"
  }
}
```

## 8. Stopping Services
- Stop the FastAPI server: `Ctrl+C` in the terminal.
- Stop Docker services when done:
  ```powershell
  docker compose -f docker\docker-compose.yml down
  ```

## Notes
- Keep Docker running whenever you interact with the backend; it depends on Postgres/Redis/Qdrant.
- For Day 3+ tasks (Docling, embeddings, Celery workers, etc.), additional services and configs will be added later—this file covers the current baseline only.
