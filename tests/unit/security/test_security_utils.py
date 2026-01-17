"""
Unit tests for security_utils.py - PasswordHasher, InputValidator, JWTManager
"""
import pytest
from datetime import datetime, timedelta
import jwt
from src.security.security_utils import (
    PasswordHasher,
    InputValidator,
    JWTManager,
    SecurityLogger,
    SECRET_KEY,
    ALGORITHM
)


class TestPasswordHasher:
    """Test suite for PasswordHasher class."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = PasswordHasher.hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password
    
    def test_hash_password_different_results(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "TestPassword123"
        hash1 = PasswordHasher.hash_password(password)
        hash2 = PasswordHasher.hash_password(password)
        
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = PasswordHasher.hash_password(password)
        
        assert PasswordHasher.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = PasswordHasher.hash_password(password)
        
        assert PasswordHasher.verify_password(wrong_password, hashed) is False
    
    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "TestPassword123"
        invalid_hash = "not_a_valid_hash"
        
        assert PasswordHasher.verify_password(password, invalid_hash) is False
    
    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        hashed = PasswordHasher.hash_password("TestPassword123")
        
        assert PasswordHasher.verify_password("", hashed) is False


class TestInputValidator:
    """Test suite for InputValidator class."""
    
    # Email validation tests
    def test_validate_email_valid(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@example.co.uk",
            "user+tag@example.com",
            "123@example.com",
            "test_email@test-domain.com"
        ]
        
        for email in valid_emails:
            is_valid, error_msg = InputValidator.validate_email(email)
            assert is_valid is True, f"Failed for {email}"
            assert error_msg == ""
    
    def test_validate_email_invalid_format(self):
        """Test validation of invalid email formats."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@exam ple.com",
            "user..name@example.com"
        ]
        
        for email in invalid_emails:
            is_valid, error_msg = InputValidator.validate_email(email)
            assert is_valid is False, f"Should fail for {email}"
            assert "Invalid email format" in error_msg
    
    def test_validate_email_empty(self):
        """Test validation of empty email."""
        is_valid, error_msg = InputValidator.validate_email("")
        assert is_valid is False
        assert "Email is required" in error_msg
    
    def test_validate_email_none(self):
        """Test validation of None email."""
        is_valid, error_msg = InputValidator.validate_email(None)
        assert is_valid is False
        assert "Email is required" in error_msg
    
    def test_validate_email_too_long(self):
        """Test validation of email that's too long."""
        long_email = "a" * 250 + "@example.com"
        is_valid, error_msg = InputValidator.validate_email(long_email)
        assert is_valid is False
        assert "too long" in error_msg
    
    # Username validation tests
    def test_validate_username_valid(self):
        """Test validation of valid usernames."""
        valid_usernames = [
            "user123",
            "test_user",
            "user-name",
            "abc",
            "a" * 50
        ]
        
        for username in valid_usernames:
            is_valid, error_msg = InputValidator.validate_username(username)
            assert is_valid is True, f"Failed for {username}"
            assert error_msg == ""
    
    def test_validate_username_too_short(self):
        """Test validation of username that's too short."""
        is_valid, error_msg = InputValidator.validate_username("ab")
        assert is_valid is False
        assert "at least 3 characters" in error_msg
    
    def test_validate_username_too_long(self):
        """Test validation of username that's too long."""
        long_username = "a" * 51
        is_valid, error_msg = InputValidator.validate_username(long_username)
        assert is_valid is False
        assert "too long" in error_msg
    
    def test_validate_username_invalid_chars(self):
        """Test validation of username with invalid characters."""
        invalid_usernames = [
            "user name",
            "user@name",
            "user#123",
            "user$"
        ]
        
        for username in invalid_usernames:
            is_valid, error_msg = InputValidator.validate_username(username)
            assert is_valid is False, f"Should fail for {username}"
            assert "can only contain" in error_msg
    
    def test_validate_username_empty(self):
        """Test validation of empty username."""
        is_valid, error_msg = InputValidator.validate_username("")
        assert is_valid is False
        assert "Username is required" in error_msg
    
    # Password validation tests
    def test_validate_password_valid(self):
        """Test validation of valid passwords."""
        valid_passwords = [
            "Password123",
            "MyP@ssw0rd",
            "Test1234Pass",
            "Abc12345"
        ]
        
        for password in valid_passwords:
            is_valid, error_msg = InputValidator.validate_password(password)
            assert is_valid is True, f"Failed for {password}"
            assert error_msg == ""
    
    def test_validate_password_too_short(self):
        """Test validation of password that's too short."""
        is_valid, error_msg = InputValidator.validate_password("Pass12")
        assert is_valid is False
        assert "at least 8 characters" in error_msg
    
    def test_validate_password_too_long(self):
        """Test validation of password that's too long."""
        long_password = "P" + "a" * 128
        is_valid, error_msg = InputValidator.validate_password(long_password)
        assert is_valid is False
        assert "too long" in error_msg
    
    def test_validate_password_no_uppercase(self):
        """Test validation of password without uppercase."""
        is_valid, error_msg = InputValidator.validate_password("password123")
        assert is_valid is False
        assert "uppercase" in error_msg.lower()
    
    def test_validate_password_no_lowercase(self):
        """Test validation of password without lowercase."""
        is_valid, error_msg = InputValidator.validate_password("PASSWORD123")
        assert is_valid is False
        assert "lowercase" in error_msg.lower()
    
    def test_validate_password_no_digit(self):
        """Test validation of password without digit."""
        is_valid, error_msg = InputValidator.validate_password("PasswordABC")
        assert is_valid is False
        assert "number" in error_msg.lower()
    
    def test_validate_password_empty(self):
        """Test validation of empty password."""
        is_valid, error_msg = InputValidator.validate_password("")
        assert is_valid is False
        assert "Password is required" in error_msg
    
    # Role validation tests
    def test_validate_role_valid(self):
        """Test validation of valid roles."""
        valid_roles = ['client', 'planner', 'admin']
        
        for role in valid_roles:
            is_valid, error_msg = InputValidator.validate_role(role)
            assert is_valid is True
            assert error_msg == ""
    
    def test_validate_role_invalid(self):
        """Test validation of invalid roles."""
        invalid_roles = ['superadmin', 'user', 'guest', '']
        
        for role in invalid_roles:
            is_valid, error_msg = InputValidator.validate_role(role)
            assert is_valid is False
            assert "Invalid role" in error_msg
    
    # Sanitize string tests
    def test_sanitize_string_normal(self):
        """Test sanitization of normal string."""
        text = "Normal text"
        result = InputValidator.sanitize_string(text)
        assert result == "Normal text"
    
    def test_sanitize_string_html(self):
        """Test sanitization of string with HTML."""
        text = "<script>alert('xss')</script>"
        result = InputValidator.sanitize_string(text)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_sanitize_string_max_length(self):
        """Test sanitization respects max length."""
        text = "a" * 1000
        result = InputValidator.sanitize_string(text, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_string_empty(self):
        """Test sanitization of empty string."""
        result = InputValidator.sanitize_string("")
        assert result == ""
    
    def test_sanitize_string_none(self):
        """Test sanitization of None."""
        result = InputValidator.sanitize_string(None)
        assert result == ""
    
    # ID validation tests
    def test_validate_id_valid(self):
        """Test validation of valid IDs."""
        valid_ids = [1, 100, 999999, "42"]
        
        for id_value in valid_ids:
            is_valid, error_msg, converted = InputValidator.validate_id(id_value)
            assert is_valid is True
            assert error_msg == ""
            assert isinstance(converted, int)
            assert converted > 0
    
    def test_validate_id_invalid_negative(self):
        """Test validation of negative ID."""
        is_valid, error_msg, converted = InputValidator.validate_id(-1)
        assert is_valid is False
        assert "positive" in error_msg
    
    def test_validate_id_invalid_zero(self):
        """Test validation of zero ID."""
        is_valid, error_msg, converted = InputValidator.validate_id(0)
        assert is_valid is False
        assert "positive" in error_msg
    
    def test_validate_id_invalid_format(self):
        """Test validation of non-numeric ID."""
        is_valid, error_msg, converted = InputValidator.validate_id("abc")
        assert is_valid is False
        assert "Invalid ID format" in error_msg


class TestJWTManager:
    """Test suite for JWTManager class."""
    
    def test_generate_token(self):
        """Test JWT token generation."""
        token = JWTManager.generate_token(
            user_id=1,
            email="test@test.com",
            role="client",
            permission_lvl=0
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test verification of valid token."""
        token = JWTManager.generate_token(
            user_id=1,
            email="test@test.com",
            role="client",
            permission_lvl=0
        )
        
        is_valid, payload = JWTManager.verify_token(token)
        
        assert is_valid is True
        assert payload['user_id'] == 1
        assert payload['email'] == "test@test.com"
        assert payload['role'] == "client"
        assert payload['permission_lvl'] == 0
    
    def test_verify_token_expired(self):
        """Test verification of expired token."""
        # Create an expired token
        payload = {
            'user_id': 1,
            'email': 'test@test.com',
            'role': 'client',
            'permission_lvl': 0,
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        is_valid, error_payload = JWTManager.verify_token(token)
        
        assert is_valid is False
        assert 'error' in error_payload
        assert 'expired' in error_payload['error'].lower()
    
    def test_verify_token_invalid(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.string"
        
        is_valid, error_payload = JWTManager.verify_token(invalid_token)
        
        assert is_valid is False
        assert 'error' in error_payload
    
    def test_verify_token_wrong_secret(self):
        """Test verification of token with wrong secret."""
        # Create token with different secret
        payload = {
            'user_id': 1,
            'email': 'test@test.com',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, "wrong-secret", algorithm=ALGORITHM)
        
        is_valid, error_payload = JWTManager.verify_token(token)
        
        assert is_valid is False


class TestSecurityLogger:
    """Test suite for SecurityLogger class."""
    
    def test_log_failed_login(self, capsys):
        """Test logging of failed login attempt."""
        SecurityLogger.log_failed_login("test@test.com", "127.0.0.1")
        captured = capsys.readouterr()
        
        assert "Failed login attempt" in captured.out
        assert "test@test.com" in captured.out
        assert "127.0.0.1" in captured.out
    
    def test_log_successful_login(self, capsys):
        """Test logging of successful login."""
        SecurityLogger.log_successful_login("test@test.com", "127.0.0.1")
        captured = capsys.readouterr()
        
        assert "Successful login" in captured.out
        assert "test@test.com" in captured.out
    
    def test_log_suspicious_activity(self, capsys):
        """Test logging of suspicious activity."""
        SecurityLogger.log_suspicious_activity("Test activity", "Test details")
        captured = capsys.readouterr()
        
        assert "SUSPICIOUS" in captured.out
        assert "Test activity" in captured.out
        assert "Test details" in captured.out
