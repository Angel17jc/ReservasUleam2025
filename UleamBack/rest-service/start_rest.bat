@echo off
cd /d "C:\ReservasUleam2025\UleamBack\rest-service"
set PYTHONPATH=%CD%
echo Iniciando REST Service...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
