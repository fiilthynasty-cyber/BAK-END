# AI Lead Vacuum

AI Lead Vacuum is a starter monorepo for lead discovery, scoring, notifications, and subscription workflows.

## Structure

- `backend/`: API and business logic
- `frontend/`: React client application
- `worker/`: background queue and scraping workers
- `ai_models/`: model-specific modules

## Quick Start

1. Start backend API:

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

2. Start frontend app:

```bash
cd frontend
npm install
npm run dev
```

3. Optional worker test:

```bash
cd worker
python scraper_worker.py
```

## API Snapshot

- `GET /health`
- `GET /leads/`
- `POST /leads/`
- `GET /leads/{lead_id}`
- `PUT /leads/{lead_id}`
- `DELETE /leads/{lead_id}`
