# Security Policy

## Supported Versions

Currently supported versions for security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Security Features

### Authentication & Authorization
- **Status**: ⚠️ Not Implemented (Planned for v0.4)
- **Recommendation**: Deploy behind an authentication proxy (e.g., nginx with Basic Auth, OAuth2 Proxy)

### CORS Protection
- **Status**: ✅ Implemented
- **Configuration**: Set `ALLOWED_ORIGINS` environment variable
- **Default**: Localhost only (`http://localhost:8080`, `http://127.0.0.1:8080`)
- **Production**: MUST specify exact origins (never use `*`)

### File Upload Security
- **Status**: ✅ Implemented
- **Protections**:
  - File type validation (whitelist: `.csv`, `.txt`, `.xlsx`, `.xls`, `.tsv`, `.json`)
  - File size limits (default: 100MB, configurable via `MAX_FILE_SIZE_MB`)
  - Filename sanitization (prevents path traversal)
  - Secure random file IDs (cryptographically secure)

### PHI/PII Data Protection
- **Status**: ✅ Implemented
- **Features**:
  - Automatic PHI field detection (HIPAA-compliant patterns)
  - Content-based PHI detection (emails, phones, SSN)
  - Multiple redaction methods:
    - `hash`: SHA-256 hashing with optional salt
    - `mask`: Show last 4 characters only
    - `remove`: Complete redaction
  - Comprehensive audit logging

### API Key Security
- **Status**: ✅ Implemented
- **Protections**:
  - API keys masked in logs (shows `****abcd`)
  - Format validation for API keys
  - Keys never stored in code or version control
  - Environment variable configuration

### Error Handling
- **Status**: ✅ Improved
- **Features**:
  - Specific exception types (no generic catch-all)
  - Detailed logging without exposing sensitive data
  - User-friendly error messages

### Rate Limiting
- **Status**: ⚠️ Planned for v0.4
- **Recommendation**: Use reverse proxy rate limiting (nginx, Cloudflare)

## Reporting a Vulnerability

### Where to Report
**Do NOT open public issues for security vulnerabilities.**

Please report security vulnerabilities via:
1. **Email**: Send details to your security contact email
2. **Private Disclosure**: Use GitHub's private vulnerability reporting (if enabled)

### What to Include
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)
- Your contact information

### Response Timeline
- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 7-14 days
  - High: 14-30 days
  - Medium: 30-60 days
  - Low: 60-90 days

### Disclosure Policy
- We follow **responsible disclosure**
- Security advisories published after patch release
- Credit given to reporters (unless anonymity requested)

## Security Best Practices for Deployment

### Production Deployment Checklist

#### Required Security Measures
- [ ] Set `ALLOWED_ORIGINS` to specific domains (never `*`)
- [ ] Generate and set `PHI_HASH_SALT` (use `secrets.token_hex(32)`)
- [ ] Configure `OPENAI_API_KEY` via environment (never hardcode)
- [ ] Set `MAX_FILE_SIZE_MB` appropriate for your use case
- [ ] Enable `ENABLE_AUDIT_LOGGING=true`
- [ ] Set `LOG_LEVEL=INFO` or `WARNING` (not `DEBUG`)
- [ ] Use HTTPS/TLS for all connections
- [ ] Deploy behind authentication proxy
- [ ] Implement rate limiting (nginx, Cloudflare, etc.)
- [ ] Regular security updates and patches
- [ ] Backup audit logs regularly
- [ ] Restrict file system permissions for upload/output directories

#### Recommended Security Measures
- [ ] Deploy in containerized environment (Docker)
- [ ] Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- [ ] Enable web application firewall (WAF)
- [ ] Implement IP whitelisting if applicable
- [ ] Set up monitoring and alerting (Sentry, DataDog)
- [ ] Regular security audits
- [ ] Penetration testing before production
- [ ] Data retention policies (auto-delete uploads after processing)
- [ ] Encrypt data at rest and in transit
- [ ] Separate production and development environments

### Environment-Specific Configuration

#### Development
```bash
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000
LOG_LEVEL=DEBUG
ENABLE_AUDIT_LOGGING=false
```

#### Staging
```bash
ALLOWED_ORIGINS=https://staging.yourdomain.com
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true
PHI_HASH_SALT=<generate-unique-salt>
```

#### Production
```bash
ALLOWED_ORIGINS=https://app.yourdomain.com,https://dashboard.yourdomain.com
LOG_LEVEL=WARNING
ENABLE_AUDIT_LOGGING=true
PHI_HASH_SALT=<generate-unique-salt>
MAX_FILE_SIZE_MB=50
RATE_LIMIT_PER_MINUTE=30
```

## Known Security Limitations

### Current Version (v0.3.0)
1. **No Built-in Authentication**: Must deploy behind auth proxy
2. **No Rate Limiting**: Use reverse proxy for rate limiting
3. **In-Memory Job Storage**: Jobs lost on restart (persistence planned for v0.4)
4. **No User Management**: Single-tenant deployment only
5. **Limited Input Validation**: Assumes trusted users

### Medical Data Specific
1. **PHI Detection**: Pattern-based (may have false positives/negatives)
2. **Audit Logs**: File-based (not tamper-proof without external protection)
3. **Data Retention**: Manual deletion required (auto-cleanup planned)
4. **Encryption**: At-rest encryption depends on filesystem (not built-in)

## Compliance Considerations

### HIPAA Compliance
⚠️ **This software is NOT HIPAA-compliant out of the box**

To achieve HIPAA compliance, you must:
- [ ] Deploy in HIPAA-compliant infrastructure (AWS HIPAA, Azure Healthcare)
- [ ] Sign Business Associate Agreement (BAA) with cloud provider
- [ ] Implement encryption at rest and in transit
- [ ] Enable comprehensive audit logging
- [ ] Implement access controls and authentication
- [ ] Regular risk assessments
- [ ] Staff training on HIPAA requirements
- [ ] Incident response procedures
- [ ] Data backup and disaster recovery

### GDPR Compliance
For GDPR compliance:
- [ ] Implement data subject rights (access, deletion, portability)
- [ ] Document data processing activities
- [ ] Implement data minimization
- [ ] Privacy by design and default
- [ ] Data protection impact assessment (DPIA)
- [ ] Consent management (if applicable)
- [ ] Data breach notification procedures

## Security Updates

### How to Stay Updated
1. Watch this repository for security advisories
2. Subscribe to release notifications
3. Check `CHANGES.md` for security-related updates
4. Follow semantic versioning for security patches

### Update Policy
- **Security patches**: Released ASAP for supported versions
- **Breaking security changes**: Major version updates
- **Non-breaking security improvements**: Minor version updates

## Additional Resources

### Security Tools
- **Static Analysis**: Run `ruff check` for code quality
- **Dependency Scanning**: Use `pip-audit` or Dependabot
- **Secret Scanning**: Use `detect-secrets` or GitHub secret scanning
- **Container Scanning**: Use Trivy or Snyk for Docker images

### Further Reading
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [GDPR Compliance](https://gdpr.eu/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Contact

For security-related questions (non-vulnerabilities):
- Open a GitHub Discussion
- Email: [Your security contact email]

For security vulnerabilities:
- **DO NOT** open public issues
- Use private disclosure methods described above

---

**Last Updated**: 2025-10-17
**Version**: 0.3.0
