# PRD — PRAVAH

**Product Name:** PRAVAH
**Meaning:** प्रवाह — continuous flow, distribution, and movement
**Product Category:** AI-Powered Social Media Management, Automation & No-Code/Low-Code Platform
**Product Type:** Multi-Tenant SaaS
**Primary Brand Domain Target:** `pravah`-based brand domain; exact domain availability must be verified before final brand registration.

---

## 1. Product Vision

PRAVAH is a production-grade, secure, multi-tenant, organisation-based AI social media management and automation platform that enables individuals, businesses, agencies and organisations to connect their social accounts, analyse their profiles, generate AI-optimised content, visually build automation workflows, schedule and automatically publish content, monitor performance and manage multiple brands from one platform.

PRAVAH must be a **real working product**, not a prototype, demo, mockup, proof-of-concept or simulated application.

There must be:

* No dummy functionality.
* No fake API responses.
* No mock social publishing.
* No hardcoded business data.
* No fake analytics.
* No simulated authentication.
* No placeholder implementation presented as completed functionality.
* No `TODO`, `FIXME`, `coming soon` or intentionally incomplete production features.
* Every advertised feature must have a real implementation or a clearly enforced plan/permission boundary.
* All data must be persisted through the real database/storage architecture.
* All external integrations must use their actual APIs.
* Failed external operations must be handled safely and visibly.
* The system must be ethical and compliant with applicable platform policies and laws.

---

# 2. Core Product Principles

PRAVAH must follow these principles:

1. **Security first**
2. **Real implementation only**
3. **Multi-tenancy by design**
4. **Organisation isolation**
5. **RBAC everywhere**
6. **Privacy by default**
7. **Explicit user consent**
8. **Official social APIs only**
9. **No spam automation**
10. **No bypassing platform restrictions**
11. **No credential scraping**
12. **No deceptive engagement**
13. **No artificial likes/followers/comments**
14. **No unauthorised posting**
15. **No storing unnecessary social credentials**
16. **Transparent AI-generated content**
17. **Auditable automation**
18. **Database-driven configuration**
19. **Admin-controlled plans and limits**
20. **Responsive and accessible UX**
21. **No browser `alert()`, `confirm()` or `prompt()`**
22. **No destructive action without an application modal confirmation**
23. **No fake success messages**
24. **No silent failures**

---

# 3. Target Users

### 3.1 Individual Users

Users managing:

* Personal brands
* Creators
* Professionals
* Influencers
* Freelancers

### 3.2 Business Users

Businesses managing:

* Company profiles
* Marketing
* Product announcements
* Campaigns
* Multiple social channels

### 3.3 Agencies

Agencies managing:

* Multiple clients
* Multiple organisations
* Multiple brands
* Multiple social accounts
* Multiple content calendars

### 3.4 Enterprise

Enterprise customers requiring:

* Organisation hierarchy
* Multiple teams
* RBAC
* Approval workflows
* Audit logs
* Security policies
* SSO
* Advanced integrations

### 3.5 Platform Administrators

Administrators managing:

* Users
* Organisations
* Plans
* Billing
* Providers
* Social integrations
* CMS
* Security
* System configuration
* Feature flags
* Analytics
* Audit logs

---

# 4. Application Architecture

PRAVAH must be a true multi-tenant architecture.

Hierarchy:

```text
PRAVAH Platform
│
├── Platform Administration
│
├── Users
│
├── Organisations
│   │
│   ├── Organisation Settings
│   ├── Members
│   ├── Teams
│   ├── Roles
│   ├── Social Accounts
│   ├── Social Pages
│   ├── Content
│   ├── AI Providers
│   ├── Workflows
│   ├── Schedules
│   ├── Analytics
│   └── Billing
│
└── Public Website
```

Every organisation-owned record must have an appropriate tenant/organisation ownership boundary.

A user must never be able to access another organisation's data through:

* URL manipulation
* API manipulation
* ID substitution
* GraphQL/query manipulation
* browser requests
* exported identifiers
* background jobs
* workflow execution
* websocket/realtime channels

---

# 5. First-Run Setup

When PRAVAH is deployed for the first time, `/setup` must automatically become available.

The setup process must be database-driven and protected against concurrent initialisation.

### Setup Wizard

#### Step 1 — System Configuration

Collect:

* Application name
* Application URL
* Environment
* Default timezone
* Default locale
* Default currency
* Email configuration
* Storage configuration
* Database connection
* Encryption configuration
* Application branding

#### Step 2 — Super Administrator

Create the first:

**Super Admin**

Fields:

* First name
* Middle name
* Last name
* Email
* Phone
* Password
* Confirm password

Password must satisfy configurable security requirements.

#### Step 3 — Authentication

Configure:

* Email/password
* Email verification
* OTP
* Password reset
* Magic link
* Passwordless login
* 2FA
* SSO

#### Step 4 — SSO Configuration

Admin can configure supported identity providers.

Examples:

* Google
* Microsoft
* GitHub
* Apple
* Generic OIDC
* Generic SAML where supported

SSO configuration must be encrypted.

#### Step 5 — Initial Platform Settings

Configure:

* Registration enabled/disabled
* Email verification requirement
* Phone verification requirement
* 2FA policy
* Password policy
* Session duration
* Login attempt policy
* Rate limiting
* Maintenance mode
* Public website settings

#### Step 6 — Initial Free Plan

Automatically create the default Free Plan:

```text
Social Accounts: 1
Posts: 1/day
Duration: 30 days
```

After the free entitlement expires, the user must purchase an active plan to continue restricted functionality.

#### Step 7 — Complete Setup

After successful setup:

* Mark installation as initialized.
* Disable public access to `/setup`.
* Require authenticated Super Admin for setup-related configuration.
* Log setup completion in the audit system.

---

# 6. Authentication

PRAVAH must support:

### Standard Authentication

Registration:

* Email
* Phone number optional
* Password
* Confirm password
* First name
* Middle name optional
* Last name optional

### Verification

Support:

* Email verification
* OTP verification
* Configurable verification policies

### Login Methods

Support:

* Email + password
* OTP
* Magic link
* Passwordless
* SSO

### Account Recovery

Support:

* Forgot password
* Password reset
* Recovery codes
* Session revocation
* Account recovery controls

### 2FA

Support:

* TOTP
* Backup/recovery codes
* Configurable enforcement

Future provider-specific mechanisms may be added through the authentication architecture.

---

# 7. Authentication Security

Implement:

