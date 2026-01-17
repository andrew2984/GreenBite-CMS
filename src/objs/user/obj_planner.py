from sqlalchemy.orm import relationship
from .obj_user import CMSUser
from ..obj_event import Event, event_planner_association


# Event Planner
class CMSEventPLanner(CMSUser):
    events = relationship(
        "Event", secondary=event_planner_association, back_populates="planners"
    )

    def view_all_events(self, db):
        if self.permission_lvl < 1:
            raise PermissionError("Insufficient permissions to view all events.")
        events = db.query(Event).all()
        Event.print_events_table(events)

    def get_assigned_events(self, db):
        return self.events

    def get_assigned_events_list(self, db):
        if self.events:
            Event.print_events_table(self.events)
        else:
            print("No events assigned to this planner.")

    def accept_event(self, db, event_id):
        """Accept an event (change status from pre-approval to accepted)"""
        event = Event.get_by_id(db, event_id)
        if not event or event not in self.events:
            return False

        if event.status == 2:  # pre-approval
            event.set_status(3)  # accepted
            db.commit()
            return True
        return False

    def decline_event(self, db, event_id):
        """Decline an event (change status from pre-approval to declined)"""
        event = Event.get_by_id(db, event_id)
        if not event or event not in self.events:
            return False

        if event.status == 2:  # pre-approval
            event.set_status(4)  # declined
            # Remove planner from event so it can be reassigned
            self.events.remove(event)
            db.commit()
            return True
        return False
