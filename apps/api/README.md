# PRAVAH — Backend API Service

Production-grade asynchronous FastAPI backend service for PRAVAH AI Social Media Management & Automation Platform.

## 🚀 Quick Start (Standalone Repo)

### 1. Virtual Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
cp .env.example .env
```

### 3. Database Migration
```bash
alembic upgrade head
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

- API Documentation: http://localhost:8000/api/v1/docs
- Health Status: http://localhost:8000/health
- Version Info: http://localhost:8000/api/v1/version

### 5. Running Tests
```bash
pytest tests/ -v
```

## 🐳 Docker Deployment
```bash
docker build -t pravah-api .
docker run -p 8000:8000 --env-file .env pravah-api
```