* Password hashing using modern adaptive password hashing.
* Secure password reset tokens.
* Short-lived OTPs.
* OTP attempt limits.
* OTP expiration.
* Login rate limiting.
* Account lockout/risk controls.
* Session rotation.
* Secure session invalidation.
* Device/session management.
* CSRF protection where applicable.
* Secure cookies.
* HttpOnly cookies.
* SameSite policy.
* Secure cookies in production.
* Brute-force protection.
* Credential stuffing protection.
* IP/risk throttling.
* Security event logging.
* Suspicious login detection.
* Reauthentication for sensitive actions.

Never store:

* Plaintext passwords
* Plaintext OAuth client secrets
* Plaintext API keys
* Plaintext provider secrets
* Social access tokens unless required and securely encrypted

---

# 8. Organisation System

Every registered user can create or join organisations according to the active plan.

Organisation contains:

* Organisation name
* Slug
* Logo
* Description
* Website
* Industry
* Location
* Contact information
* Timezone
* Locale
* Brand identity
* Social profiles
* Billing
* Members
* Teams
* Roles
* Permissions
* Content
* Workflows
* Analytics

A user may belong to multiple organisations.

The active organisation must always be explicitly identifiable in the application.

---

# 9. Organisation Profiles

Each organisation can maintain separate:

* Brand profile
* Social identity
* Content strategy
* Audience
* Industry
* Tone of voice
* Language
* Keywords
* Hashtags
* Content preferences
* Posting preferences
* AI instructions

AI-generated content must use the selected organisation context.

---

# 10. RBAC

Implement complete RBAC.

Default role:

**User**

Platform roles:

* Super Admin
* Admin
* Moderator
* Support

Organisation roles:

* Organisation Owner
* Organisation Admin
* Manager
* Editor
* Publisher
* Analyst
* User
* Custom Roles

Administrators must be able to create custom roles.

Permissions must be granular.

Examples:

```text
organisation.view
organisation.update
member.view
member.invite
member.remove
role.manage
social.view
social.connect
social.disconnect
content.view
content.create
content.update
content.delete
content.publish
workflow.view
workflow.create
workflow.execute
analytics.view
billing.view
billing.manage
settings.manage
```

Permission checks must exist server-side.

Frontend-only permission hiding is insufficient.

---

# 11. Dashboard

The dashboard must be:

* Responsive
* Mobile friendly
* Desktop optimised
* Tablet compatible
* Fast
* Modern
* Accessible
* Customisable

Layout:

```text
Sidebar
├── Overview
├── Content
├── Calendar
├── Social Accounts
├── Pages
├── AI Studio
├── Workflows
├── Analytics
├── Campaigns
├── Inbox
├── Team
├── Billing
└── Settings
```

---

# 12. Custom Dashboard Builder

The Overview dashboard must support:

* Drag & drop
* Resize
* Add widget
* Remove widget
* Reorder
* Collapse
* Expand
* Widget configuration
* Save layout
* Reset layout
* Multiple dashboard layouts

Widgets may include:

* Total posts
* Scheduled posts
* Published posts
* Failed posts
* Social account summary
* Engagement
* Followers
* Reach
* Impressions
* Best performing content
* Upcoming posts
* AI recommendations
* Content performance
* Workflow execution
* Account health
* Plan usage

Widget availability must be permission- and plan-aware.

---

# 13. No-Code / Low-Code Visual Platform

PRAVAH must provide an n8n/Flowise-style visual interface.

Users must be able to construct workflows visually.

Core interaction:

```text
Trigger
   ↓
Condition
   ↓
AI Generation
   ↓
Image Generation
   ↓
Content Validation
   ↓
Approval
   ↓
Schedule
   ↓
Publish
   ↓
Analytics
```

The visual builder must support:

* Drag & drop nodes
* Connect nodes
* Delete nodes
* Duplicate nodes
* Configure nodes
* Resize nodes
* Zoom
* Pan
* Minimap
* Undo
* Redo
* Validation
* Save
* Draft
* Publish
* Version history
* Workflow activation/deactivation
* Execution history
* Error states
* Retry
* Logs

---

# 14. Workflow Engine

Workflows must execute through a real backend execution engine.

Do not execute critical workflows solely inside the browser.

Support:

### Triggers

* Schedule
* Manual execution
* New content
* Social event where supported
* Webhook
* Campaign event
* Approval event
* Account event
* System event

### Logic Nodes

* Condition
* AND
* OR
* NOT
* Switch
* Filter
* Delay
* Loop
* Iterator
* Merge
* Transform

### AI Nodes

* Generate text
* Rewrite
* Summarise
* Translate
* Generate hashtags
* Generate captions
* Generate image prompt
* Generate image
* Analyse profile
* Analyse content
* Recommend posting time

### Social Nodes

* Publish post
* Schedule post
* Retrieve account
* Retrieve page
* Retrieve analytics
* Retrieve posts
* Content validation

### Utility Nodes

* HTTP request
* Webhook
* JSON transformation
* Variable
* Secret reference
* Notification
* Email

All nodes must have real implementations.

---

# 15. Workflow Security

Workflows must execute within the organisation's security context.

A workflow must not be able to:

* Access another organisation.
* Access another user's secrets.
* bypass permissions.
* expose access tokens.
* publish without required permission.
* execute disabled integrations.
* exceed plan limits.

Workflow executions must have:

* Execution ID
* Workflow ID
* Organisation ID
* User/actor ID
* Start time
* End time
* Status
* Node execution status
* Error information
* Retry count
* Resource consumption

Sensitive values must be masked in logs.

---

# 16. Social Media Integrations

Initial architecture must support:

* Facebook
* Instagram
* X
* LinkedIn
* YouTube

The integration architecture must be extensible for additional networks.

Potential future integrations:

* TikTok
* Pinterest
* Threads
* Reddit
* Telegram
* Google Business Profile
* Other officially supported platforms

Only officially supported APIs and permitted integration methods may be used.

PRAVAH must never:

* automate through stolen credentials.
* scrape private account information.
* bypass CAPTCHA.
* bypass rate limits.
* bypass platform restrictions.
* imitate browser behaviour to circumvent API limitations.
* publish without user authorisation.

---

# 17. Social Account Connection

Connection flow:

```text
Organisation
   ↓
Add Social Account
   ↓
Select Platform
   ↓
OAuth / Official Authentication
   ↓
Consent
   ↓
Retrieve Authorised Accounts
   ↓
User Selects Account/Page
   ↓
Store Encrypted Tokens
   ↓
Synchronise Metadata
   ↓
Analyse Profile
   ↓
Create AI Profile Summary
```

