from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.db.database import SessionLocal, engine, Base
from src.objs.user.obj_user import CMSUser
from src.objs.user.obj_admin import CMSAdminUser
from src.objs.user.obj_client import CMSClientUser
from src.objs.user.obj_planner import CMSEventPLanner
from src.objs.obj_event import Event
from src.security.security_utils import (
    InputValidator, 
    JWTManager, 
    require_auth, 
    require_role,
    SecurityLogger
)

Base.metadata.create_all(bind=engine)

app = Flask(__name__)

# Security Configuration
# CORS: More permissive for development, restrict in production
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')
CORS(app, 
     origins=ALLOWED_ORIGINS,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type", "Authorization"],
     supports_credentials=False)

# Rate Limiting: Prevent brute force attacks
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Security Headers Middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify server is running"""
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limit registration attempts
def register():
    """
    User registration endpoint with comprehensive input validation
    Security features:
    - Input validation for all fields
    - Password hashing (bcrypt)
    - Email uniqueness check
    - Sanitized inputs
    - Rate limiting
    """
    data = request.get_json()
    db = SessionLocal()
    
    try:
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'client').lower()
        
        # Validate all inputs
        is_valid, error_msg = InputValidator.validate_username(username)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        is_valid, error_msg = InputValidator.validate_email(email)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        is_valid, error_msg = InputValidator.validate_password(password)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        is_valid, error_msg = InputValidator.validate_role(role)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        # Check if email already exists
        existing_user = db.query(CMSUser).filter_by(user_email=email).first()
        if existing_user:
            SecurityLogger.log_suspicious_activity(
                "Duplicate registration attempt",
                f"Email: {email}"
            )
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Sanitize username
        username = InputValidator.sanitize_string(username, max_length=50)
        
        permission_lvl = PERMISSION_LEVELS.get(role, 0)
        
        # Create user based on role
        if role == 'client':
            new_user = CMSClientUser(
                user_name=username,
                user_email=email,
                user_pswd="",  # Will be set by set_password
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
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
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
        
        return jsonify({
            'success': True,
            'message': f'User registered successfully as {role}',
            'token': token,
            'user': {
                'id': new_user.id,
                'username': new_user.user_name,
                'email': new_user.user_email,
                'role': role
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        SecurityLogger.log_suspicious_activity("Registration error", str(e))
        # Don't expose internal errors to user
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500
    finally:
        db.close()

@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit login attempts
def login():
    """
    User login endpoint with security measures
    Security features:
    - Input validation
    - Password verification with bcrypt
    - Rate limiting to prevent brute force
    - Secure error messages (no email enumeration)
    - JWT token generation
    - Audit logging
    """
    data = request.get_json()
    db = SessionLocal()
    
    try:
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validate inputs
        if not email or not password:
            return jsonify({'success': False, 'message': 'Missing email or password'}), 400
        
        is_valid, error_msg = InputValidator.validate_email(email)
        if not is_valid:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        # Attempt login (password verification happens in CMSUser.login)
        user = CMSUser.login(db, email, password)
        
        if not user:
            # Log failed attempt
            SecurityLogger.log_failed_login(email, request.remote_addr)
            # Use generic error message to prevent email enumeration
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        # Log successful login
        SecurityLogger.log_successful_login(email, request.remote_addr)
        
        # Determine role from permission level
        role = 'client'
        for role_name, perm_level in PERMISSION_LEVELS.items():
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
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.user_name,
                'email': user.user_email,
                'role': role,
                'roleDisplay': ROLE_NAMES.get(user.permission_lvl, 'Unknown')
            }
        }), 200
        
    except Exception as e:
        SecurityLogger.log_suspicious_activity("Login error", str(e))
        return jsonify({'success': False, 'message': 'Login failed. Please try again.'}), 500
    finally:
        db.close()

@app.route('/api/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    db = SessionLocal()
    
    try:
        email = data.get('email')
        
        if not email:
            return jsonify({'exists': False}), 400
        
        user = db.query(CMSUser).filter_by(user_email=email).first()
        
        return jsonify({'exists': user is not None}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/client/events', methods=['GET'])
@require_auth
def get_client_events():
    """Get all events for authenticated client with access control"""
    db = SessionLocal()
    
    try:
        # Users can only see their own events
        user_id = request.user_id
        
        events = db.query(Event).filter_by(client_id=user_id).all()
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'location': event.location,
                'notes': event.notes,
                'price_total': event.price_total,
                'status': event.get_status(verbose=True),
                'status_code': event.status,
                'payment_confirmed': event.payment_confirmed,
                'created_at': event.created_at.isoformat() if event.created_at else None
            })
        
        return jsonify({
            'success': True,
            'events': events_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/client/create-event', methods=['POST'])
@require_auth
def create_event():
    """Create event with input validation and sanitization"""
    data = request.get_json()
    db = SessionLocal()
    
    try:
        user_id = request.user_id
        event_date_str = data.get('event_date', '').strip()
        title = InputValidator.sanitize_string(data.get('title', ''), max_length=200)
        location = InputValidator.sanitize_string(data.get('location', ''), max_length=300)
        notes = InputValidator.sanitize_string(data.get('notes', ''), max_length=1000)
        
        # Validate price
        try:
            price_total = float(data.get('price_total', 0.0))
            if price_total < 0:
                return jsonify({'success': False, 'message': 'Price cannot be negative'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid price format'}), 400
        
        if not event_date_str:
            return jsonify({'success': False, 'message': 'Event date is required'}), 400
        
        # Get user
        user = db.query(CMSClientUser).filter_by(id=user_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Parse event date
        try:
            event_date = datetime.fromisoformat(event_date_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format. Use ISO format (YYYY-MM-DD HH:mm)'}), 400
        
        # Create event
        new_event = Event(
            client_name=user.user_name,
            client_email=user.user_email,
            client_id=user.id,
            event_date=event_date,
            title=title,
            location=location,
            notes=notes,
            price_total=price_total
        )
        
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        
        return jsonify({
            'success': True,
            'message': 'Event created successfully',
            'event': {
                'id': new_event.id,
                'title': new_event.title,
                'event_date': new_event.event_date.isoformat(),
                'location': new_event.location,
                'notes': new_event.notes,
                'price_total': new_event.price_total,
                'status': new_event.get_status(verbose=True),
                'created_at': new_event.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/client/cancel-event', methods=['POST'])
@require_auth
def cancel_event():
    """Cancel event with access control - users can only cancel their own events"""
    data = request.get_json()
    db = SessionLocal()
    
    try:
        user_id = request.user_id
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'success': False, 'message': 'Event ID is required'}), 400
        
        # Validate event_id
        is_valid, error_msg, validated_id = InputValidator.validate_id(event_id)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        # Ensure user can only cancel their own events
        event = db.query(Event).filter_by(id=validated_id, client_id=user_id).first()
        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        
        event.set_status(10)  # cancelled
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event cancelled successfully'
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/planner/events', methods=['GET'])
@require_role(1)  # Planner level required
def get_planner_events():
    """Get events assigned to authenticated planner"""
    db = SessionLocal()
    
    try:
        user_id = request.user_id
        
        planner = db.query(CMSEventPLanner).filter_by(id=user_id).first()
        if not planner:
            return jsonify({'success': False, 'message': 'Planner not found'}), 404
        
        # Get all events assigned to this planner, sorted by date
        events = sorted(planner.events, key=lambda e: e.event_date if e.event_date else datetime.max)
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'client_name': event.client_name,
                'client_email': event.client_email,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'location': event.location,
                'notes': event.notes,
                'price_total': event.price_total,
                'status': event.get_status(verbose=True),
                'status_code': event.status,
                'payment_confirmed': event.payment_confirmed,
                'created_at': event.created_at.isoformat() if event.created_at else None
            })
        
        return jsonify({
            'success': True,
            'events': events_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/admin/events', methods=['GET'])
@require_role(2)  # Admin level required
def get_admin_events():
    """Get all events (admin only) with proper authorization"""
    db = SessionLocal()
    
    try:
        user_id = request.user_id
        
        admin = db.query(CMSAdminUser).filter_by(id=user_id).first()
        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found'}), 404
        
        # Get all events in the system, sorted by date
        all_events = db.query(Event).all()
        events = sorted(all_events, key=lambda e: e.event_date if e.event_date else datetime.max)
        
        # Get all planners (filter by permission level 1)
        planners = db.query(CMSEventPLanner).filter_by(permission_lvl=1).all()
        planners_data = []
        for planner in planners:
            planners_data.append({
                'id': planner.id,
                'username': planner.user_name,
                'email': planner.user_email
            })
        
        events_data = []
        for event in events:
            # Get assigned planners for this event
            assigned_planners = [str(p.id) for p in event.planners]
            
            events_data.append({
                'id': event.id,
                'title': event.title,
                'client_name': event.client_name,
                'client_email': event.client_email,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'location': event.location,
                'notes': event.notes,
                'price_total': event.price_total,
                'status': event.get_status(verbose=True),
                'status_code': event.status,
                'payment_confirmed': event.payment_confirmed,
                'assigned_planners': ','.join(assigned_planners) if assigned_planners else '',
                'created_at': event.created_at.isoformat() if event.created_at else None
            })
        
        return jsonify({
            'success': True,
            'events': events_data,
            'planners': planners_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/admin/assign-planner', methods=['POST'])
@require_role(2)  # Admin only
def assign_planner():
    """Assign planner to event (admin only) with input validation"""
    data = request.get_json()
    db = SessionLocal()
    
    try:
        admin_id = request.user_id
        event_id = data.get('event_id')
        planner_id = data.get('planner_id')
        
        if not all([event_id, planner_id]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Validate IDs
        is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
        if not is_valid:
            return jsonify({'success': False, 'message': f'Event ID: {error_msg}'}), 400
        
        is_valid, error_msg, validated_planner_id = InputValidator.validate_id(planner_id)
        if not is_valid:
            return jsonify({'success': False, 'message': f'Planner ID: {error_msg}'}), 400
        
        admin = db.query(CMSAdminUser).filter_by(id=admin_id).first()
        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found'}), 404
        
        if admin.assign_planner_to_event(db, validated_event_id, validated_planner_id):
            event = Event.get_by_id(db, validated_event_id)
            return jsonify({
                'success': True,
                'message': 'Planner assigned successfully and event status changed to pre-approval',
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'status': event.get_status(verbose=True),
                    'status_code': event.status
                }
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to assign planner or planner already assigned'}), 400
        
    except PermissionError as e:
        return jsonify({'success': False, 'message': str(e)}), 403
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/admin/assign-planners', methods=['POST'])
@require_role(2)  # Admin only
def assign_planners():
    """Assign multiple planners to an event (admin only) with validation"""
    data = request.get_json()
    db = SessionLocal()
    
    try:
        admin_id = request.user_id
        event_id = data.get('event_id')
        planner_ids = data.get('planner_ids', [])
        
        if not event_id:
            return jsonify({'success': False, 'message': 'Event ID is required'}), 400
        
        # Validate event ID
        is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        admin = db.query(CMSAdminUser).filter_by(id=admin_id).first()
        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found'}), 404
        
        event = Event.get_by_id(db, validated_event_id)
        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        
        # Clear existing planners and assign new ones
        event.planners.clear()
        
        assigned_count = 0
        for planner_id in planner_ids:
            # Validate each planner ID
            is_valid, error_msg, validated_planner_id = InputValidator.validate_id(planner_id)
            if not is_valid:
                continue  # Skip invalid IDs
            
            planner = db.query(CMSEventPLanner).filter_by(id=validated_planner_id).first()
            if planner:
                event.planners.append(planner)
                assigned_count += 1
        
        # Set status to pre-approval if planners are assigned
        if assigned_count > 0:
            event.set_status(2)  # pre-approval
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'{assigned_count} planner(s) assigned successfully',
            'event': {
                'id': event.id,
                'title': event.title,
                'assigned_planner_count': assigned_count
            }
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/admin/cancel-event', methods=['POST'])
@require_role(2)  # Admin only
def cancel_event_admin():
    """Admin endpoint to cancel an event with authorization"""
    data = request.get_json()
    db = SessionLocal()
    
    try:
        admin_id = request.user_id
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'success': False, 'message': 'Event ID is required'}), 400
        
        # Validate ID
        is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        admin = db.query(CMSAdminUser).filter_by(id=admin_id).first()
        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found'}), 404
        
        event = Event.get_by_id(db, int(event_id))
        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        
        event.set_status(10)  # cancelled
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event cancelled successfully',
            'event': {
                'id': event.id,
                'title': event.title,
                'status': event.get_status(verbose=True),
                'status_code': event.status
            }
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/planner/accept-event', methods=['POST'])
@require_role(1)  # Planner level required
def accept_event():
    """Planner accepts event with authorization check"""
    data = request.get_json()
    db = SessionLocal()
    
    try:
        user_id = request.user_id
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'success': False, 'message': 'Event ID is required'}), 400
        
        # Validate ID
        is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        planner = db.query(CMSEventPLanner).filter_by(id=user_id).first()
        if not planner:
            return jsonify({'success': False, 'message': 'Planner not found'}), 404
        
        if planner.accept_event(db, validated_event_id):
            event = Event.get_by_id(db, validated_event_id)
            return jsonify({
                'success': True,
                'message': 'Event accepted successfully',
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'status': event.get_status(verbose=True),
                    'status_code': event.status
                }
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Event not in pre-approval status or not assigned to planner'}), 400
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/planner/decline-event', methods=['POST'])
@require_role(1)  # Planner level required
def decline_event():
    """Planner declines event with authorization check"""
    data = request.get_json()
    db = SessionLocal()
    
    try:
        user_id = request.user_id
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'success': False, 'message': 'Event ID is required'}), 400
        
        # Validate ID
        is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        planner = db.query(CMSEventPLanner).filter_by(id=user_id).first()
        if not planner:
            return jsonify({'success': False, 'message': 'Planner not found'}), 404
        
        if planner.decline_event(db, validated_event_id):
            event = Event.get_by_id(db, validated_event_id)
            return jsonify({
                'success': True,
                'message': 'Event declined successfully',
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'status': event.get_status(verbose=True),
                    'status_code': event.status
                }
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Event not in pre-approval status or not assigned to planner'}), 400
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/')
def index():
    """Serve the main HTML file"""
    from flask import send_from_directory
    return send_from_directory('src/web', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')
