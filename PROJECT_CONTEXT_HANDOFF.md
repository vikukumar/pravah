# PRAVAH — Project Context & Session Handoff Document

> **Last Updated:** September 5, 2026  
> **Workspace:** `d:\Projects\Pravah`  
> **Stack:** Next.js 16.3.4 (Turbopack, Tailwind CSS, TypeScript), FastAPI (Python 3.12, SQLAlchemy 2.0 async, Pydantic v2, SQLite/PostgreSQL, Redis), Python venv at `apps/api/.venv`  
> **Local Launcher:** `start.ps1` (Backend on `:8000`, Frontend on `:3000`)

---

## 1. Executive Summary & Purpose

This document encapsulates the complete architectural state, features implemented, bugs resolved, data schemas, API routes, and operational procedures across recent pair programming sessions. It serves as a single source of truth for seamless continuation without losing conversation context.

---

## 2. Completed Features & System Enhancements

### 2.1 Dynamic Calendar & Festival Engine
- **Problem Solved:** Static, hardcoded holiday lists lacked country/region accuracy and annual freshness.
- **Solution:** Multi-tier dynamic API fallback chain implemented in [`apps/api/app/services/calendar_service.py`](file:///d:/Projects/Pravah/apps/api/app/services/calendar_service.py):
  1. `Calendarific API` (Primary international & multi-religion festival database)
  2. `Abstract API Holidays` (Secondary fallback)
  3. `Google Calendar Public Holidays API` (Tertiary fallback)
  4. Curated offline fallback dataset for 100% offline resilience.
- **Credential Priority:** System Settings DB (Admin UI encrypted) $\rightarrow$ Environment variables.
- **Frontend Integration:** [`apps/web/app/dashboard/calendar/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/dashboard/calendar/page.tsx) provides month/year navigation, category filters (National, Gazetted, Observance), and direct "Create Post for Festival" action.

---

### 2.2 Workflow Lifecycle, Dev Execution & Account Validation
- **Problem Solved:** Workflows could not be deleted; draft workflows could not be tested; workflows executed without verifying if linked social channels were valid.
- **Changes Applied:**
  - **Soft-Delete Filtering:** Updated [`apps/api/app/api/v1/workflows.py`](file:///d:/Projects/Pravah/apps/api/app/api/v1/workflows.py) list query to exclude `archived` workflows by default (`?show_archived=true` to view).
  - **Role Permissions:** Added `workflow.delete`, `workflow.edit`, and `workflow.publish` permissions to manager/admin roles in [`apps/api/app/services/rbac_service.py`](file:///d:/Projects/Pravah/apps/api/app/services/rbac_service.py).
  - **Development Execution Flag:** Enabled draft workflows to be executed in testing mode (`dev_run=true`) in [`apps/api/app/services/workflow_engine.py`](file:///d:/Projects/Pravah/apps/api/app/services/workflow_engine.py).
  - **Account Connectivity Pre-flight:** Workflow execution engine now validates that every social account referenced in action nodes is connected and has valid credentials before execution commences.

---

### 2.3 AI Studio UI & Provider Availability
- **Inline Brand SVGs:** Replaced emoji placeholders with high-fidelity brand SVGs (Instagram, X/Twitter, Facebook, LinkedIn, YouTube) with custom brand gradients on active selection in [`apps/web/app/dashboard/ai-studio/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/dashboard/ai-studio/page.tsx).
- **Accessible Switch Design:** Replaced unstyled checkboxes with standard accessible toggle switches (`role="switch"`, `aria-checked`, smooth transitions, proper track/knob dimensions).
- **Gemini & Multi-Provider Support:** Surfaced Google Gemini alongside OpenAI, Anthropic, and OpenRouter in user-facing model selection.

---

### 2.4 Complete Admin Dashboard Overhaul
Replaced all "Under Development" placeholder pages with fully operational production pages:

| Admin Module | Frontend Page | Backend Endpoints | Purpose |
|---|---|---|---|
| **Admin Layout** | [`apps/web/app/admin/layout.tsx`](file:///d:/Projects/Pravah/apps/web/app/admin/layout.tsx) | — | 6 categorized collapsible sidebar groups: Overview, User/Org, AI & Content, Integrations, Billing & Plans, System |
| **Payment Gateways** | [`apps/web/app/admin/payment-gateways/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/admin/payment-gateways/page.tsx) | `GET/POST /admin/payment-gateways` | Razorpay & Cashfree credential storage, webhook keys, active/test toggle |
| **Subscription Plans** | [`apps/web/app/admin/plans/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/admin/plans/page.tsx) | `GET/POST/PUT/DELETE /admin/plans` | Full CRUD for plans (Free, Starter, Pro, Enterprise) with quotas, feature flags, gateway plan IDs |
| **Roles & RBAC** | [`apps/web/app/admin/roles/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/admin/roles/page.tsx) | `GET /admin/roles`, `GET /admin/permissions`, `PUT /admin/roles/{id}/permissions` | View system roles, toggle permissions by module or individually, live save |
| **System Health** | [`apps/web/app/admin/health/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/admin/health/page.tsx) | `GET /admin/health` | Real-time DB latency (ping query), Redis status, worker status, env sanity checks |
| **Email & Notifications** | [`apps/web/app/admin/notifications/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/admin/notifications/page.tsx) | `GET/POST /admin/email-settings`, `POST /admin/email-settings/test` | SMTP, SendGrid, Mailgun configuration, sender identity, live test email trigger |
| **Platform API Keys** | [`apps/web/app/admin/api-keys/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/admin/api-keys/page.tsx) | `GET /admin/api-keys`, `POST/DELETE /admin/api-keys/{key}` | Encrypted storage & masking for AI keys, calendar keys, payment & email keys |
| **Billing & Invoices** | [`apps/web/app/admin/billing/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/admin/billing/page.tsx) | `GET /admin/billing/subscriptions`, `GET /admin/billing/payments`, `PUT /admin/billing/subscriptions/{id}/plan` | MRR KPI cards, subscription list with filters, payment audit history, direct plan update |

---

### 2.5 Hydration Error Fix in Roles Page
- **Bug:** `In HTML, <button> cannot be a descendant of <button>`.
- **Location:** [`apps/web/app/admin/roles/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/admin/roles/page.tsx).
- **Cause:** Accordion module header was a `<button onClick={() => toggleModule(mod)}>`, which nested the inner `<button onClick={toggleModuleAll}>` ("All / None").
- **Fix:** Converted outer wrapper to `<div role="button" tabIndex={0} onClick={...} onKeyDown={...} className="cursor-pointer select-none">`.
- **SQLAlchemy 2.0 Cleanup:** Fixed `.where(Role.organisation_id == None)` to `.where(Role.organisation_id.is_(None))` in [`apps/api/app/api/v1/admin.py`](file:///d:/Projects/Pravah/apps/api/app/api/v1/admin.py).
- **Field Name Alignment:** Fixed `p.payment_gateway` to `getattr(p, "gateway", getattr(p, "payment_gateway", None))` for `Payment` records.

---

### 2.6 Plan Quota Resolution & Dynamic Upgrades
- **Bug:** User workspace had active `Enterprise` subscription, but UI displayed Free tier quotas (`0/1` social channels, `0/30` posts, `0/100k` tokens, `0/2` workflows).
- **Root Causes:**
  1. **Schema Mismatch:** Backend returned flat properties (`social_account_limit`), while UI read `usage?.limits?.social_account_limit` $\rightarrow$ evaluated to `undefined`, falling back to hardcoded Free defaults.
  2. **Token Field Naming:** Backend returned `ai_tokens_used_this_month`, frontend read `ai_tokens_consumed_this_month`.
  3. **Gateway Dependency:** Upgrading in development mode without live Razorpay keys was blocked.
- **Fixes Applied:**
  - **[`apps/api/app/schemas/billing.py`](file:///d:/Projects/Pravah/apps/api/app/schemas/billing.py):**
    - Added `QuotaLimitsSchema` containing all quota limits.
    - Added `ChangePlanRequest`.
    - Enhanced `UsageMetricsResponse` to include both flat and nested `limits`, `plan_name`, `plan_slug`, and `ai_tokens_consumed_this_month`.
  - **[`apps/api/app/services/billing_service.py`](file:///d:/Projects/Pravah/apps/api/app/services/billing_service.py):**
    - `get_usage_metrics`: Resolves active subscription's `PlanFeature` (or DB fallback to `free` plan), builds complete `limits` dict and flat attributes.
    - Added `check_quota(org_id, resource, increment=1)`: Centralized quota enforcement utility.
    - Added `activate_plan(org_id, plan_id, billing_period, user)`: Immediate subscription assignment and quota expansion.
  - **[`apps/api/app/api/v1/billing.py`](file:///d:/Projects/Pravah/apps/api/app/api/v1/billing.py):**
    - Added `POST /api/v1/billing/change-plan` for instant user-level plan switches.
  - **[`apps/api/app/api/v1/admin.py`](file:///d:/Projects/Pravah/apps/api/app/api/v1/admin.py):**
    - Added `PUT /api/v1/admin/billing/subscriptions/{id}/plan` for admin overrides.
  - **[`packages/shared-types/src/index.ts`](file:///d:/Projects/Pravah/packages/shared-types/src/index.ts):**
    - Expanded `UsageMetrics` interface with flat and nested limit definitions.
  - **[`apps/web/app/dashboard/billing/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/dashboard/billing/page.tsx) & [`apps/web/app/dashboard/page.tsx`](file:///d:/Projects/Pravah/apps/web/app/dashboard/page.tsx):**
    - Meters read `usage?.limits?.<field> ?? usage?.<field>`.
    - Tokens read `usage?.ai_tokens_consumed_this_month ?? usage?.ai_tokens_used_this_month ?? 0`.
    - Added meters for **Team Members** and **Workflow Executions (Monthly)**.
    - Added dev fallback in Upgrade modal: automatically activates plan directly if Razorpay credentials are not configured.

---

## 3. Current Quota Table (Default Tiers)

| Resource Metric | Free | Starter | Pro | Enterprise |
|---|---|---|---|---|
| **Connected Social Channels** | 1 | 5 | 20 | 100 |
| **Monthly Posts** | 30 | 300 | 1,500 | 10,000 |
| **Daily Posts** | 1 | 10 | 50 | 500 |
| **Monthly AI Tokens** | 50,000 | 250,000 | 1,000,000 | 5,000,000 |
| **AI Images** | 10 | 50 | 200 | 1,000 |
| **Visual Workflows** | 3 | 10 | 50 | 200 |
| **Workflow Executions/mo** | 100 | 500 | 2,500 | 20,000 |
| **Team Members** | 1 | 3 | 10 | 50 |
| **Storage (MB)** | 500 | 2,048 | 10,240 | 51,200 |

*Note: In Enterprise tier, your active workspace (`Vikash's Workspace`) currently reflects the full 100 channels, 10,000 posts, 5,000,000 AI tokens, and 200 workflows.*

---

## 4. Key Files Reference Map

```
Pravah/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/v1/
│   │   │   │   ├── admin.py            # Super Admin endpoints (Health, Roles, Plans, Keys, Billing)
│   │   │   │   ├── billing.py          # User billing, plans, /usage, /change-plan, payment webhooks
│   │   │   │   ├── workflows.py        # Workflows CRUD, execution, dev run, account validation
│   │   │   │   └── social.py           # OAuth connect, provider availability, token storage
│   │   │   ├── models/
│   │   │   │   ├── billing.py          # Plan, PlanFeature, Subscription, Payment, PaymentWebhook
│   │   │   │   └── organisation.py     # Organisation, Member, Role, Permission, RolePermission
│   │   │   ├── schemas/
│   │   │   │   └── billing.py          # QuotaLimitsSchema, UsageMetricsResponse, ChangePlanRequest
│   │   │   └── services/
│   │   │       ├── billing_service.py  # Seed plans, get_usage_metrics, check_quota, activate_plan
│   │   │       ├── calendar_service.py # Calendarific / Abstract / Google API fallback engine
│   │   │       ├── workflow_engine.py  # Execution engine, draft execution, channel connectivity check
│   │   │       └── rbac_service.py     # Role permission seeding & checking
│   ├── web/
│   │   ├── app/
│   │   │   ├── admin/
│   │   │   │   ├── layout.tsx          # Collapsible grouped admin sidebar
│   │   │   │   ├── plans/page.tsx      # Plans & Quotas management
│   │   │   │   ├── roles/page.tsx      # Role & Permission matrix editor
│   │   │   │   ├── health/page.tsx     # System health live monitor
│   │   │   │   ├── notifications/page.tsx # Email configuration
│   │   │   │   ├── api-keys/page.tsx   # Platform API keys manager
│   │   │   │   └── billing/page.tsx    # Subscriptions & payments table
│   │   │   └── dashboard/
│   │   │       ├── page.tsx            # Main overview with real-time KPI quota cards
│   │   │       ├── billing/page.tsx    # Quota meters, currency switcher, tier selector, upgrade modal
│   │   │       ├── ai-studio/page.tsx  # Brand SVG platform icons, accessible switches
│   │   │       └── calendar/page.tsx   # Dynamic festival calendar & post generator
└── packages/
    └── shared-types/src/index.ts       # Shared TypeScript types (UsageMetrics, Plan, Subscription)
```

---

## 5. Verification Commands

Run these at any time to verify system integrity:

```powershell
# 1. Verify Frontend TypeScript Compilation (apps/web)
cd d:\Projects\Pravah\apps\web
npx tsc --noEmit --skipLibCheck

# 2. Verify Backend Python Modules (apps/api)
cd d:\Projects\Pravah\apps\api
& ".\.venv\Scripts\python.exe" -c "import app.api.v1.admin, app.api.v1.billing, app.services.billing_service; print('SUCCESS: Backend clean')"

# 3. Verify Active Organisation Quotas in Database
& ".\.venv\Scripts\python.exe" -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.services.billing_service import BillingService

async def check():
    async with AsyncSessionLocal() as db:
        svc = BillingService(db)
        # Check first organisation
        from sqlalchemy import select
        from app.models.organisation import Organisation
        res = await db.execute(select(Organisation).limit(1))
        org = res.scalar_one_or_none()
        if org:
            metrics = await svc.get_usage_metrics(org.id)
            print(f'Org: {org.name} | Plan: {metrics.get(\"plan_name\")} | Social Quota: {metrics.get(\"social_account_limit\")} | Post Quota: {metrics.get(\"monthly_post_limit\")}')

asyncio.run(check())
"
```

---

## 6. How to Continue in the Next Step

- When starting a new session or asking questions, you can reference this document:
  *"Refer to `PROJECT_CONTEXT_HANDOFF.md` for our current state."*
- All admin pages, billing quotas, calendar APIs, and workflow engine fixes are complete and hot-reloading on `start.ps1`.
