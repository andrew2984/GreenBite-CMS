# Security-by-Design Implementation Documentation

## Overview
This document outlines the comprehensive security-by-design principles implemented in the GreenBite CMS application. All security measures follow industry best practices and OWASP guidelines.

---

## 1. Password Security

### Implementation
- **Password Hashing**: All passwords are hashed using bcrypt with a cost factor of 12
- **No Plaintext Storage**: Passwords are NEVER stored in plaintext in the database
- **Secure Verification**: Password verification uses constant-time comparison via bcrypt

### Location
- `src/security/security_utils.py`: `PasswordHasher` class
- `src/objs/user/obj_user.py`: `set_password()` and `check_password()` methods

### Password Requirements
- Minimum 8 characters
- Maximum 128 characters  
- Must contain: uppercase, lowercase, and numbers
- Enforced at registration via `InputValidator.validate_password()`

---

## 2. Input Validation & Sanitization

### Implementation
All user inputs are validated and sanitized before processing:

#### Email Validation
- Regex pattern matching for proper email format
- Maximum 255 characters
- Case normalization (lowercase)

#### Username Validation
- 3-50 characters
- Alphanumeric, hyphens, and underscores only
- Regex pattern: `^[a-zA-Z0-9_-]{3,50}$`

#### Input Sanitization
- HTML entity escaping to prevent XSS attacks
- Length truncation to prevent overflow attacks
- Whitespace trimming

### Location
- `src/security/security_utils.py`: `InputValidator` class
- Applied in all API endpoints before database operations

---

## 3. Authentication & Authorization

### JWT Token-Based Authentication
- **Stateless Authentication**: Using JWT tokens instead of sessions
- **Token Expiration**: 24-hour expiration on all tokens
- **Secure Payload**: Contains user_id, email, role, and permission level
- **Algorithm**: HS256 (HMAC with SHA-256)

### Role-Based Access Control (RBAC)
Three permission levels implemented:
- **Level 0 (Client)**: Can only view/manage their own events
- **Level 1 (Planner)**: Can view/accept assigned events
- **Level 2 (Admin)**: Full system access

### Decorators
- `@require_auth`: Validates JWT token, adds user context to request
- `@require_role(level)`: Enforces minimum permission level

### Location
- `src/security/security_utils.py`: `JWTManager`, `require_auth`, `require_role`
- Applied to all protected endpoints in `auth_server.py`

---

## 4. Rate Limiting

### Implementation
- **Global Limits**: 200 requests/day, 50 requests/hour per IP
- **Login Endpoint**: 10 attempts/minute to prevent brute force
- **Registration Endpoint**: 5 attempts/minute to prevent spam
- **Storage**: In-memory (production should use Redis)

### Location
- `auth_server.py`: Flask-Limiter configuration
- Applied using `@limiter.limit()` decorators

---

## 5. CORS (Cross-Origin Resource Sharing)

### Implementation
- **Restricted Origins**: Only specific origins allowed (configurable via environment)
- **Allowed Methods**: GET, POST, PUT, DELETE only
- **Credentials Support**: Enabled for authenticated requests
- **Headers Control**: Specific headers allowed/exposed

### Configuration
```python
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 
    'http://localhost:3000,http://localhost:5173').split(',')
```

### Location
- `auth_server.py`: CORS configuration with Flask-CORS

---

## 6. Security Headers

### Implementation
All responses include security headers:

- **X-Content-Type-Options**: `nosniff` - Prevents MIME sniffing
- **X-Frame-Options**: `DENY` - Prevents clickjacking
- **X-XSS-Protection**: `1; mode=block` - Enables XSS filter
- **Strict-Transport-Security**: Forces HTTPS (31536000 seconds)
- **Content-Security-Policy**: Restricts resource loading

### Location
- `auth_server.py`: `add_security_headers()` middleware

---

## 7. Secure Error Handling

### Implementation
- **Generic Error Messages**: Internal errors not exposed to users
- **No Email Enumeration**: Login errors don't reveal if email exists
- **Audit Logging**: Failed attempts are logged for monitoring
- **Safe Exception Handling**: Try-catch blocks prevent information leakage