Tokens must be encrypted at rest.

Token access must be restricted to the minimum service required.

---

# 18. Social Profile Intelligence

After connecting an account, PRAVAH should retrieve permitted public/account data through official APIs.

Create an AI-optimised internal profile summary containing relevant information such as:

* Brand identity
* Business category
* Description
* Audience indicators
* Content themes
* Posting patterns
* Communication tone
* Common topics
* Keywords
* Hashtags
* Content formats
* Engagement patterns
* Brand terminology

The summary must be:

* AI generated
* Versioned
* Refreshable
* Organisation scoped
* Privacy aware
* Based only on permitted data

The system must not infer sensitive personal attributes unnecessarily.

---

# 19. Social Pages

Users must be able to connect supported pages/accounts where permitted by the platform.

Each page must have:

* Platform
* External ID
* Name
* Username
* URL
* Profile image
* Description
* Connection status
* Permissions
* Token association
* Last synchronisation
* Health status

Pages must be independently selectable in campaigns and workflows.

---

# 20. Content Management

Content types:

* Text
* Image
* Video
* Link
* Carousel where supported
* Platform-specific formats

Content states:

```text
Draft
↓
AI Generated
↓
Review
↓
Approved
↓
Scheduled
↓
Publishing
↓
Published
```

Also support:

* Failed
* Cancelled
* Rejected
* Archived

---

# 21. AI Content Generation

Users can provide:

* Topic
* Objective
* Audience
* Tone
* Language
* Keywords
* Hashtags
* CTA
* Content type
* Platform
* Brand instructions

PRAVAH generates platform-appropriate content.

AI must consider:

* Organisation profile
* Connected social profile
* Historical content
* Brand voice
* Selected platform
* Character limits
* Content policy
* User preferences

---

# 22. Automatic Daily Content

User configures:

```text
Posts per day
Platforms
Content categories
Preferred languages
Preferred tone
Preferred topics
Approval requirement
Image requirement
Posting period
Timezone
```

PRAVAH then creates a content schedule based on:

* Profile behaviour
* Audience patterns where data is available
* Historical engagement
* Platform characteristics
* User-defined constraints
* Organisation timezone
* Content frequency
* Existing scheduled content

The system must not guarantee engagement outcomes.

---

# 23. Best-Time Recommendation Engine

The system must calculate recommended posting windows.

Inputs:

* Historical engagement
* Historical impressions
* Historical reach
* Historical publication time
* Day of week
* Platform
* Content type
* Audience data where permitted
* Organisation timezone
* User preferences

Recommendations must include an explanation such as:

```text
Recommended:
Tuesday — 7:30 PM

Reason:
Historical engagement for this profile is strongest
during this time window.
```

Recommendations must improve as more legitimate data becomes available.

---

# 24. Automatic Publishing

When the user explicitly enables automatic publishing:

```text
Content Generated
      ↓
Validation
      ↓
Plan Check
      ↓
Permission Check
      ↓
Platform Check
      ↓
Schedule Check
      ↓
Publish
      ↓
Verify API Response
      ↓
Persist Result
```

Publishing must happen through official APIs.

The system must handle:

* Rate limits
* Expired tokens
* Revoked permissions
* Platform errors
* Duplicate requests
* Network failure
* Retryable errors
* Non-retryable errors

Idempotency must prevent accidental duplicate publishing.

---

# 25. Ethical Publishing Rules

Automatic publishing must require explicit user consent.

The system must provide:

* Automation enable/disable
* Platform-specific controls
* Content approval controls
* Emergency stop
* Schedule pause
* Account disconnect
* Audit trail

PRAVAH must not be designed for:

* Spam
* Mass unsolicited messaging
* Fake engagement
* Bot networks
* Artificial followers
* Manipulated reviews
* Coordinated deceptive behaviour
* Platform abuse
* Circumvention of API restrictions

---

# 26. Content Approval System

Organisations can optionally require approval.

Workflow:

```text
AI Generated
     ↓
Editor Review
     ↓
Manager Approval
     ↓
Publisher
     ↓
Social Platform
```

Approvers can:

* Approve
* Reject
* Request changes
* Edit
* Comment

Every action must be audited.

---

# 27. AI Provider Architecture

PRAVAH must support a provider abstraction layer.

The platform must support:

* OpenRouter
* 400+ compatible providers/models through the provider architecture
* Custom provider configuration
* Organisation providers
* User providers
* Admin-managed providers

Provider categories:

* Text generation
* Image generation
* Vision
* Embeddings
* Moderation
* Translation
* Other AI capabilities

---

# 28. OpenRouter

OpenRouter must be implemented as a first-class provider.

Admin can configure:

* API key
* Enabled models
* Default model
* Fallback model
* Token limits
* Usage limits
* Cost limits

Users may use:

* Admin-provided provider
* Organisation provider
* Their own provider

depending on plan and permissions.

---

# 29. Custom AI Providers

Provider configuration should support:

* Provider name
* API endpoint
* Authentication method
* API key
* Model
* Model capabilities
* Request format
* Response mapping where necessary
* Rate limits
* Timeout
* Retry policy
* Enabled/disabled
* Organisation scope

Secrets must be encrypted.

---

# 30. Provider Priority

Configurable hierarchy:

```text
User Provider
      ↓
Organisation Provider
      ↓
Admin Provider
      ↓
Platform Default
```

Actual precedence must be configurable.

---

# 31. AI Cost Controls

Implement:

* Token usage tracking
* Image generation usage
* Provider usage
* Cost estimation
* Monthly limits
* Daily limits
* Organisation limits
* User limits
* Plan limits
* Alerts
* Hard stop when configured limits are exceeded

---

# 32. AI Safety

AI generation must include:

* Prompt validation
* Content moderation where appropriate
* Policy checks
* Sensitive data protection
* Secret filtering
* Output validation
* Platform-specific restrictions

Never send unnecessary sensitive organisation/user information to third-party AI providers.

---

# 33. Media Library

Users need an organisation-scoped media library.

Support:

* Images
* Videos
* Generated images
* Uploaded media
* Post attachments

Features:

* Upload
* Preview
* Search
* Filter
* Tags
* Metadata
* Delete
* Archive
* Usage tracking

Storage must be configurable.

---

# 34. Content Calendar

Calendar views:

* Month
* Week
* Day
* List

Features:

* Drag and drop scheduling
* Reschedule
* Filter by platform
* Filter by account
* Filter by status
* Campaign filter
* Content preview
* Approval status
* Publishing status

Calendar changes must persist to backend.

