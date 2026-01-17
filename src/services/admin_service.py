from typing import Tuple, Dict, List, Optional
from datetime import datetime
from ..objs.user.obj_admin import CMSAdminUser
from ..objs.user.obj_planner import CMSEventPLanner
from ..objs.obj_event import Event
from ..security.security_utils import InputValidator

# service layer classes to handle admin-related business logic
class AdminService:
    
    @staticmethod
    def get_all_events(
        db,
        user_id: int
    ) -> Tuple[bool, str, Optional[Dict], int]:
        try:
            admin = db.query(CMSAdminUser).filter_by(id=user_id).first()
            if not admin:
                return False, 'Admin not found', None, 404
            
            # Get all events, sorted by date
            all_events = db.query(Event).all()
            events = sorted(
                all_events,
                key=lambda e: e.event_date if e.event_date else datetime.max
            )
            
            # Get all planners
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
            
            result = {
                'events': events_data,
                'planners': planners_data
            }
            
            return True, 'Events retrieved successfully', result, 200
            
        except Exception as e:
            return False, f'Error: {str(e)}', None, 500
    
    @staticmethod
    def assign_planner_to_event(
        db,
        admin_id: int,
        event_id: int,
        planner_id: int
    ) -> Tuple[bool, str, Optional[Dict], int]:
        try:
            if not all([event_id, planner_id]):
                return False, 'Missing required fields', None, 400
            
            # Validate IDs
            is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
            if not is_valid:
                return False, f'Event ID: {error_msg}', None, 400
            
            is_valid, error_msg, validated_planner_id = InputValidator.validate_id(planner_id)
            if not is_valid:
                return False, f'Planner ID: {error_msg}', None, 400
            
            admin = db.query(CMSAdminUser).filter_by(id=admin_id).first()
            if not admin:
                return False, 'Admin not found', None, 404
            
            if admin.assign_planner_to_event(db, validated_event_id, validated_planner_id):
                event = Event.get_by_id(db, validated_event_id)
                event_data = {
                    'id': event.id,
                    'title': event.title,
                    'status': event.get_status(verbose=True),
                    'status_code': event.status
                }
                return True, 'Planner assigned successfully and event status changed to pre-approval', event_data, 200
            else:
                return False, 'Failed to assign planner or planner already assigned', None, 400
            
        except PermissionError as e:
            return False, str(e), None, 403
        except Exception as e:
            db.rollback()
            return False, f'Error: {str(e)}', None, 500
    
    @staticmethod
    def assign_multiple_planners(
        db,
        admin_id: int,
        event_id: int,
        planner_ids: List[int]
    ) -> Tuple[bool, str, Optional[Dict], int]:
 
        try:
            if not event_id:
                return False, 'Event ID is required', None, 400
            
            # Validate event ID
            is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
            if not is_valid:
                return False, error_msg, None, 400
            
            admin = db.query(CMSAdminUser).filter_by(id=admin_id).first()
            if not admin:
                return False, 'Admin not found', None, 404
            
            event = Event.get_by_id(db, validated_event_id)
            if not event:
                return False, 'Event not found', None, 404
            
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
            
            event_data = {
                'id': event.id,
                'title': event.title,
                'assigned_planner_count': assigned_count
            }
            
            return True, f'{assigned_count} planner(s) assigned successfully', event_data, 200
            
        except Exception as e:
            db.rollback()
            return False, f'Error: {str(e)}', None, 500
    
    @staticmethod
    def cancel_event(
        db,
        admin_id: int,
        event_id: int
    ) -> Tuple[bool, str, Optional[Dict], int]:

        try:
            if not event_id:
                return False, 'Event ID is required', None, 400
            
            # Validate ID
            is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
            if not is_valid:
                return False, error_msg, None, 400
            
            admin = db.query(CMSAdminUser).filter_by(id=admin_id).first()
            if not admin:
                return False, 'Admin not found', None, 404
            
            event = Event.get_by_id(db, validated_event_id)
            if not event:
                return False, 'Event not found', None, 404
            
            event.set_status(10)  # cancelled
            db.commit()
            
            event_data = {
                'id': event.id,
                'title': event.title,
                'status': event.get_status(verbose=True),
                'status_code': event.status
            }
            
            return True, 'Event cancelled successfully', event_data, 200
            
        except Exception as e:
            db.rollback()
            return False, f'Error: {str(e)}', None, 500
