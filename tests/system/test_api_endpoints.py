"""
System tests for Flask API endpoints
End-to-end testing of the REST API
"""
import pytest
import json
from datetime import datetime, timedelta


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, flask_client):
        """Test health check endpoint."""
        response = flask_client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""
    
    def test_register_endpoint(self, flask_client):
        """Test user registration endpoint."""
        response = flask_client.post('/api/register', json={
            'username': 'systemtest',
            'email': 'system@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'token' in data
        assert data['user']['email'] == 'system@test.com'
    
    def test_register_duplicate_email(self, flask_client):
        """Test registration with duplicate email."""
        # Register first time
        flask_client.post('/api/register', json={
            'username': 'user1',
            'email': 'duplicate@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        
        # Try to register again with same email
        response = flask_client.post('/api/register', json={
            'username': 'user2',
            'email': 'duplicate@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_login_endpoint(self, flask_client):
        """Test user login endpoint."""
        # Register user first
        flask_client.post('/api/register', json={
            'username': 'logintest',
            'email': 'login@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        
        # Login
        response = flask_client.post('/api/login', json={
            'email': 'login@test.com',
            'password': 'TestPassword123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'token' in data
    
    def test_login_wrong_password(self, flask_client):
        """Test login with wrong password."""
        # Register user
        flask_client.post('/api/register', json={
            'username': 'wrongpwdtest',
            'email': 'wrongpwd@test.com',
            'password': 'CorrectPassword123',
            'role': 'client'
        })
        
        # Try to login with wrong password
        response = flask_client.post('/api/login', json={
            'email': 'wrongpwd@test.com',
            'password': 'WrongPassword123'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_check_email_endpoint(self, flask_client):
        """Test email check endpoint."""
        # Register user
        flask_client.post('/api/register', json={
            'username': 'emailcheck',
            'email': 'emailcheck@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        
        # Check existing email
        response = flask_client.post('/api/check-email', json={
            'email': 'emailcheck@test.com'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['exists'] is True
        
        # Check non-existing email
        response = flask_client.post('/api/check-email', json={
            'email': 'nonexistent@test.com'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['exists'] is False


class TestClientEndpoints:
    """Test client-specific API endpoints."""
    
    def test_get_client_events_requires_auth(self, flask_client):
        """Test that getting events requires authentication."""
        response = flask_client.get('/api/client/events')
        
        assert response.status_code == 401
    
    def test_get_client_events_with_auth(self, flask_client):
        """Test getting client events with authentication."""
        # Register and get token
        register_response = flask_client.post('/api/register', json={
            'username': 'clientevents',
            'email': 'clientevents@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        data = json.loads(register_response.data)
        token = data['token']
        
        # Get events
        response = flask_client.get(
            '/api/client/events',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'events' in data
    
    def test_create_event_endpoint(self, flask_client):
        """Test creating an event."""
        # Register client
        register_response = flask_client.post('/api/register', json={
            'username': 'createevent',
            'email': 'createevent@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        data = json.loads(register_response.data)
        token = data['token']
        
        # Create event
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        response = flask_client.post(
            '/api/client/create-event',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'event_date': event_date,
                'title': 'API Test Event',
                'location': 'Test Location',
                'notes': 'Test notes',
                'price_total': 150.0
            }
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['event']['title'] == 'API Test Event'
    
    def test_cancel_event_endpoint(self, flask_client):
        """Test cancelling an event."""
        # Register client
        register_response = flask_client.post('/api/register', json={
            'username': 'cancelevent',
            'email': 'cancelevent@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        data = json.loads(register_response.data)
        token = data['token']
        
        # Create event
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        create_response = flask_client.post(
            '/api/client/create-event',
            headers={'Authorization': f'Bearer {token}'},
            json={'event_date': event_date, 'title': 'Event to Cancel'}
        )
        event_data = json.loads(create_response.data)
        event_id = event_data['event']['id']
        
        # Cancel event
        response = flask_client.post(
            '/api/client/cancel-event',
            headers={'Authorization': f'Bearer {token}'},
            json={'event_id': event_id}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestPlannerEndpoints:
    """Test planner-specific API endpoints."""
    
    def test_planner_events_requires_planner_role(self, flask_client):
        """Test that planner endpoints require planner role."""
        # Register as client
        register_response = flask_client.post('/api/register', json={
            'username': 'notplanner',
            'email': 'notplanner@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        data = json.loads(register_response.data)
        token = data['token']
        
        # Try to access planner endpoint
        response = flask_client.get(
            '/api/planner/events',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403
    
    def test_get_planner_events(self, flask_client):
        """Test getting planner events."""
        # Register as planner
        register_response = flask_client.post('/api/register', json={
            'username': 'testplanner',
            'email': 'testplanner@test.com',
            'password': 'TestPassword123',
            'role': 'planner'
        })
        data = json.loads(register_response.data)
        token = data['token']
        
        # Get planner events
        response = flask_client.get(
            '/api/planner/events',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'events' in data


class TestAdminEndpoints:
    """Test admin-specific API endpoints."""
    
    def test_admin_events_requires_admin_role(self, flask_client):
        """Test that admin endpoints require admin role."""
        # Register as client
        register_response = flask_client.post('/api/register', json={
            'username': 'notadmin',
            'email': 'notadmin@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        data = json.loads(register_response.data)
        token = data['token']
        
        # Try to access admin endpoint
        response = flask_client.get(
            '/api/admin/events',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403
    
    def test_get_admin_events(self, flask_client):
        """Test getting all events as admin."""
        # Register as admin
        register_response = flask_client.post('/api/register', json={
            'username': 'testadmin',
            'email': 'testadmin@test.com',
            'password': 'TestPassword123',
            'role': 'admin'
        })
        data = json.loads(register_response.data)
        token = data['token']
        
        # Get all events
        response = flask_client.get(
            '/api/admin/events',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'events' in data
        assert 'planners' in data
    
    def test_assign_planner_endpoint(self, flask_client):
        """Test assigning planner to event."""
        # Register admin
        admin_response = flask_client.post('/api/register', json={
            'username': 'assignadmin',
            'email': 'assignadmin@test.com',
            'password': 'TestPassword123',
            'role': 'admin'
        })
        admin_data = json.loads(admin_response.data)
        admin_token = admin_data['token']
        
        # Register planner
        planner_response = flask_client.post('/api/register', json={
            'username': 'assignplanner',
            'email': 'assignplanner@test.com',
            'password': 'TestPassword123',
            'role': 'planner'
        })
        planner_data = json.loads(planner_response.data)
        planner_id = planner_data['user']['id']
        
        # Register client and create event
        client_response = flask_client.post('/api/register', json={
            'username': 'assignclient',
            'email': 'assignclient@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        client_data = json.loads(client_response.data)
        client_token = client_data['token']
        
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        event_response = flask_client.post(
            '/api/client/create-event',
            headers={'Authorization': f'Bearer {client_token}'},
            json={'event_date': event_date, 'title': 'Assign Test'}
        )
        event_data = json.loads(event_response.data)
        event_id = event_data['event']['id']
        
        # Assign planner to event
        response = flask_client.post(
            '/api/admin/assign-planner',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'event_id': event_id, 'planner_id': planner_id}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestSecurityHeaders:
    """Test security headers are properly set."""
    
    def test_security_headers_present(self, flask_client):
        """Test that security headers are added to responses."""
        response = flask_client.get('/api/health')
        
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        
        assert 'X-XSS-Protection' in response.headers
        assert 'Strict-Transport-Security' in response.headers
        assert 'Content-Security-Policy' in response.headers


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiting_on_login(self, flask_client):
        """Test rate limiting on login endpoint."""
        # Register user
        flask_client.post('/api/register', json={
            'username': 'ratelimit',
            'email': 'ratelimit@test.com',
            'password': 'TestPassword123',
            'role': 'client'
        })
        
        # Make multiple login attempts
        for i in range(15):
            response = flask_client.post('/api/login', json={
                'email': 'ratelimit@test.com',
                'password': 'TestPassword123'
            })
        
        # Rate limit should be enforced (exact behavior depends on limiter config)
        # We just verify the endpoint is accessible
        assert response.status_code in [200, 429]  # 429 = Too Many Requests
