# GreenBite CMS - Event Management System

## Security-by-Design Implementation

This application demonstrates comprehensive security-by-design principles for an Advanced Software Engineering assignment.

---

## 🔒 Security Features Implemented

### 1. **Password Security**
- ✅ Bcrypt password hashing (cost factor: 12)
- ✅ NO plaintext password storage
- ✅ Secure password verification with constant-time comparison
- ✅ Strong password requirements (min 8 chars, uppercase, lowercase, numbers)

### 2. **Authentication & Authorization**
- ✅ JWT token-based stateless authentication
- ✅ 24-hour token expiration
- ✅ Role-Based Access Control (RBAC) - 3 levels (Client, Planner, Admin)
- ✅ Authorization decorators (`@require_auth`, `@require_role`)

### 3. **Input Validation & Sanitization**
- ✅ Email format validation (regex)
- ✅ Username validation (3-50 chars, alphanumeric)
- ✅ Password strength validation
- ✅ XSS prevention via HTML entity escaping
- ✅ ID validation (positive integers only)
- ✅ Price & date validation

### 4. **Rate Limiting**
- ✅ Global rate limits (200/day, 50/hour per IP)
- ✅ Login endpoint: 10 attempts/minute (brute force prevention)
- ✅ Registration endpoint: 5 attempts/minute (spam prevention)

### 5. **CORS Security**
- ✅ Restricted to specific origins only
- ✅ Configurable via environment variables
- ✅ Controlled methods and headers

### 6. **Security Headers**
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: DENY (clickjacking prevention)
- ✅ X-XSS-Protection: enabled
- ✅ Strict-Transport-Security: HTTPS enforcement
- ✅ Content-Security-Policy: resource restriction

### 7. **Secure Error Handling**
- ✅ Generic error messages (no information leakage)
- ✅ No email enumeration on login
- ✅ Exception logging without user exposure

### 8. **Access Control**
- ✅ Users can ONLY access their own data
- ✅ Token-based user identification (not request parameters)
- ✅ Database-level filtering by user ID
- ✅ Permission level enforcement

### 9. **Database Security**
- ✅ SQLAlchemy ORM (SQL injection prevention)
- ✅ Parameterized queries only
- ✅ Unique constraints on sensitive fields (email)

### 10. **Audit Logging**
- ✅ Failed login attempt tracking
- ✅ Successful login logging
- ✅ Suspicious activity alerts
- ✅ Timestamped security events

---

## 📁 Key Security Files

- **[src/security/security_utils.py](src/security/security_utils.py)** - All security utilities
- **[SECURITY.md](SECURITY.md)** - Comprehensive security documentation
- **[test_security.py](test_security.py)** - Security demonstrations
- **[migrate_passwords.py](migrate_passwords.py)** - Password migration tool

---

## 🚀 Quick Start

### Install Dependencies
```bash
pip install -r Requirements.txt
```

### Run Security Tests
```bash
python test_security.py
```

### Start Server
```bash
python auth_server.py
```

---

## 🎓 Assignment Requirements Met

✅ **Data Validation**: Comprehensive input validation for all endpoints  
✅ **Access Control**: Role-based authorization with JWT tokens  
✅ **No Plaintext Storage**: All passwords hashed with bcrypt  
✅ **Secure Authentication**: Token-based authentication with expiration  
✅ **Input Sanitization**: XSS prevention via HTML escaping  
✅ **Rate Limiting**: Brute force attack prevention  
✅ **Security Headers**: Browser security controls  
✅ **Audit Logging**: Security event tracking  

See **[SECURITY.md](SECURITY.md)** for complete documentation.

