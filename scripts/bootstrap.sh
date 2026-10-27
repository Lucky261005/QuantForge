#!/usr/bin/env bash
# One-shot local dev setup: backend venv + deps + migrations, frontend deps.
# Usage: ./scripts/bootstrap.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Backend: creating virtualenv and installing dependencies"
cd "$ROOT_DIR/backend"
python -m venv .venv
if [ -f .venv/Scripts/activate ]; then
  source .venv/Scripts/activate  # Windows (Git Bash)
else
  source .venv/bin/activate      # macOS / Linux
fi
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "==> Creating .env from .env.example (edit SECRET_KEY before deploying anywhere real)"
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

echo "==> Running database migrations (SQLite by default)"
DATABASE_URL="${DATABASE_URL:-sqlite:///./quantforge.db}" alembic upgrade head

echo "==> Frontend: installing dependencies"
cd "$ROOT_DIR/frontend"
npm install

cat <<'EOF'

Setup complete.

Start the backend:
  cd backend && source .venv/Scripts/activate && uvicorn app.main:app --reload

Start the frontend (separate terminal):
  cd frontend && npm run dev

Optionally seed demo data once the backend is running:
  python scripts/seed_demo_data.py
EOF