---

# 35. Analytics

Analytics must use actual data retrieved from supported APIs.

Metrics may include:

* Followers
* Reach
* Impressions
* Engagement
* Likes
* Comments
* Shares
* Saves
* Clicks
* Views
* Watch time where available
* Post performance

Provide:

* Account analytics
* Platform analytics
* Post analytics
* Campaign analytics
* Organisation analytics

Do not display fabricated metrics.

---

# 36. Analytics Dashboard

Support:

* Date range
* Platform filter
* Account filter
* Content filter
* Campaign filter

Charts must support:

* Trend
* Comparison
* Ranking
* Performance distribution

Export:

* CSV
* PDF where implemented
* Other configured reporting formats

---

# 37. AI Analytics

AI can analyse legitimate analytics and produce:

* Performance summary
* Best content
* Weak content
* Trend detection
* Posting recommendations
* Content recommendations
* Topic recommendations
* Format recommendations

AI must distinguish:

**Observed data** from **AI inference/recommendation**.

---

# 38. Campaigns

Users can create campaigns.

Campaign fields:

* Name
* Description
* Objective
* Start date
* End date
* Platforms
* Social accounts
* Content categories
* Budget information where applicable
* Status
* Owner
* Team
* Approval rules

Campaign content can connect to workflows.

---

# 39. Notifications

Notification system must support:

* In-app
* Email
* Optional supported channels

Events:

* Content approved
* Content rejected
* Publishing success
* Publishing failure
* Token expired
* Social account disconnected
* Workflow failed
* Plan usage warning
* Subscription event
* Security event

Users must control notification preferences.

---

# 40. Admin Panel

Admin dashboard must include:

```text
Dashboard
Users
Organisations
Roles
Permissions
Plans
Subscriptions
Payments
Social Integrations
AI Providers
AI Models
Usage
Content
Workflows
CMS
SEO
Menus
Pages
Media
Notifications
Email
Security
Audit Logs
System Settings
Feature Flags
```

---

# 41. User Management

Admins can:

* View users
* Search users
* Filter users
* Suspend users
* Activate users
* Verify users
* Reset authentication state
* Force password reset
* Revoke sessions
* Assign platform roles
* View organisations
* View security events

Sensitive information must be protected according to administrator permission.

---

# 42. Organisation Administration

Admins can:

* View organisations
* Search
* Filter
* Suspend
* Activate
* Manage limits
* View subscription
* View usage
* Manage ownership
* Review security events

Administrators must not unnecessarily expose private user content.

---

# 43. Plan Management

Plans must be completely admin-driven.

Admin can create unlimited plans.

Plan configuration can define:

* Name
* Description
* Price
* Currency
* Billing period
* Trial
* Social account limit
* Page limit
* Post limit
* Daily post limit
* Monthly post limit
* AI usage
* Image generation
* Workflow limit
* Workflow executions
* Team members
* Organisations
* Storage
* Analytics retention
* API access
* Custom providers
* SSO
* 2FA
* Approval workflows
* Automation
* Advanced analytics
* Feature permissions

No business limits should be hardcoded into application logic.

---

# 44. Default Free Plan

The default Free Plan must be created during first installation.

```text
Plan: Free

Social Accounts:
1

Posts:
1 post/day

Duration:
30 days

After expiry:
Purchase required for continued restricted functionality.
```

All plan restrictions must be enforced server-side.

---

# 45. Subscription System

Subscription states:

* Trial
* Active
* Past Due
* Grace Period
* Cancelled
* Expired
* Suspended

The system must correctly handle:

* Renewal
* Upgrade
* Downgrade
* Cancellation
* Failed payment
* Refund
* Webhook events

---

# 46. Razorpay

Implement real Razorpay integration.

Support:

* Customer creation
* Plan/subscription mapping
* Checkout
* Payment verification
* Subscription status
* Webhooks
* Failed payments
* Refunds where supported
* Payment history

Never trust browser-provided payment success.

Server-side verification is mandatory.

---

# 47. Cashfree

Implement real Cashfree integration.

Support:

* Payment creation
* Checkout
* Payment verification
* Webhooks
* Payment status
* Refund workflow where supported
* Transaction history

Payment webhooks must be authenticated and idempotent.

---

# 48. Payment Security

Implement:

* Signature verification
* Webhook verification
* Idempotency
* Transaction state machine
* Duplicate event protection
* Audit logging
* Secure payment references
* No card storage
* No sensitive payment data storage

---

# 49. Dynamic Public Website

PRAVAH must include a complete public website.

Pages:

* Home
* About
* Pricing
* Contact
* Features
* Integrations
* Blog
* FAQ
* Terms & Conditions
* Privacy Policy
* Refund Policy
* Cookie Policy
* Security
* Other admin-created pages

All pages must be database-driven.

---

# 50. Visual CMS

Admin must have a no-code/low-code website builder.

Capabilities:

* Drag & drop sections
* Blocks
* Components
* Text
* Images
* Buttons
* Cards
* Forms
* Tables
* Pricing sections
* Testimonials
* FAQ
* Hero sections
* Footers
* Headers
* Navigation
* Custom sections

Support:

* Desktop preview
* Tablet preview
* Mobile preview
* Responsive controls
* Spacing
* Typography
* Visibility
* Layout
* Background
* Borders
* Shadows

---

# 51. CMS Versioning

Pages must support:

* Draft
* Preview
* Publish
* Unpublish
* Revision history
* Restore previous version
* Scheduled publishing

No content should be destroyed accidentally.

---

# 52. SEO

Implement complete SEO architecture.

Support:

* Page title
* Meta description
* Canonical URL
* Open Graph
* Twitter/X metadata
* Robots directives
* Sitemap
* Robots.txt
* Structured data
* Breadcrumb schema
* Article schema
* Organisation schema
* SoftwareApplication schema
* FAQ schema where valid
* Dynamic URLs
* Slugs
* Redirects
* 404
* 301
* 302

SEO configuration must be admin manageable.

---

# 53. Dynamic Navigation

Admin can manage:

* Header
* Footer
* Menus
* Submenus
* External links
* Internal links
* CTA buttons

Navigation must update dynamically without code changes.

---

# 54. Contact System

Contact page must provide configurable forms.

Fields can be dynamically configured.

Support:

* Validation
* Spam protection
* Rate limiting
* Email notification
* Database storage
* Admin management
* Status
* Notes

---

# 55. Form Builder

Admin can create custom forms.

Support:

* Text
* Email
* Phone
* Number
* Select
* Multi-select
* Checkbox
* Radio
* Textarea
* File upload
* Consent

