#!/bin/bash
cd "$(dirname "$0")"
source backend/.venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000
