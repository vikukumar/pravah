# PRAVAH Deployment & Operations Guide

## 1. Prerequisites

- Docker Engine 24+ & Docker Compose v2+
- Python 3.12+
- Node.js 20+
- Domain DNS pointed to your server IP (`pravah.app`)

---

## 2. GitHub Actions Release & Automated Versioning

PRAVAH features an enterprise-grade automated CI/CD release pipeline ([`.github/workflows/release.yml`](.github/workflows/release.yml)):

- **Automatic SemVer Detection**: Evaluates Conventional Commits since the last release tag:
  - `feat!` or `BREAKING CHANGE:` → **Major** bump (`v2.0.0`)
  - `feat:` → **Minor** bump (`v1.1.0`)
  - `fix:`, `perf:`, `refactor:` → **Patch** bump (`v1.0.1`)
  - Manual triggers support explicit overrides (`patch`, `minor`, `major`, `custom`).
- **Zero Actions Storage Quota Usage**: Standalone distribution ZIP files and cryptographic checksums are attached directly to GitHub Releases via `gh release create`, avoiding GitHub Actions artifact storage limits.
- **Categorized Release Notes**: Automatically groups changes into Breaking Changes, Features, Bug Fixes, and Maintenance with commit references.
- **Production Container Publishing**: Pre-built Docker images are published automatically to GitHub Container Registry (GHCR):
  - Unified All-in-One: `ghcr.io/vikukumar/pravah:<version>` & `latest`
  - Modular API: `ghcr.io/vikukumar/pravah-api:<version>` & `latest`
  - Modular Web: `ghcr.io/vikukumar/pravah-web:<version>` & `latest`

---

## 3. Deployment Topologies

### Topology 1: Application-Only Compose (`docker-compose.app.yml`)
> **Best for:** Existing infrastructure with PostgreSQL and Redis already running on the host or managed cloud (RDS/ElastiCache).

Connects frontend, backend, and scheduler on a shared network to external/host databases with persistent uploads:

```bash
# 1. Configure host database and Redis connections in .env
DATABASE_URL=postgresql+asyncpg://pravah_user:password@host.docker.internal:5432/pravah_prod_db
DATABASE_SYNC_URL=postgresql://pravah_user:password@host.docker.internal:5432/pravah_prod_db
REDIS_URL=redis://host.docker.internal:6379/0

# 2. Start frontend, backend API, and scheduler
docker compose -f docker-compose.app.yml up -d

# 3. Check health and persistent uploads volume
docker compose -f docker-compose.app.yml ps
docker volume inspect pravah_app_uploads
```

---

### Topology 2: Full Production Compose (`docker-compose.prod.yml`)
> **Best for:** Standalone VM / bare-metal server deployment with SSL termination, PostgreSQL 16, Redis 7, Nginx, API, and Web.

```bash
# 1. Copy environment template
cp .env.example .env
nano .env

# 2. Place SSL certificates in ./ssl/ (cert.pem & key.pem)

# 3. Launch complete production stack
docker compose -f docker-compose.prod.yml up -d

# 4. Verify status
docker compose -f docker-compose.prod.yml ps
```

*Data and content persistence guarantees:*
- `pravah_uploads_data` → `/app/uploads` (media, generated images, brand assets)
- `pravah_postgres_data` → `/var/lib/postgresql/data/pgdata` (database)
- `pravah_redis_data` → `/data` (queue & cache state)

---

### Topology 3: Kubernetes Deployment via Helm 3 Chart (`deploy/helm/pravah`)
> **Best for:** Scalable Kubernetes clusters (EKS, GKE, AKS, k3s, or bare-metal k8s).

Install directly from the GHCR OCI registry or local chart:

```bash
# 1. Install or upgrade via official OCI chart
helm upgrade --install pravah oci://ghcr.io/vikukumar/charts/pravah \
  --version 1.0.0 \
  --namespace pravah --create-namespace \
  -f deploy/helm/pravah/values.yaml

# 2. Verify all workloads (API, Web, Scheduler, Ingress, PVC)
kubectl get pods,svc,pvc,ingress -n pravah
```

---

### Topology 4: Single All-in-One Container (`Dockerfile`)
```bash
docker run -d \
  --name pravah-app \
  -p 3000:3000 \
  -p 8000:8000 \
  -v pravah_uploads:/app/uploads \
  --env-file .env \
  ghcr.io/vikukumar/pravah:latest
```

---

### Topology 5: Standalone Release ZIP
1. Download `pravah-vX.Y.Z.zip` and `SHA256SUMS.txt` from [GitHub Releases](https://github.com/vikukumar/pravah/releases).
2. Verify integrity: `sha256sum -c SHA256SUMS.txt`
3. Extract and launch:
   ```bash
   unzip pravah-vX.Y.Z.zip
   cd pravah-vX.Y.Z
   cp .env.example .env
   ./start.sh      # Linux/macOS
   # or
   .\start.ps1     # Windows
   ```

---

## 4. Post-Deployment Verification

1. Navigate to `https://your-domain.com/setup` in your browser.
2. Complete the 7-step interactive setup wizard.
3. Access your Super Administrator dashboard at `/admin`.
4. Test OAuth social channels at `/dashboard/social`.
5. Execute a visual DAG workflow test run at `/dashboard/workflows`.