Forms must have:

* Validation
* Submission tracking
* Spam protection
* Rate limiting
* Notification rules

---

# 56. Modern UI Requirements

PRAVAH must have a premium modern SaaS interface.

Design principles:

* Clean typography
* Consistent spacing
* Responsive layouts
* Modern cards
* Subtle animation
* Accessible contrast
* Keyboard accessibility
* Loading states
* Skeleton states
* Empty states
* Error states
* Success states

Do not use browser-native:

```javascript
alert()
confirm()
prompt()
```

Instead use application-native:

* Modal
* Dialog
* Drawer
* Toast
* Confirmation dialog

---

# 57. Responsive Design

Support:

* Desktop
* Laptop
* Tablet
* Mobile

Mobile dashboard should use:

* Collapsible sidebar
* Bottom actions where appropriate
* Touch-friendly controls
* Responsive tables
* Mobile-friendly visual workflow editor
* Responsive calendar
* Responsive content editor

---

# 58. Accessibility

Target WCAG 2.2 AA.

Support:

* Keyboard navigation
* Focus management
* Screen readers
* Semantic HTML
* ARIA where appropriate
* Accessible dialogs
* Accessible form validation
* Reduced motion
* Sufficient contrast

---

# 59. Security Architecture

Security must be a first-class architectural concern.

Implement:

* Secure authentication
* RBAC
* Tenant isolation
* Encryption at rest
* Encryption in transit
* Secret management
* Secure cookies
* CSRF protection
* XSS protection
* SQL injection protection
* SSRF protection
* Command injection protection
* File upload validation
* MIME validation
* Malware scanning where appropriate
* Rate limiting
* Abuse protection
* Request validation
* Output encoding
* Security headers
* CSP
* HSTS
* Audit logging

---

# 60. Data Encryption

Sensitive fields must be encrypted.

Examples:

* OAuth access tokens
* Refresh tokens
* API keys
* AI provider keys
* SSO secrets
* Webhook secrets
* SMTP passwords
* Payment credentials

Encryption keys must not be stored alongside encrypted secrets.

Use proper key-management architecture.

---

# 61. Audit Logs

Audit events:

* Login
* Logout
* Failed login
* Password change
* Password reset
* 2FA changes
* SSO changes
* Organisation creation
* Organisation changes
* Member changes
* Role changes
* Permission changes
* Social account connection
* Social account disconnection
* Content creation
* Content modification
* Content publishing
* Workflow execution
* Provider changes
* Plan changes
* Payment events
* Administrative actions

Audit records should include:

* Actor
* Organisation
* Action
* Target
* Timestamp
* IP where appropriate
* User agent where appropriate
* Result
* Relevant metadata

---

# 62. Session Management

Users must be able to view:

* Current sessions
* Devices
* Approximate login information
* Last activity
* Session creation date

Allow:

* Revoke individual session
* Revoke all sessions

Security-sensitive changes may automatically revoke sessions.

---

# 63. API Architecture

Provide secure APIs for:

* Authentication
* Users
* Organisations
* Social accounts
* Pages
* Content
* Calendar
* AI
* Workflows
* Analytics
* Billing
* CMS
* Administration

API security must include:

* Authentication
* Authorisation
* Validation
* Rate limiting
* Tenant enforcement
* Audit logging where appropriate

---

# 64. Webhooks

Support inbound/outbound webhooks where required.

Webhook architecture must include:

* Signing
* Verification
* Replay protection
* Idempotency
* Retry policy
* Delivery status
* Failure logs

---

# 65. Background Jobs

Long-running operations must execute through a background job architecture.

Examples:

* Social synchronisation
* AI generation
* Image generation
* Content publishing
* Analytics synchronisation
* Email
* Webhooks
* Workflow execution
* Report generation

Jobs must support:

* Queue
* Retry
* Backoff
* Dead-letter handling
* Cancellation
* Timeout
* Idempotency

---

# 66. Reliability

The platform must handle:

* API timeout
* Provider outage
* Social API outage
* Database errors
* Queue failure
* Network failure
* Expired token
* Invalid response
* Duplicate request
* Concurrent execution

Users must receive meaningful status information.

---

# 67. Observability

Implement:

* Structured logs
* Error tracking
* Metrics
* Health checks
* Readiness checks
* Liveness checks
* Queue monitoring
* Database monitoring
* Integration monitoring
* AI provider monitoring

Sensitive information must never appear in logs.

---

# 68. Admin System Health

Admin dashboard should display:

* Application health
* Database health
* Queue health
* Storage health
* Social integration health
* AI provider health
* Email health
* Payment provider health
* Error rate
* Job failures
* API latency

---

# 69. Feature Flags

Features must be controlled through database-driven feature flags.

Support:

* Global enable/disable
* Plan-based feature availability
* Organisation-level feature availability
* User-level overrides where authorised

Do not hardcode feature availability throughout the application.

---

# 70. Internationalisation

Architecture must support:

* Multiple languages
* Multiple currencies
* Multiple timezones
* Localised date/time
* Localised number formatting

Initial UI may use English, but architecture must not prevent Hindi and other languages.

---

# 71. Timezone Architecture

Every organisation must have a timezone.

Scheduling must correctly handle:

* DST where applicable
* Organisation timezone
* User timezone
* Social platform timezone
* UTC backend storage

Store timestamps in UTC and convert for presentation/execution appropriately.

---

# 72. Database Requirements

Database architecture must support production workloads.

Core entities include:

```text
User
UserCredential
Session
VerificationToken
OTP
TwoFactorCredential
RecoveryCode
SSOProvider
Organisation
OrganisationMember
Team
Role
Permission
RolePermission
SocialProvider
SocialAccount
SocialPage
SocialToken
SocialProfile
SocialProfileSummary
Content
ContentAsset
ContentVersion
ContentApproval
ContentSchedule
Campaign
Workflow
WorkflowNode
WorkflowEdge
WorkflowExecution
WorkflowNodeExecution
AIProvider
AIModel
AIUsage
Plan
PlanFeature
Subscription
Payment
PaymentTransaction
PaymentWebhook
Notification
NotificationPreference
AuditLog
Dashboard
DashboardWidget
CMSPage
CMSRevision
CMSBlock
Menu
Form
FormField
FormSubmission
SEOConfiguration
SystemSetting
FeatureFlag
Webhook
Job
JobExecution
```

Database relationships must enforce ownership and integrity.

---

# 73. Tenant Isolation

Every tenant-sensitive query must enforce organisation scope.

