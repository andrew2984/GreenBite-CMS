from typing import Tuple, Dict, List, Optional
from datetime import datetime
from ..objs.user.obj_planner import CMSEventPLanner
from ..objs.obj_event import Event
from ..security.security_utils import InputValidator

# service layer class to handle planner-related business logic
class PlannerService:
    
    @staticmethod
    def get_planner_events(
        db,
        user_id: int
    ) -> Tuple[bool, str, Optional[List[Dict]], int]:
        try:
            planner = db.query(CMSEventPLanner).filter_by(id=user_id).first()
            if not planner:
                return False, 'Planner not found', None, 404
            
            # Get all events assigned to this planner, sorted by date
            events = sorted(
                planner.events,
                key=lambda e: e.event_date if e.event_date else datetime.max
            )
            
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
            
            return True, 'Events retrieved successfully', events_data, 200
            
        except Exception as e:
            return False, f'Error: {str(e)}', None, 500
    
    @staticmethod
    def accept_event(
        db,
        user_id: int,
        event_id: int
    ) -> Tuple[bool, str, Optional[Dict], int]:
        try:
            if not event_id:
                return False, 'Event ID is required', None, 400
            
            # Validate ID
            is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
            if not is_valid:
                return False, error_msg, None, 400
            
            planner = db.query(CMSEventPLanner).filter_by(id=user_id).first()
            if not planner:
                return False, 'Planner not found', None, 404
            
            if planner.accept_event(db, validated_event_id):
                event = Event.get_by_id(db, validated_event_id)
                event_data = {
                    'id': event.id,
                    'title': event.title,
                    'status': event.get_status(verbose=True),
                    'status_code': event.status
                }
                return True, 'Event accepted successfully', event_data, 200
            else:
                return False, 'Event not in pre-approval status or not assigned to planner', None, 400
            
        except Exception as e:
            db.rollback()
            return False, f'Error: {str(e)}', None, 500
    
    @staticmethod
    def decline_event(
        db,
        user_id: int,
        event_id: int
    ) -> Tuple[bool, str, Optional[Dict], int]:
        try:
            if not event_id:
                return False, 'Event ID is required', None, 400
            
            # Validate ID
            is_valid, error_msg, validated_event_id = InputValidator.validate_id(event_id)
            if not is_valid:
                return False, error_msg, None, 400
            
            planner = db.query(CMSEventPLanner).filter_by(id=user_id).first()
            if not planner:
                return False, 'Planner not found', None, 404
            
            if planner.decline_event(db, validated_event_id):
                event = Event.get_by_id(db, validated_event_id)
                event_data = {
                    'id': event.id,
                    'title': event.title,
                    'status': event.get_status(verbose=True),
                    'status_code': event.status
                }
                return True, 'Event declined successfully', event_data, 200
            else:
                return False, 'Event not in pre-approval status or not assigned to planner', None, 400
            
        except Exception as e:
            db.rollback()
            return False, f'Error: {str(e)}', None, 500
