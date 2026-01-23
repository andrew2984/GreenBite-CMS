from typing import Tuple, Dict, Optional
from datetime import datetime
from src.objs.user.obj_user import CMSUser
from src.objs.user.obj_admin import CMSAdminUser
from src.objs.user.obj_client import CMSClientUser
from src.objs.user.obj_planner import CMSEventPLanner
from src.security.security_utils import (
    InputValidator,
    JWTManager,
    SecurityLogger
)

# service layer class to handle authentication-related business logic
class AuthService:
    
    PERMISSION_LEVELS = {
        'client': 0,
        'planner': 1,
        'admin': 2
    }
    
    ROLE_NAMES = {
        0: 'Client',
        1: 'Planner',
        2: 'Admin'
    }
    
    @staticmethod
    def register_user(
        db,
        username: str,
        email: str,
        password: str,
        role: str = 'client'
    ) -> Tuple[bool, str, Optional[Dict], int]:

        try:
            # Sanitize inputs
            username = username.strip()
            email = email.strip().lower()
            role = role.lower()
            
            # Validate all inputs
            is_valid, error_msg = InputValidator.validate_username(username)
            if not is_valid:
                return False, error_msg, None, 400
            
            is_valid, error_msg = InputValidator.validate_email(email)
            if not is_valid:
                return False, error_msg, None, 400
            
            is_valid, error_msg = InputValidator.validate_password(password)
            if not is_valid:
                return False, error_msg, None, 400
            
            is_valid, error_msg = InputValidator.validate_role(role)
            if not is_valid:
                return False, error_msg, None, 400
            
            # Check if email already exists
            existing_user = db.query(CMSUser).filter_by(user_email=email).first()
            if existing_user:
                SecurityLogger.log_suspicious_activity(
                    "Duplicate registration attempt",
                    f"Email: {email}"
                )
                return False, 'Email already registered', None, 400
            
            # Sanitize username
            username = InputValidator.sanitize_string(username, max_length=50)
            
            permission_lvl = AuthService.PERMISSION_LEVELS.get(role, 0)
            
            # Create user based on role
            if role == 'client':
                new_user = CMSClientUser(
                    user_name=username,
                    user_email=email,
                    user_pswd="",
                    permission_lvl=permission_lvl
                )
            elif role == 'planner':
                new_user = CMSEventPLanner(
                    user_name=username,
                    user_email=email,
                    user_pswd="",
                    permission_lvl=permission_lvl
                )
            elif role == 'admin':
                new_user = CMSAdminUser(
                    user_name=username,
                    user_email=email,
                    user_pswd="",
                    permission_lvl=permission_lvl
                )
            else:
                return False, 'Invalid role', None, 400
            
            # Hash password securely
            new_user.set_password(password)
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Generate JWT token
            token = JWTManager.generate_token(
                new_user.id,
                new_user.user_email,
                role,
                new_user.permission_lvl
            )
            
            user_data = {
                'success': True,
                'message': f'User registered successfully as {role}',
                'token': token,
                'user': {
                    'id': new_user.id,
                    'username': new_user.user_name,
                    'email': new_user.user_email,
                    'role': role
                }
            }
            
            return True, 'Registration successful', user_data, 201
            
        except Exception as e:
            db.rollback()
            SecurityLogger.log_suspicious_activity("Registration error", str(e))
            return False, 'Registration failed. Please try again.', None, 500
    
    @staticmethod
    def login_user(
        db,
        email: str,
        password: str,
        ip_address: str = None
    ) -> Tuple[bool, str, Optional[Dict], int]:

        try:
            email = email.strip().lower()
            
            # Validate inputs
            if not email or not password:
                return False, 'Missing email or password', None, 400
            
            is_valid, error_msg = InputValidator.validate_email(email)
            if not is_valid:
                return False, 'Invalid credentials', None, 401
            
            # Attempt login
            user = CMSUser.login(db, email, password)
            
            if not user:
                # Log failed attempt
                SecurityLogger.log_failed_login(email, ip_address or 'unknown')
                return False, 'Invalid credentials', None, 401
            
            # Log successful login
            SecurityLogger.log_successful_login(email, ip_address or 'unknown')
            
            # Determine role from permission level
            role = 'client'
            for role_name, perm_level in AuthService.PERMISSION_LEVELS.items():
                if perm_level == user.permission_lvl:
                    role = role_name
                    break
            
            # Generate JWT token
            token = JWTManager.generate_token(
                user.id,
                user.user_email,
                role,
                user.permission_lvl
            )
            
            user_data = {
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.user_name,
                    'email': user.user_email,
                    'role': role,
                    'roleDisplay': AuthService.ROLE_NAMES.get(user.permission_lvl, 'Unknown')
                }
            }
            
            return True, 'Login successful', user_data, 200
            
        except Exception as e:
            SecurityLogger.log_suspicious_activity("Login error", str(e))
            return False, f'Login failed. Please try again.\n{str(e)}', None, 500
    
    @staticmethod
    def check_email_exists(db, email: str) -> Tuple[bool, int]:

        try:
            if not email:
                return False, 400
            
            user = db.query(CMSUser).filter_by(user_email=email).first()
            return user is not None, 200
            
        except Exception:
            return False, 500
