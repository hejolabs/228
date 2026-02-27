#!/bin/bash
cd "$(dirname "$0")"

echo "백엔드 시작..."
source backend/.venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000 &
cd "$(dirname "$0")"

echo "프론트엔드 시작..."
npm run dev --prefix frontend &

echo ""
echo "백엔드:    http://localhost:8000"
echo "프론트엔드: http://localhost:5173"
echo "종료: ./shutdown.sh"

wait
