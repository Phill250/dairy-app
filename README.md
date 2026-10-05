# Smart Dairy Manager

Layered FastAPI backend (routers → services → repository → schemas → models)
with Postgres/SQLAlchemy, and a Next.js frontend.

## Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your real Postgres credentials

# make sure Postgres is running and the database in DATABASE_URL exists, e.g.:
#   createdb dairy_db

uvicorn app.main:app --reload
```

API docs available at http://localhost:8000/docs

### Training the ML model

```bash
cd backend
python -m app.ml.train_model path/to/kaggle_dataset.csv
```

This writes `app/ml/milk_yield_model.pkl`, which `MLService` picks up
automatically on the next server restart. If no model file exists yet,
the app falls back to a simple heuristic — nothing breaks.

## Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Visit http://localhost:3000

## Project layout

```
backend/
  app/
    core/          # config, db session
    models/        # SQLAlchemy ORM models
    schemas/       # Pydantic request/response contracts
    repository/     # raw DB queries only
    services/       # business logic (advice rules, ML orchestration)
    routers/        # thin HTTP endpoints
    ml/             # training script + saved model artifact
frontend/
  app/             # Next.js App Router pages
  components/      # LogForm, LogsTable
  lib/api.ts       # typed fetch client to the backend
```

## Next steps to consider

- Add Alembic migrations instead of `Base.metadata.create_all` once the schema stabilizes.
- Add `days_in_milk`, `breed`, `lactation_number` columns if your Kaggle dataset has them — richer features will meaningfully improve prediction quality.
- Add a `/api/logs/history` endpoint feeding recent entries into the model as a rolling-average feature.
- Add auth if multiple farmers/farms will use the same deployment.