### Examples
```python
# Bad (reveals email exists)
return "Invalid password for user@example.com"

# Good (generic message)
return "Invalid credentials"
```

### Location
- All endpoints in `auth_server.py`
- `SecurityLogger` class in `src/security/security_utils.py`

---

## 8. Access Control

### User Data Isolation
- **Client Endpoints**: Users can ONLY access their own events
- **Database Filtering**: `filter_by(client_id=user_id)` ensures isolation
- **Token Verification**: User ID extracted from JWT, not from request body

### Authorization Checks
- Admin-only operations protected with `@require_role(2)`
- Planner operations protected with `@require_role(1)`
- Client operations protected with `@require_auth`

### Location
- Enforced in all API endpoints via decorators and database queries

---

## 9. Secure Database Practices

### Implementation
- **ORM Usage**: SQLAlchemy ORM prevents SQL injection
- **Parameterized Queries**: All queries use ORM methods, not raw SQL
- **Unique Constraints**: Email field has unique constraint
- **ID Validation**: All IDs validated before database queries

### Password Storage Schema
```python
class CMSUser(Base):
    user_pswd = Column(String, nullable=False)  # Stores bcrypt hash
```

### Location
- `src/db/database.py`: Database configuration
- `src/objs/user/obj_user.py`: User model

---

## 10. Security Logging & Monitoring

### Implementation
- **Failed Login Tracking**: Logs email and IP address
- **Successful Login Tracking**: Audit trail for access
- **Suspicious Activity Logging**: Duplicate registrations, errors
- **Timestamp Recording**: All logs include ISO 8601 timestamps

### Log Format
```
[SECURITY] 2026-01-17T10:30:45 - Failed login attempt for user@example.com from 192.168.1.1
```

### Location
- `src/security/security_utils.py`: `SecurityLogger` class
- Called throughout `auth_server.py` endpoints

---

## 11. Additional Security Measures

### ID Validation
- Validates all IDs are positive integers
- Prevents type confusion attacks
- Returns validated integer for database queries

### Price Validation
- Ensures prices are valid floats
- Prevents negative prices
- Handles ValueError exceptions

### Date Validation
- ISO format required (YYYY-MM-DD HH:mm)
- Invalid formats rejected with helpful error
- Prevents injection via date strings

---

## Security Checklist for Production

Before deploying to production:

- [ ] Change `SECRET_KEY` in security_utils.py (use environment variable)
- [ ] Configure `ALLOWED_ORIGINS` for production domain
- [ ] Use Redis for rate limiting instead of memory
- [ ] Enable HTTPS/TLS (Strict-Transport-Security header requires it)
- [ ] Set up proper logging to file/service (not just console)
- [ ] Disable Flask debug mode (`debug=False` in app.run)
- [ ] Review and adjust rate limits based on traffic
- [ ] Implement session invalidation/logout functionality
- [ ] Add password reset with email verification
- [ ] Consider adding 2FA for admin accounts
- [ ] Regular security audits and dependency updates
- [ ] Database backups with encryption
- [ ] Implement CAPTCHA for registration/login

---

## Testing Security

### Manual Tests
1. **Password Hashing**: Check database - passwords should be bcrypt hashes
2. **Rate Limiting**: Make rapid requests - should get 429 Too Many Requests
3. **Invalid Tokens**: Use expired/invalid JWT - should get 401 Unauthorized
4. **XSS Attempts**: Submit `<script>alert('xss')</script>` - should be escaped
5. **Authorization**: Try accessing admin endpoint as client - should get 403 Forbidden

### Automated Tests
Consider implementing:
- Unit tests for validation functions
- Integration tests for authentication flow
- Penetration testing with OWASP ZAP
- Dependency vulnerability scanning

---

## Dependencies

Security-related packages:
- `bcrypt==4.1.2`: Password hashing
- `PyJWT==2.8.0`: JWT token management
- `Flask-Limiter==3.5.0`: Rate limiting
- `Flask-CORS==4.0.0`: CORS management

---

## References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- JWT Best Practices: https://tools.ietf.org/html/rfc8725
- bcrypt: https://en.wikipedia.org/wiki/Bcrypt

---

## Contact

For security concerns or vulnerabilities, please report immediately to the development team.

**Last Updated**: January 17, 2026
