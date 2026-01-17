"""
Pytest configuration and shared fixtures for all tests.
This file is automatically loaded by pytest before running tests.
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db.database import Base
from src.objs.user.obj_user import CMSUser
from src.objs.user.obj_admin import CMSAdminUser
from src.objs.user.obj_client import CMSClientUser
from src.objs.user.obj_planner import CMSEventPLanner
from src.objs.obj_event import Event
from src.security.security_utils import PasswordHasher, JWTManager


@pytest.fixture(scope='function')
def test_db_engine():
    """Create a test database engine using in-memory SQLite."""
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope='function')
def db_session(test_db_engine):
    """Create a new database session for a test."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_client(db_session):
    """Create a sample client user for testing."""
    client = CMSClientUser(
        user_name="test_client",
        user_email="client@test.com",
        user_pswd="",
        permission_lvl=0
    )
    client.set_password("TestPassword123")
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client


@pytest.fixture
def sample_planner(db_session):
    """Create a sample planner user for testing."""
    planner = CMSEventPLanner(
        user_name="test_planner",
        user_email="planner@test.com",
        user_pswd="",
        permission_lvl=1
    )
    planner.set_password("TestPassword123")
    db_session.add(planner)
    db_session.commit()
    db_session.refresh(planner)
    return planner


@pytest.fixture
def sample_admin(db_session):
    """Create a sample admin user for testing."""
    admin = CMSAdminUser(
        user_name="test_admin",
        user_email="admin@test.com",
        user_pswd="",
        permission_lvl=2
    )
    admin.set_password("TestPassword123")
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def sample_event(db_session, sample_client):
    """Create a sample event for testing."""
    event = Event(
        client_name=sample_client.user_name,
        client_email=sample_client.user_email,
        client_id=sample_client.id,
        event_date=datetime.utcnow() + timedelta(days=30),
        title="Test Event",
        location="Test Location",
        notes="Test notes",
        price_total=100.0
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def valid_token():
    """Generate a valid JWT token for testing."""
    return JWTManager.generate_token(
        user_id=1,
        email="test@test.com",
        role="client",
        permission_lvl=0
    )


@pytest.fixture
def admin_token():
    """Generate a valid admin JWT token for testing."""
    return JWTManager.generate_token(
        user_id=1,
        email="admin@test.com",
        role="admin",
        permission_lvl=2
    )


@pytest.fixture
def planner_token():
    """Generate a valid planner JWT token for testing."""
    return JWTManager.generate_token(
        user_id=1,
        email="planner@test.com",
        role="planner",
        permission_lvl=1
    )


@pytest.fixture
def expired_token():
    """Generate an expired JWT token for testing."""
    import jwt
    from src.security.security_utils import SECRET_KEY, ALGORITHM
    
    payload = {
        'user_id': 1,
        'email': 'test@test.com',
        'role': 'client',
        'permission_lvl': 0,
        'exp': datetime.utcnow() - timedelta(hours=1),
        'iat': datetime.utcnow() - timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def flask_app():
    """Create a Flask app instance for testing."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    from auth_server import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def flask_client(flask_app):
    """Create a Flask test client."""
    return flask_app.test_client()


@pytest.fixture
def mock_request():
    """Create a mock Flask request object."""
    class MockRequest:
        def __init__(self):
            self.user_id = 1
            self.user_email = "test@test.com"
            self.user_role = "client"
            self.permission_lvl = 0
            self.headers = {}
            self.remote_addr = "127.0.0.1"
    
    return MockRequest()


# Pytest hooks for custom reporting
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interactions"
    )
    config.addinivalue_line(
        "markers", "system: System tests for end-to-end scenarios"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "system" in str(item.fspath):
            item.add_marker(pytest.mark.system)
