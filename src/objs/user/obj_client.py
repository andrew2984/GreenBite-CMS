from sqlalchemy.orm import relationship
from .obj_user import CMSUser
from ..obj_event import Event

class CMSClientUser(CMSUser):
    event = relationship("Event", back_populates="user")

    @classmethod
    def get_events(self, db):
        return db.query(Event).filter_by(client_id=self.id).all() 
    
    def request_event(self, db, event_date, location=None, notes=None, price_total=0.0):
        new_event = Event(
            client_name=self.user_name,
            client_email=self.user_email,
            client_id=self.id,
            event_date=event_date,
            location=location,
            notes=notes,
            price_total=price_total
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event
    
    def cancel_event(self, db, event_id):
        event = db.query(Event).filter_by(id=event_id, client_id=self.id).first()
        if event:
            event.set_status(10)  # hashtag cancelled
            db.commit()
            return True
        return False
    
    def check_event_status(self, db, event_id):
        event = db.query(Event).filter_by(id=event_id, client_id=self.id).first()
        if event:
            return event.get_status(verbose=True)
        return None
    
    def pay_for_event(self, db, event_id):
        event = db.query(Event).filter_by(id=event_id, client_id=self.id).first()
        if event and event.status == 7:
            event.mark_payment_confirmed()
            db.commit()
            return True
        return False