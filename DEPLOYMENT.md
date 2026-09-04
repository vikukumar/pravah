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

## 3. Deployment Options

### Option A: Pre-built Docker Containers (Recommended)

```bash
# Pull and run the unified production image directly
docker run -d \
  --name pravah-app \
  -p 3000:3000 \
  -p 8000:8000 \
  -v pravah_data:/app/apps/api \
  --env-file .env \
  ghcr.io/vikukumar/pravah:latest
```

### Option B: Standalone Release ZIP Deployment

1. Download `pravah-vX.Y.Z.zip` and `SHA256SUMS.txt` from [GitHub Releases](https://github.com/vikukumar/pravah/releases).
2. Verify integrity:
   ```bash
   sha256sum -c SHA256SUMS.txt
   ```
3. Extract and launch:
   ```bash
   unzip pravah-vX.Y.Z.zip
   cd pravah-vX.Y.Z
   cp .env.example .env
   # Edit .env with your production secrets
   ./start.sh      # On Linux/macOS
   # or
   .\start.ps1     # On Windows
   ```

### Option C: Production Docker Compose Stack

```bash
# 1. Clone repository and navigate to root
git clone https://github.com/vikukumar/pravah.git
cd pravah

# 2. Copy environment file and configure secrets
cp .env.example .env
nano .env

# 3. Launch full production stack with Nginx, PostgreSQL, Redis, API, Worker, and Web
docker compose -f docker-compose.prod.yml up --build -d

# 4. Check container health status
docker compose -f docker-compose.prod.yml ps
```

---

## 4. Post-Deployment Verification

1. Navigate to `https://your-domain.com/setup` in your browser.
2. Complete the 7-step interactive setup wizard.
3. Access your Super Administrator dashboard at `/admin`.
4. Test OAuth social channels at `/dashboard/social`.
5. Execute a visual DAG workflow test run at `/dashboard/workflows`.

