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
def create_event():
    data = request.get_json()
    db = SessionLocal()
    
    try:
        user_id = data.get('user_id')
        event_date_str = data.get('event_date')
        title = data.get('title')
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

@app.route('/api/planner/events', methods=['GET'])
def get_planner_events():
    user_id = request.args.get('user_id')
    db = SessionLocal()
    
    try:
        if not user_id:
            return jsonify({'success': False, 'message': 'Missing user_id'}), 400
        
        planner = db.query(CMSEventPLanner).filter_by(id=int(user_id)).first()
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
def get_admin_events():
    user_id = request.args.get('user_id')
    db = SessionLocal()
    
    try:
        if not user_id:
            return jsonify({'success': False, 'message': 'Missing user_id'}), 400
        
        admin = db.query(CMSAdminUser).filter_by(id=int(user_id)).first()
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
def assign_planner():
    data = request.get_json()
    db = SessionLocal()
    
    try:
        admin_id = data.get('admin_id')
        event_id = data.get('event_id')
        planner_id = data.get('planner_id')
        
        if not all([admin_id, event_id, planner_id]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        admin = db.query(CMSAdminUser).filter_by(id=int(admin_id)).first()
        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found'}), 404
        
        if admin.assign_planner_to_event(db, int(event_id), int(planner_id)):
            event = Event.get_by_id(db, int(event_id))
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
def assign_planners():
    """Assign multiple planners to an event (replaces existing assignments)"""
    data = request.get_json()
    db = SessionLocal()
    
    try:
        admin_id = data.get('user_id')
        event_id = data.get('event_id')
        planner_ids = data.get('planner_ids', [])
        
        if not admin_id or not event_id:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        admin = db.query(CMSAdminUser).filter_by(id=int(admin_id)).first()
        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found'}), 404
        
        event = Event.get_by_id(db, int(event_id))
        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        
        # Clear existing planners and assign new ones
        event.planners.clear()
        
        assigned_count = 0
        for planner_id in planner_ids:
            planner = db.query(CMSEventPLanner).filter_by(id=int(planner_id)).first()
            if planner:
                event.planners.append(planner)
                assigned_count += 1
        
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
def cancel_event_admin():
    """Admin endpoint to cancel an event"""
    data = request.get_json()
    db = SessionLocal()
    
    try:
        admin_id = data.get('user_id')
        event_id = data.get('event_id')
        
        if not all([admin_id, event_id]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        admin = db.query(CMSAdminUser).filter_by(id=int(admin_id)).first()
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
def accept_event():
    data = request.get_json()
    db = SessionLocal()
    
    try:
        user_id = data.get('user_id')
        event_id = data.get('event_id')
        
        if not all([user_id, event_id]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        planner = db.query(CMSEventPLanner).filter_by(id=int(user_id)).first()
        if not planner:
            return jsonify({'success': False, 'message': 'Planner not found'}), 404
        
        if planner.accept_event(db, int(event_id)):
            event = Event.get_by_id(db, int(event_id))
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
def decline_event():
    data = request.get_json()
    db = SessionLocal()
    
    try:
        user_id = data.get('user_id')
        event_id = data.get('event_id')
        
        if not all([user_id, event_id]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        planner = db.query(CMSEventPLanner).filter_by(id=int(user_id)).first()
        if not planner:
            return jsonify({'success': False, 'message': 'Planner not found'}), 404
        
        if planner.decline_event(db, int(event_id)):
            event = Event.get_by_id(db, int(event_id))
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
