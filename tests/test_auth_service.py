import pytest
from unittest.mock import MagicMock, patch

from src.services.auth_service import AuthService
from src.objs.user.obj_user import CMSUser

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None
    return db

@patch("src.services.auth_service.JWTManager.generate_token")
@patch("src.services.auth_service.InputValidator")
def test_register_user_success(mock_validator, mock_jwt, mock_db):
    mock_validator.validate_username.return_value = (True, "")
    mock_validator.validate_email.return_value = (True, "")
    mock_validator.validate_password.return_value = (True, "")
    mock_validator.validate_role.return_value = (True, "")
    mock_validator.sanitize_string.return_value = "testuser"

    mock_jwt.return_value = "fake.jwt.token"

    result, msg, data, status = AuthService.register_user(
        mock_db,
        username=" testuser ",
        email="TEST@EMAIL.COM",
        password="StrongPass123!",
        role="client"
    )

    assert result is True
    assert status == 201
    assert data["token"] == "fake.jwt.token"
    assert data["user"]["email"] == "test@email.com"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@patch("src.services.auth_service.SecurityLogger.log_suspicious_activity")
def test_register_user_duplicate_email(mock_logger, mock_db):
    mock_db.query.return_value.filter_by.return_value.first.return_value = CMSUser()

    result, msg, data, status = AuthService.register_user(
        mock_db,
        "user",
        "user@email.com",
        "Password123!",
        "client"
    )

    assert result is False
    assert status == 400
    assert msg == "Email already registered"
    mock_logger.assert_called_once()
    
@patch("src.services.auth_service.InputValidator.validate_email")
def test_register_user_invalid_email(mock_validate_email, mock_db):
    mock_validate_email.return_value = (False, "Invalid email")

    result, msg, data, status = AuthService.register_user(
        mock_db,
        "user",
        "bad-email",
        "Password123!",
        "client"
    )

    assert result is False
    assert status == 400
    assert msg == "Invalid email"
    
@patch("src.services.auth_service.JWTManager.generate_token")
@patch("src.services.auth_service.CMSUser.login")
def test_login_user_success(mock_login, mock_jwt, mock_db):
    user = MagicMock()
    user.id = 1
    user.user_name = "testuser"
    user.user_email = "test@email.com"
    user.permission_lvl = 0

    mock_login.return_value = user
    mock_jwt.return_value = "fake.jwt.token"

    result, msg, data, status = AuthService.login_user(
        mock_db,
        email="TEST@EMAIL.COM",
        password="Password123!",
        ip_address="127.0.0.1"
    )

    assert result is True
    assert status == 200
    assert data["user"]["role"] == "client"
    assert data["token"] == "fake.jwt.token"
    
@patch("src.services.auth_service.CMSUser.login")
@patch("src.services.auth_service.SecurityLogger.log_failed_login")
def test_login_user_invalid_credentials(mock_log, mock_login, mock_db):
    mock_login.return_value = None

    result, msg, data, status = AuthService.login_user(
        mock_db,
        email="user@email.com",
        password="wrongpass",
        ip_address="127.0.0.1"
    )

    assert result is False
    assert status == 401
    assert msg == "Invalid credentials"
    mock_log.assert_called_once()
    
def test_login_user_missing_fields(mock_db):
    result, msg, data, status = AuthService.login_user(
        mock_db,
        email="",
        password=""
    )

    assert result is False
    assert status == 400
    
def test_check_email_exists_true(mock_db):
    mock_db.query.return_value.filter_by.return_value.first.return_value = CMSUser()

    exists, status = AuthService.check_email_exists(
        mock_db,
        "user@email.com"
    )

    assert exists is True
    assert status == 200

def test_check_email_exists_missing_email(mock_db):
    exists, status = AuthService.check_email_exists(mock_db, "")

    assert exists is False
    assert status == 400