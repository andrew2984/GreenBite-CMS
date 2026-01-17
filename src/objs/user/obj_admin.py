from sqlalchemy.orm import relationship
from .obj_user import CMSUser
from ..obj_event import Event


class CMSAdminUser(CMSUser):

    def assign_planner_to_event(self, db, event_id, planner_id):
        if self.permission_lvl < 2:
            raise PermissionError("Insufficient permissions to assign planners.")

        event = Event.get_by_id(db, event_id)
        if not event:
            return False

        from .obj_planner import CMSEventPLanner

        planner = db.query(CMSEventPLanner).filter_by(id=planner_id).first()
        if not planner:
            return False

        if planner not in event.planners:
            event.planners.append(planner)
            event.set_status(2)  # Change status to "pre-approval"
            db.commit()
            return True
        return False

    def remove_planner_from_event(self, db, event_id, planner_id):
        if self.permission_lvl < 2:
            raise PermissionError("Insufficient permissions to remove planners.")

        event = Event.get_by_id(db, event_id)
        if not event:
            return False

        from .obj_planner import CMSEventPLanner

        planner = db.query(CMSEventPLanner).filter_by(id=planner_id).first()
        if not planner:
            return False

        if planner in event.planners:
            event.planners.remove(planner)
            db.commit()
            return True
        return False

    def get_event_planners(self, db, event_id):
        event = Event.get_by_id(db, event_id)
        if event:
            return event.planners
        return []

    def get_planner_events(self, db, planner_id):
        from .obj_planner import CMSEventPLanner

        planner = db.query(CMSEventPLanner).filter_by(id=planner_id).first()
        if planner:
            return planner.events
        return []
