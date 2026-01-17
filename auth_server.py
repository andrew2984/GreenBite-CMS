from flask import Flask, request, jsonify
from flask_cors import CORS
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

Base.metadata.create_all(bind=engine)

app = Flask(__name__)
CORS(app)

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

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    db = SessionLocal()
    
    try:
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'client')
        
 
        if not all([username, email, password, role]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        existing_user = db.query(CMSUser).filter_by(user_email=email).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        permission_lvl = PERMISSION_LEVELS.get(role, 0)
        
        if role == 'client':
            new_user = CMSClientUser(
                user_name=username,
                user_email=email,
                user_pswd=password,
                permission_lvl=permission_lvl
            )
        elif role == 'planner':
            new_user = CMSEventPLanner(
                user_name=username,
                user_email=email,
                user_pswd=password,
                permission_lvl=permission_lvl
            )
        elif role == 'admin':
            new_user = CMSAdminUser(
                user_name=username,
                user_email=email,
                user_pswd=password,
                permission_lvl=permission_lvl
            )
        else:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return jsonify({
            'success': True,
            'message': f'User registered successfully as {role}',
            'user': {
                'id': new_user.id,
                'username': new_user.user_name,
                'email': new_user.user_email,
                'role': role
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    db = SessionLocal()
    
    try:
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Missing email or password'}), 400
        
        user = CMSUser.login(db, email, password)
        
        if not user:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        
        role = 'client'
        for role_name, perm_level in PERMISSION_LEVELS.items():
            if perm_level == user.permission_lvl:
                role = role_name
                break
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.user_name,
                'email': user.user_email,
                'role': role,
                'roleDisplay': ROLE_NAMES.get(user.permission_lvl, 'Unknown')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
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
def get_client_events():
    user_id = request.args.get('user_id')
    db = SessionLocal()
    
    try:
        if not user_id:
            return jsonify({'success': False, 'message': 'Missing user_id'}), 400
        
        events = db.query(Event).filter_by(client_id=int(user_id)).all()
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
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
def create_event():
    data = request.get_json()
    db = SessionLocal()
    
    try:
        user_id = data.get('user_id')
        event_date_str = data.get('event_date')
        location = data.get('location')
        notes = data.get('notes')
        price_total = float(data.get('price_total', 0.0))
        
        if not all([user_id, event_date_str]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Get user
        user = db.query(CMSClientUser).filter_by(id=int(user_id)).first()
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
def cancel_event():
    data = request.get_json()
    db = SessionLocal()
    
    try:
        user_id = data.get('user_id')
        event_id = data.get('event_id')
        
        if not all([user_id, event_id]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        event = db.query(Event).filter_by(id=int(event_id), client_id=int(user_id)).first()
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