Never rely solely on:

```text
WHERE id = ?
```

Use organisation-aware authorization.

Example conceptual rule:

```text
organisation_id = currentOrganisation.id
AND resource_id = requestedResource.id
AND user has required permission
```

This validation must occur server-side.

---

# 74. Data Retention

Admin must configure retention policies for:

* Audit logs
* Analytics
* Workflow execution logs
* Notifications
* Content versions
* Deleted records
* Payment records

Legal/accounting retention requirements must be respected.

---

# 75. Account Deletion

Users must be able to request account deletion according to system policy.

Deletion must consider:

* Organisations
* Ownership
* Social connections
* Content
* Billing
* Audit requirements
* Legal retention

Do not delete legally required records prematurely.

---

# 76. Organisation Deletion

Organisation owners/admins with permission may request deletion.

Use confirmation modal.

Provide:

* Warning
* Required confirmation
* Optional reauthentication
* Grace period if configured
* Audit event

---

# 77. Social Disconnect

Disconnecting a social account must:

* Revoke where supported
* Remove active publishing ability
* Preserve required historical analytics/content references
* Remove/rotate stored tokens
* Stop related workflows
* Prevent future publishing

---

# 78. Content Safety

Before automatic publishing, content should pass configurable validation.

Checks may include:

* Empty content
* Platform character limits
* Unsupported media
* Invalid URLs
* Missing permissions
* Expired connection
* Organisation policy
* AI safety policy
* Spam-like repetition
* Duplicate content

The system should block or request review when appropriate.

---

# 79. Duplicate Prevention

PRAVAH must prevent accidental duplicate posts.

Use:

* Content fingerprints
* Platform/account/time checks
* Publishing idempotency keys
* Provider response tracking

Intentional duplicate cross-platform publishing must remain possible where supported.

---

# 80. Emergency Controls

Every organisation must have an emergency control to:

* Pause all publishing
* Pause workflows
* Disable automation
* Disable specific social account
* Disable specific campaign

Super Admin must have emergency platform-level controls.

---

# 81. Billing Usage Metering

Usage must be calculated from actual events.

Examples:

```text
Connected Social Accounts
Published Posts
AI Requests
Generated Images
Workflow Executions
Storage
Team Members
```

Usage must update reliably and must not be based on frontend counters.

---

# 82. Plan Enforcement

Plan enforcement must occur before resource-consuming operations.

Example:

```text
User requests AI image
        ↓
Authenticate
        ↓
Authorise
        ↓
Identify Organisation
        ↓
Load Subscription
        ↓
Check Plan
        ↓
Check Usage
        ↓
Reserve Usage
        ↓
Execute
        ↓
Commit Usage
```

Failed operations must not incorrectly consume successful-use quotas.

---

# 83. Admin Configuration

Admin should be able to configure without modifying source code:

* Branding
* Logo
* Favicon
* Colours/theme
* Public pages
* Navigation
* SEO
* Plans
* Pricing
* Payment providers
* AI providers
* Social providers
* Authentication methods
* Email settings
* Security policies
* Feature flags
* Notifications
* Legal pages
* System settings

---

# 84. Branding

Admin can configure:

* Product name
* Logo
* Favicon
* Light logo
* Dark logo
* Primary colour
* Secondary colour
* Typography
* Login branding
* Email branding
* Public website branding

Branding should dynamically propagate throughout the application.

---

# 85. Email System

Transactional email templates must be dynamic.

Examples:

* Welcome
* Email verification
* OTP
* Password reset
* Magic link
* Login alert
* Invitation
* Subscription
* Payment
* Publishing failure
* Workflow failure

Admin can configure templates.

---

# 86. Search

Global search should support relevant authorised resources:

* Organisations
* Users
* Social accounts
* Pages
* Posts
* Campaigns
* Workflows
* Analytics
* Media

Search results must respect RBAC and tenant isolation.

---

# 87. Import/Export

Support secure export where appropriate:

* Content
* Analytics
* Media metadata
* Workflows
* Organisation configuration

Exports must respect permissions.

---

# 88. API Rate Limits

Implement separate limits for:

* Authentication
* Public APIs
* User APIs
* Organisation APIs
* AI APIs
* Webhooks
* Publishing
* Admin APIs

Limits must be configurable.

---

# 89. Error Handling

Every API must return structured errors.

Frontend must show application-native error states.

Never expose:

* Stack traces
* Database details
* Secrets
* Internal provider credentials
* Infrastructure details

to normal users.

---

# 90. UI State Management

Every asynchronous operation must support:

* Loading
* Success
* Error
* Retry
* Empty
* Disabled

No fake loading followed by fake success.

---

# 91. Modal System

Create a reusable application modal system.

Use it for:

* Confirmation
* Delete
* Disconnect
* Payment actions
* Settings
* Form dialogs
* Workflow configuration
* Content preview
* Errors
* Security confirmation

Do not use native browser dialogs.

---

# 92. Onboarding

After registration:

```text
Registration
↓
Verification
↓
Organisation creation
↓
Brand setup
↓
Connect social account
↓
AI profile analysis
↓
Content preferences
↓
Posting preferences
↓
Dashboard
```

Users must be able to skip optional onboarding steps where appropriate.

---

# 93. Organisation Onboarding

Ask:

* Organisation name
* Industry
* Website
* Description
* Target audience
* Preferred language
* Brand tone
* Content categories
* Posting frequency
* Preferred posting hours

These settings become AI context.

---

# 94. Social Onboarding

User can connect one or more permitted social platforms based on their plan.

After connection:

* Synchronise profile
* Retrieve available pages/accounts
* Save permitted metadata
* Generate AI profile summary
* Configure posting preferences

---

# 95. Content Strategy

Users can configure:

* Content pillars
* Topics
* Keywords
* Excluded topics
* Tone
* Language
* CTA
* Hashtag strategy
* Posting frequency

AI generation must respect these settings.

---

# 96. AI Content Review

Before publishing, users can inspect:

* Generated text
* Generated image
* Platform
* Account
* Scheduled time
* AI provider
* Model
* Generation timestamp

Users can regenerate or edit content.

---

# 97. Human Control

Even when automatic publishing is enabled, users must be able to:

* Pause automation
* Edit scheduled content
* Cancel scheduled content
* Disable individual accounts
* Disable individual workflows
* Require approval

Automation must never remove user control.

---

# 98. Public Pricing

Pricing page must be generated from actual admin-configured plans.

No hardcoded pricing.

Display:

