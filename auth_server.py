from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.database import engine, Base
from src.objs.user.obj_user import CMSUser
from src.security.security_utils import require_auth, require_role
from src.services import AuthService, EventService, AdminService, PlannerService

from src.objs.config import DevelopmentConfig, DevServerConfig
from decouple import config

app = Flask(__name__,
    static_folder='src/web',
    static_url_path='')

env = config('FLASK_ENV', default='development')

if env == "development":
    app.config.from_object(DevelopmentConfig)
elif env == "dev_server":
    app.config.from_object(DevServerConfig)

connection_string = app.config['CONNECTION_STRING']

engine = create_engine(connection_string, echo=True)
Session = sessionmaker(bind=engine)

#Base.metadata.create_all(bind=engine)

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
connect_src = app.config['CONNECT_SRC']

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    #response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Content-Security-Policy'] = (
    "script-src 'self' 'unsafe-inline' 'unsafe-hashes'; "
    "style-src 'self' 'unsafe-inline'; "
    f"connect-src {connect_src}"
    )
    return response

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    db = Session()
    try:
        username = data.get('username', '')
        email = data.get('email', '')
        password = data.get('password', '')
        role = data.get('role', 'client')
        success, message, user_data, status_code = AuthService.register_user(db, username, email, password, role)
        if success:
            return jsonify(user_data), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    db = Session()
    try:
        email = data.get('email', '')
        password = data.get('password', '')
        success, message, user_data, status_code = AuthService.login_user(db, email, password, request.remote_addr)
        if success:
            return jsonify(user_data), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    db = Session()
    try:
        email = data.get('email')
        exists, status_code = AuthService.check_email_exists(db, email)
        return jsonify({'exists': exists}), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/client/events', methods=['GET'])
@require_auth
def get_client_events():
    db = Session()
    try:
        success, message, events_data, status_code = EventService.get_client_events(db, request.user_id)
        if success:
            return jsonify({'success': True, 'events': events_data}), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/client/create-event', methods=['POST'])
@require_auth
def create_event():
    data = request.get_json()
    db = Session()
    try:
        success, message, event_data, status_code = EventService.create_event(
            db, request.user_id, data.get('event_date', ''), data.get('title', ''),
            data.get('location', ''), data.get('notes', ''), data.get('price_total', 0.0)
        )
        if success:
            return jsonify({'success': True, 'message': message, 'event': event_data}), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/client/cancel-event', methods=['POST'])
@require_auth
def cancel_event():
    data = request.get_json()
    db = Session()
    try:
        success, message, status_code = EventService.cancel_event(db, request.user_id, data.get('event_id'))
        return jsonify({'success': success, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/planner/events', methods=['GET'])
@require_role(1)
def get_planner_events():
    db = Session()
    try:
        success, message, events_data, status_code = PlannerService.get_planner_events(db, request.user_id)
        if success:
            return jsonify({'success': True, 'events': events_data}), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/admin/events', methods=['GET'])
@require_role(2)
def get_admin_events():
    db = Session()
    try:
        success, message, data, status_code = AdminService.get_all_events(db, request.user_id)
        if success:
            return jsonify({'success': True, 'events': data['events'], 'planners': data['planners']}), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/admin/assign-planner', methods=['POST'])
@require_role(2)
def assign_planner():
    data = request.get_json()
    db = Session()
    try:
        success, message, event_data, status_code = AdminService.assign_planner_to_event(
            db, request.user_id, data.get('event_id'), data.get('planner_id')
        )
        if success:
            return jsonify({'success': True, 'message': message, 'event': event_data}), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/admin/assign-planners', methods=['POST'])
@require_role(2)
def assign_planners():
    data = request.get_json()
    db = Session()
    try:
        success, message, event_data, status_code = AdminService.assign_multiple_planners(
            db, request.user_id, data.get('event_id'), data.get('planner_ids', [])
        )
        if success:
            return jsonify({'success': True, 'message': message, 'event': event_data}), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/admin/cancel-event', methods=['POST'])
@require_role(2)
def cancel_event_admin():
    data = request.get_json()
    db = Session()
    try:
        success, message, event_data, status_code = AdminService.cancel_event(db, request.user_id, data.get('event_id'))
        if success:
            return jsonify({'success': True, 'message': message, 'event': event_data}), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/planner/accept-event', methods=['POST'])
@require_role(1)
def accept_event():
    data = request.get_json()
    db = Session()
    try:
        success, message, event_data, status_code = PlannerService.accept_event(db, request.user_id, data.get('event_id'))
        if success:
            return jsonify({'success': True, 'message': message, 'event': event_data}), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/api/planner/decline-event', methods=['POST'])
@require_role(1)
def decline_event():
    data = request.get_json()
    db = Session()
    try:
        success, message, event_data, status_code = PlannerService.decline_event(db, request.user_id, data.get('event_id'))
        if success:
            return jsonify({'success': True, 'message': message, 'event': event_data}), status_code
        else:
            return jsonify({'success': False, 'message': message}), status_code
    finally:
        db.close()

@app.route('/')
def index():
    from flask import send_from_directory
    return send_from_directory('src/web', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')