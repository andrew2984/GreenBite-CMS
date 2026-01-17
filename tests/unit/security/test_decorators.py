"""
Unit tests for security decorators - require_auth and require_role
"""
import pytest
from unittest.mock import Mock, patch
from flask import Flask, jsonify
from src.security.security_utils import require_auth, require_role, JWTManager


class TestSecurityDecorators:
    """Test suite for authentication and authorization decorators."""
    
    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def valid_token(self):
        """Generate a valid token for testing."""
        return JWTManager.generate_token(
            user_id=1,
            email="test@test.com",
            role="client",
            permission_lvl=0
        )
    
    def test_require_auth_with_valid_token(self, app, valid_token):
        """Test require_auth decorator with valid token."""
        @app.route('/test')
        @require_auth
        def test_endpoint():
            from flask import request
            return jsonify({
                'user_id': request.user_id,
                'email': request.user_email
            })
        
        with app.test_client() as client:
            response = client.get(
                '/test',
                headers={'Authorization': f'Bearer {valid_token}'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['user_id'] == 1
            assert data['email'] == 'test@test.com'
    
    def test_require_auth_missing_header(self, app):
        """Test require_auth decorator without authorization header."""
        @app.route('/test')
        @require_auth
        def test_endpoint():
            return jsonify({'message': 'success'})
        
        with app.test_client() as client:
            response = client.get('/test')
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'Authorization header missing' in data['message']
    
    def test_require_auth_invalid_format(self, app):
        """Test require_auth decorator with invalid header format."""
        @app.route('/test')
        @require_auth
        def test_endpoint():
            return jsonify({'message': 'success'})
        
        with app.test_client() as client:
            response = client.get(
                '/test',
                headers={'Authorization': 'InvalidFormat'}
            )
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'Invalid authorization header format' in data['message']
    
    def test_require_auth_invalid_token(self, app):
        """Test require_auth decorator with invalid token."""
        @app.route('/test')
        @require_auth
        def test_endpoint():
            return jsonify({'message': 'success'})
        
        with app.test_client() as client:
            response = client.get(
                '/test',
                headers={'Authorization': 'Bearer invalid.token.here'}
            )
            
            assert response.status_code == 401
    
    def test_require_role_sufficient_permission(self, app):
        """Test require_role decorator with sufficient permissions."""
        admin_token = JWTManager.generate_token(
            user_id=1,
            email="admin@test.com",
            role="admin",
            permission_lvl=2
        )
        
        @app.route('/admin')
        @require_role(2)
        def admin_endpoint():
            return jsonify({'message': 'admin access granted'})
        
        with app.test_client() as client:
            response = client.get(
                '/admin',
                headers={'Authorization': f'Bearer {admin_token}'}
            )
            
            assert response.status_code == 200
    
    def test_require_role_insufficient_permission(self, app, valid_token):
        """Test require_role decorator with insufficient permissions."""
        @app.route('/admin')
        @require_role(2)
        def admin_endpoint():
            return jsonify({'message': 'admin access granted'})
        
        with app.test_client() as client:
            response = client.get(
                '/admin',
                headers={'Authorization': f'Bearer {valid_token}'}
            )
            
            assert response.status_code == 403
            data = response.get_json()
            assert 'Insufficient permissions' in data['message']
    
    def test_require_role_planner_access(self, app):
        """Test require_role decorator for planner role."""
        planner_token = JWTManager.generate_token(
            user_id=1,
            email="planner@test.com",
            role="planner",
            permission_lvl=1
        )
        
        @app.route('/planner')
        @require_role(1)
        def planner_endpoint():
            return jsonify({'message': 'planner access granted'})
        
        with app.test_client() as client:
            response = client.get(
                '/planner',
                headers={'Authorization': f'Bearer {planner_token}'}
            )
            
            assert response.status_code == 200