* Plan
* Price
* Billing period
* Included features
* Limits
* CTA
* Trial where applicable

---

# 99. Legal Pages

Admin must be able to manage:

* Terms & Conditions
* Privacy Policy
* Refund Policy
* Cookie Policy
* Acceptable Use Policy
* AI Usage Policy
* Social Media Automation Policy

Version legal documents.

Record user acceptance where legally/operationally required.

---

# 100. Privacy

Privacy architecture must follow data minimisation.

Provide mechanisms for:

* Consent
* Data access
* Data correction
* Data deletion
* Data export
* Privacy preferences

Do not use personal/social data for unrelated purposes without appropriate consent/legal basis.

---

# 101. Compliance Architecture

Design for applicable requirements including, where relevant:

* GDPR
* Indian privacy/data protection requirements
* Applicable payment regulations
* Social platform developer policies
* AI provider policies

Actual legal compliance must be reviewed and configured according to deployment jurisdiction.

---

# 102. Social Platform Compliance

Each platform integration must have an integration-specific capability matrix.

For example:

```text
Platform
├── Account connection
├── Page connection
├── Text publishing
├── Image publishing
├── Video publishing
├── Analytics
├── Scheduling
├── Comments
└── Other capabilities
```

Only expose capabilities that the official API actually permits.

---

# 103. Provider Capability System

Every integration must declare capabilities dynamically.

Example:

```text
supports_text
supports_image
supports_video
supports_carousel
supports_pages
supports_analytics
supports_scheduling
supports_comments
```

The UI must dynamically hide unavailable capabilities.

---

# 104. No-Code Component Architecture

Visual components must be metadata-driven.

Every node/component should define:

```text
id
type
name
description
category
inputs
outputs
configurationSchema
permissions
planRequirements
executionHandler
validation
```

A node without a real execution handler must not be available as a functional node.

---

# 105. Workflow Versioning

Every workflow must support:

* Draft
* Published version
* Version history
* Restore
* Duplicate
* Disable
* Enable

Published workflows must remain stable while drafts are edited.

---

# 106. Workflow Testing

Provide safe workflow testing.

Testing must use:

* Real configured providers
* Real configured accounts where appropriate
* Sandbox/test mode where officially supported

Never label simulated results as real results.

---

# 107. Workflow Execution Safety

Before execution:

```text
Validate Workflow
↓
Validate Permissions
↓
Validate Plan
↓
Validate Credentials
↓
Validate Platform Capability
↓
Validate Content
↓
Execute
```

---

# 108. Observability Per Workflow

Users should see:

* Execution status
* Start time
* Duration
* Nodes executed
* Successful nodes
* Failed nodes
* Error reason
* Retry
* Logs excluding secrets

---

# 109. Admin AI Provider Marketplace

Admin should be able to configure a catalogue of providers/models.

Each provider should expose:

* Name
* Logo
* Capabilities
* Models
* Cost information
* Availability
* Status
* Configuration requirements

---

# 110. User AI Provider

Users with permission can configure their own provider.

Secrets belong to the user or organisation depending on selected scope.

Provider scope:

```text
User
Organisation
Platform
```

---

# 111. Provider Failure Handling

If a configured AI provider fails:

```text
Primary Provider
      ↓
Retry
      ↓
Configured Fallback
      ↓
Retry
      ↓
Failure
```

Fallback must only occur according to administrator/user configuration and plan permissions.

---

# 112. Data Synchronisation

Social data synchronisation must be incremental where possible.

Track:

* Last sync
* Sync status
* Cursor/page information where supported
* Errors
* Retry count

Avoid unnecessary API calls.

---

# 113. API Quota Management

Track provider/platform quota usage where information is available.

Prevent uncontrolled API consumption.

Implement:

* Rate limit handling
* Backoff
* Queueing
* Throttling
* Retry

---

# 114. Security Notifications

Notify users/admins about:

* New login
* Password change
* 2FA change
* SSO change
* Provider key change
* Social account connection
* Social account disconnection
* Suspicious activity
* Session revocation

---

# 115. Admin Audit

Super Admin must have immutable/auditable administrative history.

Administrators must not be able to silently modify or erase security-critical audit records.

---

# 116. Backup and Recovery

Production deployment must support:

* Database backup
* Configuration backup
* Media backup
* Backup verification
* Restore procedure

Credentials and secrets must not be exposed in backups.

---

# 117. Disaster Recovery

Architecture should define:

* RPO
* RTO
* Backup frequency
* Restore procedure
* Failure handling
* Dependency failure strategy

These values should be configurable according to deployment requirements.

---

# 118. Performance

Target:

* Fast initial application load
* Optimised API calls
* Pagination
* Lazy loading
* Caching where safe
* Background processing
* Database indexing
* Efficient queries

Do not load entire datasets unnecessarily.

---

# 119. Scalability

Architecture must support scaling:

```text
Frontend
    ↓
API Layer
    ↓
Application Services
    ↓
Queue
    ↓
Workers
    ↓
External Providers
```

Workers must be horizontally scalable.

---

# 120. Multi-Tenant Billing

Billing belongs to the organisation.

Users may have different roles, but subscription ownership must be organisation-aware.

Plan limits must apply to the organisation according to the configured plan model.

---

# 121. Agency Model

Agencies must be able to create multiple organisations/clients according to their plan.

Organisation switching must be secure.

Never mix:

```text
Client A
```

with:

```text
Client B
```

data.

---

# 122. White-Label Architecture

Architecture should allow future white-label functionality.

Potential configuration:

* Product name
* Domain
* Logo
* Theme
* Email branding
* Public website
* Login page
* Favicon

White-label availability must be controlled by plan.

---

# 123. Admin Metrics

Admin dashboard should provide:

* Total users
* Active users
* Organisations
* Active subscriptions
* Revenue
* Payments
* AI usage
* Social connections
* Published posts
* Workflow executions
* Errors
* Provider usage

All values must come from real data.

---

# 124. Security Testing

Before production release, test:

* Authentication
* Authorisation
* RBAC
* Tenant isolation
* IDOR
* CSRF
* XSS
* SQL injection
* SSRF
* File upload
* Rate limiting
* Session handling
* OAuth security
* Webhook verification
* Payment verification
* Secret exposure
* Workflow isolation

---

# 125. Automated Testing

Provide:

### Unit Tests

For:

* Services
* Validators
* Permissions
* Billing
* Usage
* Scheduling
* Workflow execution

### Integration Tests

For:

* Database
* Authentication
* OAuth
* Payments
* AI providers
* Social integrations

### End-to-End Tests

For:

