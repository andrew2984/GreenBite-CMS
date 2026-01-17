from typing import Tuple, Dict, List, Optional
from datetime import datetime
from ..objs.obj_event import Event
from ..objs.user.obj_client import CMSClientUser
from ..security.security_utils import InputValidator

# service layer class to handle event-related business logic
class EventService:
    
    @staticmethod
    def get_client_events(db, user_id: int) -> Tuple[bool, str, Optional[List[Dict]], int]:

        try:
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
            
            return True, 'Events retrieved successfully', events_data, 200
            
        except Exception as e:
            return False, f'Error: {str(e)}', None, 500
    
    @staticmethod
    def create_event(
        db,
        user_id: int,
        event_date_str: str,
        title: str = '',
        location: str = '',
        notes: str = '',
        price_total: float = 0.0
    ) -> Tuple[bool, str, Optional[Dict], int]:

        try:
            # Sanitize inputs
            title = InputValidator.sanitize_string(title, max_length=200)
            location = InputValidator.sanitize_string(location, max_length=300)
            notes = InputValidator.sanitize_string(notes, max_length=1000)
            
            # Validate price
            try:
                price_total = float(price_total)
                if price_total < 0:
                    return False, 'Price cannot be negative', None, 400
            except ValueError:
                return False, 'Invalid price format', None, 400
            
            if not event_date_str:
                return False, 'Event date is required', None, 400
            
            # Get user
            user = db.query(CMSClientUser).filter_by(id=user_id).first()
            if not user:
                return False, 'User not found', None, 404
            
            # Parse event date
            try:
                event_date = datetime.fromisoformat(event_date_str)
            except ValueError:
                return False, 'Invalid date format. Use ISO format (YYYY-MM-DD HH:mm)', None, 400
            
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
            
            event_data = {
                'id': new_event.id,
                'title': new_event.title,
                'event_date': new_event.event_date.isoformat(),
                'location': new_event.location,
                'notes': new_event.notes,
                'price_total': new_event.price_total,
                'status': new_event.get_status(verbose=True),
                'created_at': new_event.created_at.isoformat()
            }
            
            return True, 'Event created successfully', event_data, 201
            
        except Exception as e:
            db.rollback()
            return False, f'Error: {str(e)}', None, 500
    
    @staticmethod
    def cancel_event(
        db,
        user_id: int,
        event_id: int
    ) -> Tuple[bool, str, int]:

        try:
            if not event_id:
                return False, 'Event ID is required', 400
            
            # Validate event_id
            is_valid, error_msg, validated_id = InputValidator.validate_id(event_id)
            if not is_valid:
                return False, error_msg, 400
            
            # Ensure user can only cancel their own events
            event = db.query(Event).filter_by(id=validated_id, client_id=user_id).first()
            if not event:
                return False, 'Event not found', 404
            
            event.set_status(10)  # cancelled
            db.commit()
            
            return True, 'Event cancelled successfully', 200
            
        except Exception as e:
            db.rollback()
            return False, f'Error: {str(e)}', 500
    
    @staticmethod
    def get_event_by_id(db, event_id: int) -> Optional[Event]:
        return Event.get_by_id(db, event_id)
