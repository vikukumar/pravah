# ☸️ PRAVAH Kubernetes Helm Chart

Official Helm 3 chart for deploying **PRAVAH** (Enterprise AI Workflow Automation & Social Media Platform) onto Kubernetes clusters (EKS, GKE, AKS, k3s, or bare-metal).

---

## 🚀 Installation using GitHub URLs

### Method 1: Add the PRAVAH Helm Repository via GitHub URL (Recommended)

You can add our Helm repository directly using GitHub:

```bash
# Add the repository via GitHub Raw URL (works immediately without any extra setup)
helm repo add pravah https://raw.githubusercontent.com/vikukumar/pravah/gh-pages/

# Or via GitHub Pages URL (if GitHub Pages is enabled on the repository)
helm repo add pravah https://vikukumar.github.io/pravah/

# Update your local chart cache
helm repo update
```

Install or upgrade PRAVAH:

```bash
# Install with default values in 'pravah' namespace
helm upgrade --install pravah pravah/pravah \
  --namespace pravah --create-namespace

# Or install with your customized values
helm upgrade --install pravah pravah/pravah \
  --namespace pravah --create-namespace \
  -f my-values.yaml
```

---

### Method 2: Direct Install from GitHub Release URL

You can also install any specific release directly from the GitHub Release archive without adding a repository:

```bash
helm upgrade --install pravah \
  https://github.com/vikukumar/pravah/releases/download/v1.0.1/pravah-1.0.1.tgz \
  --namespace pravah --create-namespace \
  -f my-values.yaml
```

---

### Method 3: Install from Local Source

If you have cloned the repository locally:

```bash
helm upgrade --install pravah ./deploy/helm/pravah \
  --namespace pravah --create-namespace \
  -f deploy/helm/pravah/values.yaml
```

---

## 📦 Chart Architecture

The chart orchestrates the full production topology for PRAVAH:

| Component | Kind | Default Port | Description |
|-----------|------|--------------|-------------|
| **API** | `Deployment`, `Service`, `HPA` | `8000` | FastAPI core service handling authentication, AI generation, and workflows |
| **Web** | `Deployment`, `Service`, `HPA` | `3000` | Next.js 14 web application & dashboard |
| **Scheduler** | `Deployment` | — | Background task scheduler for publishing automation |
| **Worker** | `Deployment` | — | Asynchronous task processing (AI workflows, bulk post publishing) |
| **Ingress** | `Ingress` | `80` / `443` | Ingress routes for both Web (`/`) and API (`/api`) with TLS |
| **Storage** | `PersistentVolumeClaim` | — | Persistent storage for uploads, brand assets, and media |
| **Config** | `ConfigMap`, `Secret` | — | Environment variables, database connection strings, and API keys |

---

## ⚙️ Configuration Parameters

Key configurable parameters in `values.yaml`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imageRegistry` | Container image registry | `"ghcr.io"` |
| `api.image.repository` | Docker image repository for API | `"vikukumar/pravah-api"` |
| `api.image.tag` | Docker image tag for API | `"1.0.1"` |
| `api.replicaCount` | Replicas for backend API | `2` |
| `web.image.repository` | Docker image repository for Web | `"vikukumar/pravah-web"` |
| `web.image.tag` | Docker image tag for Web | `"1.0.1"` |
| `web.replicaCount` | Replicas for web frontend | `2` |
| `persistence.uploads.size` | Uploads PVC storage size | `"10Gi"` |
| `ingress.enabled` | Enable Ingress controller routing | `true` |
| `ingress.hosts[0].host` | Hostname for web application | `"app.pravah.internal"` |
| `database.url` | PostgreSQL connection URI | `"postgresql://..."` |
| `redis.url` | Redis connection URI | `"redis://..."` |

---

## 🔍 Verification & Health Checks

```bash
# Check all deployed pods, services, and PVCs
kubectl get all,pvc,ingress -n pravah

# Check API health
kubectl exec -it deployment/pravah-api -n pravah -- curl http://localhost:8000/health

# Stream API logs
kubectl logs -f deployment/pravah-api -n pravah
```

---

## 🗑️ Uninstalling the Chart

To remove the PRAVAH release:

```bash
helm uninstall pravah --namespace pravah
```