* Registration
* Verification
* Login
* Forgot password
* 2FA
* Organisation creation
* Social connection
* Content creation
* Workflow creation
* Scheduling
* Publishing
* Billing
* Admin operations

---

# 126. Production Quality Gate

The application must not be considered complete until:

```text
Install
✓

Setup
✓

Database
✓

Authentication
✓

RBAC
✓

Multi-tenancy
✓

Social APIs
✓

AI providers
✓

Workflow engine
✓

Content generation
✓

Scheduling
✓

Publishing
✓

Analytics
✓

Billing
✓

CMS
✓

SEO
✓

Security
✓

Testing
✓

Build
✓

Deployment
✓
```

All advertised functionality must work against real implementations.

---

# 127. Definition of Done

A feature is considered complete only when:

1. Database model exists.
2. Backend implementation exists.
3. Authorization exists.
4. Validation exists.
5. Frontend exists.
6. Loading state exists.
7. Error state exists.
8. Empty state exists where applicable.
9. Audit logging exists where applicable.
10. Tests exist.
11. API integration works.
12. Data persists correctly.
13. Tenant isolation is enforced.
14. Plan restrictions are enforced.
15. Mobile UI works.
16. Accessibility is addressed.
17. Security requirements are satisfied.
18. No fake/mock implementation remains.
19. No placeholder functionality is exposed.
20. Production build succeeds.

---

# 128. Core User Journey

```text
Visit PRAVAH
      ↓
Public Website
      ↓
Register / Login
      ↓
Email / OTP Verification
      ↓
Dashboard
      ↓
Create Organisation
      ↓
Configure Organisation
      ↓
Connect Social Account
      ↓
Synchronise Profile
      ↓
AI Profile Analysis
      ↓
Configure Content Strategy
      ↓
Select AI Provider
      ↓
Configure Posting Frequency
      ↓
Generate Content
      ↓
Review / Approve
      ↓
Create Schedule
      ↓
Automatic Publishing
      ↓
Collect Analytics
      ↓
AI Performance Analysis
      ↓
Optimise Future Content
```

---

# 129. Core Automated Content Journey

```text
User Configuration
       ↓
Organisation Profile
       ↓
Social Profile Intelligence
       ↓
Historical Analytics
       ↓
AI Recommendation Engine
       ↓
Best Posting Window
       ↓
Content Topic Selection
       ↓
AI Text Generation
       ↓
AI Image Generation
       ↓
Content Validation
       ↓
Plan Validation
       ↓
Permission Validation
       ↓
Approval Requirement
       ↓
Schedule
       ↓
Official Social API
       ↓
Publish
       ↓
Verify Result
       ↓
Store Published Post
       ↓
Collect Analytics
       ↓
AI Analysis
       ↓
Improve Recommendation
```

---

# 130. Core Product Differentiation

PRAVAH must not simply be another social media scheduler.

Its core differentiation is:

```text
Social Management
        +
AI Content Intelligence
        +
Profile Intelligence
        +
Automatic Publishing
        +
No-Code Workflow Automation
        +
400+ AI Provider Architecture
        +
Multi-Tenant Organisation System
        +
Visual Dashboard Builder
        +
Visual Workflow Builder
        +
AI Recommendation Engine
        +
Enterprise Security
        +
Dynamic SaaS CMS
        +
Admin-Controlled SaaS Platform
```

---

# 131. Primary Product Navigation

```text
Overview

Create
├── AI Writer
├── Image Studio
├── Content Composer
└── Templates

Content
├── Posts
├── Drafts
├── Scheduled
├── Published
└── Calendar

Social
├── Accounts
├── Pages
└── Connections

Automation
├── Workflows
├── Executions
├── Templates
└── Triggers

Analytics
├── Overview
├── Accounts
├── Posts
├── Campaigns
└── AI Insights

Campaigns

Media

Team

Billing

Settings
├── Organisation
├── Profile
├── Security
├── AI Providers
├── Notifications
├── Integrations
└── Preferences
```

---

# 132. Admin Navigation

```text
Admin Dashboard

Users
Organisations
Roles & Permissions

Plans
Subscriptions
Payments
Transactions

Social Platforms
AI Providers
AI Models

Content
Campaigns
Workflows

CMS
├── Pages
├── Navigation
├── Forms
├── Media
├── SEO
└── Legal

Notifications
Email Templates

Security
├── Authentication
├── SSO
├── 2FA
├── Sessions
├── Rate Limits
└── Audit Logs

System
├── General
├── Branding
├── Storage
├── Email
├── Feature Flags
└── Health
```

---

# 133. Product UX Standard

Every screen must feel like part of one cohesive product.

Required UX states:

```text
Loading
Empty
Populated
Saving
Saved
Error
Retry
Disabled
Permission Denied
Plan Limit
Expired Subscription
Connection Expired
Integration Unavailable
```

All destructive operations require application-native confirmation dialogs.

---

# 134. Security Priority Order

PRAVAH engineering decisions must prioritise:

```text
1. User safety
2. Data privacy
3. Tenant isolation
4. Authentication
5. Authorisation
6. Secret protection
7. Platform compliance
8. Payment security
9. Reliability
10. Performance
11. Convenience
```

Convenience must never override security or ethical requirements.

---

# 135. Final Product Requirement

PRAVAH must ultimately function as a complete production SaaS platform where:

* A real user can register.
* A real user can verify their account.
* A real user can login securely.
* A real user can recover their account.
* A real user can enable 2FA/passwordless/magic-link authentication where configured.
* A real user can create an organisation.
* Multiple users can work inside the organisation.
* RBAC actually prevents unauthorised operations.
* A real social account can be connected through an official API.
* Real permitted profile data can be synchronised.
* AI can analyse that data.
* AI can generate real content.
* AI can generate real images through configured providers.
* Users can visually construct real workflows.
* Workflows actually execute on the backend.
* Real schedules are persisted.
* Real posts are published through permitted official APIs.
* Real analytics are collected.
* Plans actually control usage.
* Razorpay and Cashfree process real payments.
* Subscriptions actually change access.
* Administrators can manage the entire platform dynamically.
* Public website content can be managed without source-code changes.
* SEO can be managed dynamically.
* Every organisation remains isolated.
* Security events are auditable.
* Failures are visible and recoverable.
* Users retain control over automation.
* The platform does not facilitate spam, deception, unauthorised access, platform abuse or unethical automation.

**PRAVAH is therefore defined as a real, secure, extensible, multi-tenant AI social-media operating system rather than a conventional social media scheduling application.**
