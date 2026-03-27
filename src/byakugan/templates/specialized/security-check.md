# Security Review — Working Standards

## Mindset
Think like an attacker. For every input the system receives, ask: what can an adversary control here, and what could they cause to happen as a result? Security issues are not theoretical — they are the bugs that make headlines, destroy data, and end careers. Find them before deployment.

## The Core Principle
All external data is hostile until proven otherwise. This includes: HTTP request bodies, query parameters, headers, cookies, file uploads, environment variables from external sources, data read from a database that was written by external users, webhook payloads, and CLI arguments.

## Input Validation Checklist

**Every external input must be:**
- [ ] Validated for type, format, length, and allowed values before use.
- [ ] Rejected with a clear error if invalid — never silently coerced or ignored.
- [ ] Never interpolated directly into SQL, shell commands, file paths, or HTML output.
- [ ] Stripped of null bytes, path traversal sequences (`../`), and control characters where applicable.

## OWASP Top 10 — Verification Points

### Injection (SQL, NoSQL, OS, LDAP)
- Are all database queries parameterized? Check every `.query()`, `.execute()`, `.raw()` call.
- Are shell commands constructed with argument arrays (not string interpolation)?
- Is any user input ever passed to `eval()`, `exec()`, `system()`, or template engines without sanitization?

### Authentication
- Are passwords hashed with bcrypt/Argon2id? Not MD5, SHA1, or SHA256.
- Are session tokens invalidated on logout, privilege change, and password reset?
- Is there brute-force protection (rate limiting, lockout) on the login endpoint?
- Are password reset tokens single-use and time-limited?

### Authorization
- Is authorization checked at the resource level (can this user access this specific record), not just at the route level?
- Can a user access another user's data by changing an ID in the request?
- Are admin/privileged endpoints protected from regular users?
- Is there a test case that verifies an unauthorized user receives a 403?

### Sensitive Data Exposure
- Are any secrets, tokens, or PII appearing in logs?
- Are any secrets committed to the repository or hardcoded in configuration?
- Is sensitive data in URL parameters (it will be in access logs and browser history)?
- Is data encrypted at rest in the database for the most sensitive fields?
- Is HTTPS enforced with HSTS headers?

### Security Misconfiguration
- Is debug mode disabled in production?
- Do error responses leak stack traces, DB error messages, or internal paths?
- Is CORS configured with an explicit allowlist, not `*` for authenticated APIs?
- Are security headers set: `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`?

### Cross-Site Scripting (XSS)
- Is user-provided content HTML-escaped before rendering in templates?
- Is `innerHTML`, `dangerouslySetInnerHTML`, or `v-html` used with user data?
- Is a Content Security Policy (`Content-Security-Policy` header) configured?
- If rich HTML is required, is it processed through a sanitizer (DOMPurify)?

### Insecure Deserialization
- Is any untrusted data deserialized using `pickle`, Java's `ObjectInputStream`, PHP `unserialize`, or similar?
- Is the data source of deserialized objects verified?

### Known Vulnerabilities in Dependencies
- Has `npm audit` / `pip audit` / `cargo audit` / `bundle audit` been run?
- Are there any high or critical severity CVEs in current dependencies?

### Logging and Monitoring
- Are authentication failures logged?
- Are authorization failures logged?
- Are there alerts configured for unusual authentication patterns?

## File Upload Security
- [ ] File type validated by content (magic bytes), not by extension or MIME type header.
- [ ] File size limited.
- [ ] Files stored outside the web root and not directly accessible via URL.
- [ ] Files renamed on storage — user-provided filename never used on disk.
- [ ] Malware scanning for high-risk deployments.

## Secrets Audit
- [ ] No secrets in source code (run `truffleHog` or `gitleaks`).
- [ ] No secrets in committed `.env` files, config files, or documentation.
- [ ] All secrets rotatable without a code deployment.
- [ ] Secrets are scoped: a key for service A cannot access service B's resources.

## CSRF Protection
- [ ] State-changing operations protected by CSRF tokens or `SameSite=Strict`/`Lax` cookie attribute.
- [ ] `Origin` or `Referer` header verified for state-changing API calls where applicable.

## Rate Limiting
- [ ] Login, password reset, account creation, and any expensive operation are rate-limited.
- [ ] The rate limit returns a `429` with a `Retry-After` header.
- [ ] Rate limits are stricter for unauthenticated requests.

## Reporting Findings
For each issue found, document:
1. **Location**: file, line number, or endpoint.
2. **Severity**: Critical / High / Medium / Low.
3. **Impact**: what an attacker can achieve.
4. **Evidence**: the specific code or configuration that is vulnerable.
5. **Remediation**: the specific change required to fix it.
