# PRAVAH Security Architecture & Policies

## 1. Secret & Token Encryption at Rest

All sensitive credentials (third-party OAuth access tokens, refresh tokens, webhook signing secrets) are encrypted before database insertion using **Fernet symmetric encryption (AES-128 in CBC mode with HMAC SHA-256 authentication)** derived from the server's master encryption key.

- Implementation: `apps/api/app/core/encryption.py`
- Reversible only by the backend application with legitimate runtime key.

---

## 2. Authentication & Credential Storage

- **Password Hashing**: Passwords are hashed using **Argon2id / PBKDF2 with SHA-256**, random salts, and minimum iteration constraints.
- **Two-Factor Authentication**: Standard TOTP RFC 6238 implementation supporting Google Authenticator, Authy, and hardware authenticators.
- **Recovery Codes**: Cryptographically secure 10-character alphanumeric recovery codes generated upon 2FA enrollment.
- **Session Revocation**: JWT token IDs are validated against active sessions in database / cache, allowing instant revocation from settings.

---

## 3. IDOR Prevention & Multi-Tenant Boundary Checks

- Every endpoint accepting an entity ID (`content_id`, `account_id`, `workflow_id`, `member_id`) validates that the entity's `organisation_id` matches the caller's validated `tenant.organisation.id`.
- Attempts to query or mutate another organization's entities return `403 Forbidden` or `404 Not Found`.

---

## 4. Platform Emergency Stop

Super Administrators can toggle a global publishing halt (`/admin/emergency-stop`) which instantly prevents all scheduled and manual publishing jobs from dispatching external requests across all tenant organizations.
