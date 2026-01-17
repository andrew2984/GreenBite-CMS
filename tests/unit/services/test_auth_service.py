"""
Unit tests for AuthService
"""
import pytest
from datetime import datetime
from src.services.auth_service import AuthService
from src.objs.user.obj_user import CMSUser
from src.objs.user.obj_client import CMSClientUser
from src.objs.user.obj_planner import CMSEventPLanner
from src.objs.user.obj_admin import CMSAdminUser


class TestAuthServiceRegistration:
    """Test suite for AuthService registration."""
    
    def test_register_client_success(self, db_session):
        """Test successful client registration."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="testclient",
            email="test@client.com",
            password="TestPassword123",
            role="client"
        )
        
        assert success is True
        assert status_code == 201
        assert user_data['success'] is True
        assert 'token' in user_data
        assert user_data['user']['email'] == "test@client.com"
        assert user_data['user']['role'] == "client"
    
    def test_register_planner_success(self, db_session):
        """Test successful planner registration."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="testplanner",
            email="test@planner.com",
            password="TestPassword123",
            role="planner"
        )
        
        assert success is True
        assert status_code == 201
        assert user_data['user']['role'] == "planner"
    
    def test_register_admin_success(self, db_session):
        """Test successful admin registration."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="testadmin",
            email="test@admin.com",
            password="TestPassword123",
            role="admin"
        )
        
        assert success is True
        assert status_code == 201
        assert user_data['user']['role'] == "admin"
    
    def test_register_duplicate_email(self, db_session, sample_client):
        """Test registration with duplicate email."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="newuser",
            email=sample_client.user_email,
            password="TestPassword123",
            role="client"
        )
        
        assert success is False
        assert status_code == 400
        assert "already registered" in message
    
    def test_register_invalid_email(self, db_session):
        """Test registration with invalid email."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="testuser",
            email="invalid-email",
            password="TestPassword123",
            role="client"
        )
        
        assert success is False
        assert status_code == 400
        assert "email" in message.lower()
    
    def test_register_invalid_username(self, db_session):
        """Test registration with invalid username."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="ab",  # Too short
            email="test@test.com",
            password="TestPassword123",
            role="client"
        )
        
        assert success is False
        assert status_code == 400
        assert "username" in message.lower()
    
    def test_register_weak_password(self, db_session):
        """Test registration with weak password."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="testuser",
            email="test@test.com",
            password="weak",
            role="client"
        )
        
        assert success is False
        assert status_code == 400
        assert "password" in message.lower()
    
    def test_register_invalid_role(self, db_session):
        """Test registration with invalid role."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="testuser",
            email="test@test.com",
            password="TestPassword123",
            role="superuser"
        )
        
        assert success is False
        assert status_code == 400
        assert "role" in message.lower()
    
    def test_register_strips_whitespace(self, db_session):
        """Test that registration strips whitespace from inputs."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="  testuser  ",
            email="  TEST@test.com  ",
            password="TestPassword123",
            role="  client  "
        )
        
        assert success is True
        assert user_data['user']['email'] == "test@test.com"  # Lowercase and trimmed


class TestAuthServiceLogin:
    """Test suite for AuthService login."""
    
    def test_login_success(self, db_session, sample_client):
        """Test successful login."""
        success, message, user_data, status_code = AuthService.login_user(
            db_session,
            email=sample_client.user_email,
            password="TestPassword123",
            ip_address="127.0.0.1"
        )
        
        assert success is True
        assert status_code == 200
        assert 'token' in user_data
        assert user_data['user']['email'] == sample_client.user_email
    
    def test_login_wrong_password(self, db_session, sample_client):
        """Test login with wrong password."""
        success, message, user_data, status_code = AuthService.login_user(
            db_session,
            email=sample_client.user_email,
            password="WrongPassword123",
            ip_address="127.0.0.1"
        )
        
        assert success is False
        assert status_code == 401
        assert "Invalid credentials" in message
    
    def test_login_nonexistent_user(self, db_session):
        """Test login with nonexistent user."""
        success, message, user_data, status_code = AuthService.login_user(
            db_session,
            email="nonexistent@test.com",
            password="TestPassword123",
            ip_address="127.0.0.1"
        )
        
        assert success is False
        assert status_code == 401
    
    def test_login_empty_email(self, db_session):
        """Test login with empty email."""
        success, message, user_data, status_code = AuthService.login_user(
            db_session,
            email="",
            password="TestPassword123",
            ip_address="127.0.0.1"
        )
        
        assert success is False
        assert status_code == 400
        assert "Missing" in message
    
    def test_login_empty_password(self, db_session, sample_client):
        """Test login with empty password."""
        success, message, user_data, status_code = AuthService.login_user(
            db_session,
            email=sample_client.user_email,
            password="",
            ip_address="127.0.0.1"
        )
        
        assert success is False
        assert status_code == 400
    
    def test_login_case_insensitive_email(self, db_session, sample_client):
        """Test login with different case email."""
        success, message, user_data, status_code = AuthService.login_user(
            db_session,
            email=sample_client.user_email.upper(),
            password="TestPassword123",
            ip_address="127.0.0.1"
        )
        
        assert success is True
        assert status_code == 200
    
    def test_login_returns_correct_role(self, db_session, sample_planner):
        """Test that login returns correct role information."""
        success, message, user_data, status_code = AuthService.login_user(
            db_session,
            email=sample_planner.user_email,
            password="TestPassword123",
            ip_address="127.0.0.1"
        )
        
        assert success is True
        assert user_data['user']['role'] == "Planner"


class TestAuthServiceEmailCheck:
    """Test suite for AuthService email check."""
    
    def test_check_email_exists(self, db_session, sample_client):
        """Test checking if email exists."""
        exists, status_code = AuthService.check_email_exists(
            db_session,
            sample_client.user_email
        )
        
        assert exists is True
        assert status_code == 200
    
    def test_check_email_not_exists(self, db_session):
        """Test checking if email doesn't exist."""
        exists, status_code = AuthService.check_email_exists(
            db_session,
            "nonexistent@test.com"
        )
        
        assert exists is False
        assert status_code == 200
    
    def test_check_email_none(self, db_session):
        """Test checking None email."""
        with pytest.raises(Exception):
            AuthService.check_email_exists(db_session, None)


class TestAuthServicePermissionLevels:
    """Test suite for permission levels."""
    
    def test_client_permission_level(self, db_session):
        """Test client gets correct permission level."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="testclient",
            email="client@test.com",
            password="TestPassword123",
            role="client"
        )
        
        # Verify in database
        user = db_session.query(CMSClientUser).filter_by(email="client@test.com").first()
        assert user.permission_lvl == 0
    
    def test_planner_permission_level(self, db_session):
        """Test planner gets correct permission level."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="testplanner",
            email="planner@test.com",
            password="TestPassword123",
            role="planner"
        )
        
        user = db_session.query(CMSEventPLanner).filter_by(email="planner@test.com").first()
        assert user.permission_lvl == 1
    
    def test_admin_permission_level(self, db_session):
        """Test admin gets correct permission level."""
        success, message, user_data, status_code = AuthService.register_user(
            db_session,
            username="testadmin",
            email="admin@test.com",
            password="TestPassword123",
            role="admin"
        )
        
        user = db_session.query(CMSAdminUser).filter_by(email="admin@test.com").first()
        assert user.permission_lvl == 2
