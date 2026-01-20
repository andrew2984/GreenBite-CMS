import re
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import html

SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 24


class PasswordHasher:

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False


class InputValidator:

    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        if not email or not isinstance(email, str):
            return False, "Email is required"

        if len(email) > 255:
            return False, "Email is too long (max 255 characters)"

        if not InputValidator.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"

        return True, ""

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:

        if not username or not isinstance(username, str):
            return False, "Username is required"

        if len(username) < 3:
            return False, "Username must be at least 3 characters"

        if len(username) > 50:
            return False, "Username is too long (max 50 characters)"

        if not InputValidator.USERNAME_PATTERN.match(username):
            return False, "Username can only contain letters, numbers, hyphens and underscores"

        return True, ""

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:

        if not password or not isinstance(password, str):
            return False, "Password is required"

        if len(password) < 8:
            return False, "Password must be at least 8 characters"

        if len(password) > 128:
            return False, "Password is too long (max 128 characters)"

        # Check for complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and number"

        return True, ""

    @staticmethod
    def validate_role(role: str) -> tuple[bool, str]:
        valid_roles = ['client', 'planner', 'admin']
        if role not in valid_roles:
            return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        return True, ""

    @staticmethod
    def validate_id(id_value: any) -> tuple[bool, str, int]:

        try:
            converted_id = int(id_value)
            if converted_id <= 0:
                return False, "ID must be a positive integer", 0
            return True, "", converted_id
        except (ValueError, TypeError):
            return False, "Invalid ID format", 0

    @staticmethod
    def sanitize_string(text: str, max_length: int = 500) -> str:
        if not text:
            return ""

        # Escape HTML entities
        text = html.escape(str(text))

        # Truncate to max length
        text = text[:max_length]

        return text.strip()


class JWTManager:

    @staticmethod
    def generate_token(user_id: int, email: str, role: str, permission_lvl: int) -> str:

        payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'permission_lvl': permission_lvl,
            'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token

    @staticmethod
    def verify_token(token: str) -> tuple[bool, dict]:

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, {'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return False, {'error': 'Invalid token'}


def require_auth(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'success': False, 'message': 'Authorization header missing'}), 401

        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'success': False, 'message': 'Invalid authorization header format'}), 401

        token = parts[1]

        # Verify token
        is_valid, payload = JWTManager.verify_token(token)
        if not is_valid:
            return jsonify({'success': False, 'message': payload.get('error', 'Invalid token')}), 401

        # Add user info to request context
        request.user_id = payload.get('user_id')
        request.user_email = payload.get('email')
        request.user_role = payload.get('role')
        request.permission_lvl = payload.get('permission_lvl')

        return f(*args, **kwargs)

    return decorated_function


def require_role(required_permission_lvl: int):

    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            if request.permission_lvl < required_permission_lvl:
                return jsonify({
                    'success': False,
                    'message': 'Insufficient permissions'
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


class SecurityLogger:
    """Log security-related events"""

    @staticmethod
    def log_failed_login(email: str, ip_address: str):
        """Log failed login attempt"""
        timestamp = datetime.utcnow().isoformat()
        print(f"[SECURITY] {timestamp} - Failed login attempt for {email} from {ip_address}")

    @staticmethod
    def log_successful_login(email: str, ip_address: str):
        """Log successful login"""
        timestamp = datetime.utcnow().isoformat()
        print(f"[SECURITY] {timestamp} - Successful login for {email} from {ip_address}")

    @staticmethod
    def log_suspicious_activity(activity: str, details: str):
        """Log suspicious activity"""
        timestamp = datetime.utcnow().isoformat()
        print(f"[SECURITY] {timestamp} - SUSPICIOUS: {activity} - {details}")
