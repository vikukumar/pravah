# PRAVAH Deployment & Operations Guide

## 1. Prerequisites

- Docker Engine 24+ & Docker Compose v2+
- Python 3.12+
- Node.js 20+
- Domain DNS pointed to your server IP (`pravah.app`)

---

## 2. Production Docker Deployment

```bash
# 1. Clone repository and navigate to root
git clone https://github.com/your-org/pravah.git
cd pravah

# 2. Copy environment file and configure secrets
cp .env.example .env
nano .env

# 3. Generate device-compatible icons (already completed in repo)
python scripts/generate_icons.py

# 4. Launch full production stack with Nginx, PostgreSQL, Redis, API, Worker, and Web
docker compose -f docker-compose.prod.yml up --build -d

# 5. Check container health status
docker compose -f docker-compose.prod.yml ps
```

---

## 3. Post-Deployment Verification

1. Navigate to `https://your-domain.com/setup` in your browser.
2. Complete the 7-step interactive setup wizard.
3. Access your Super Administrator dashboard at `/admin`.
4. Test OAuth social channels at `/dashboard/social`.
5. Execute a visual DAG workflow test run at `/dashboard/workflows`.
