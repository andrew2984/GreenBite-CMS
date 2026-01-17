from sqlalchemy.orm import relationship
from .obj_user import CMSUser
from ..obj_event import Event

class CMSEventPLanner(CMSUser):
    
    def view_all_events(self, db):
        if self.permission_lvl < 1:
            raise PermissionError("Insufficient permissions to view all events.")
        events = db.query(Event).all()
        Event.print_events_table(events)