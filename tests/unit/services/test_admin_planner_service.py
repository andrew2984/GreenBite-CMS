"""
Unit tests for AdminService and PlannerService
"""
import pytest
from datetime import datetime, timedelta
from src.services.admin_service import AdminService
from src.services.planner_service import PlannerService
from src.objs.obj_event import Event


class TestAdminServiceGetAllEvents:
    """Test suite for admin getting all events."""
    
    def test_get_all_events_success(self, db_session, sample_admin, sample_event):
        """Test admin getting all events."""
        success, message, data, status_code = AdminService.get_all_events(
            db_session,
            sample_admin.id
        )
        
        assert success is True
        assert status_code == 200
        assert 'events' in data
        assert 'planners' in data
        assert isinstance(data['events'], list)
        assert isinstance(data['planners'], list)
    
    def test_get_all_events_with_planners(self, db_session, sample_admin, sample_event, sample_planner):
        """Test getting all events includes planner data."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        success, message, data, status_code = AdminService.get_all_events(
            db_session,
            sample_admin.id
        )
        
        assert success is True
        assert len(data['planners']) >= 1
        
        # Find the event with assigned planners
        for event in data['events']:
            if event['id'] == sample_event.id:
                assert str(sample_planner.id) in event['assigned_planners']
    
    def test_get_all_events_non_admin(self, db_session, sample_client):
        """Test non-admin cannot get all events."""
        success, message, data, status_code = AdminService.get_all_events(
            db_session,
            sample_client.id
        )
        
        assert success is False
        assert status_code == 404


class TestAdminServiceAssignPlanner:
    """Test suite for assigning planners to events."""
    
    def test_assign_planner_success(self, db_session, sample_admin, sample_planner, sample_event):
        """Test successfully assigning planner to event."""
        success, message, event_data, status_code = AdminService.assign_planner_to_event(
            db_session,
            admin_id=sample_admin.id,
            event_id=sample_event.id,
            planner_id=sample_planner.id
        )
        
        assert success is True
        assert status_code == 200
        assert event_data['status_code'] == 2  # pre-approval
    
    def test_assign_planner_invalid_event_id(self, db_session, sample_admin, sample_planner):
        """Test assigning planner with invalid event ID."""
        success, message, event_data, status_code = AdminService.assign_planner_to_event(
            db_session,
            admin_id=sample_admin.id,
            event_id="invalid",
            planner_id=sample_planner.id
        )
        
        assert success is False
        assert status_code == 400
    
    def test_assign_planner_invalid_planner_id(self, db_session, sample_admin, sample_event):
        """Test assigning invalid planner ID."""
        success, message, event_data, status_code = AdminService.assign_planner_to_event(
            db_session,
            admin_id=sample_admin.id,
            event_id=sample_event.id,
            planner_id="invalid"
        )
        
        assert success is False
        assert status_code == 400
    
    def test_assign_multiple_planners_success(self, db_session, sample_admin, sample_event):
        """Test assigning multiple planners to event."""
        # Create multiple planners
        from src.objs.user.obj_planner import CMSEventPLanner
        planner_ids = []
        
        for i in range(3):
            planner = CMSEventPLanner(
                user_name=f"planner_{i}",
                user_email=f"planner{i}@test.com",
                user_pswd="",
                permission_lvl=1
            )
            planner.set_password("Password123")
            db_session.add(planner)
            db_session.commit()
            planner_ids.append(planner.id)
        
        success, message, event_data, status_code = AdminService.assign_multiple_planners(
            db_session,
            admin_id=sample_admin.id,
            event_id=sample_event.id,
            planner_ids=planner_ids
        )
        
        assert success is True
        assert status_code == 200
        assert event_data['assigned_count'] == 3
    
    def test_assign_multiple_planners_replaces_existing(self, db_session, sample_admin, sample_event, sample_planner):
        """Test that assigning multiple planners replaces existing assignments."""
        # Assign initial planner
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        # Create new planner
        from src.objs.user.obj_planner import CMSEventPLanner
        new_planner = CMSEventPLanner(
            user_name="new_planner",
            user_email="new_planner@test.com",
            user_pswd="",
            permission_lvl=1
        )
        new_planner.set_password("Password123")
        db_session.add(new_planner)
        db_session.commit()
        
        success, message, event_data, status_code = AdminService.assign_multiple_planners(
            db_session,
            admin_id=sample_admin.id,
            event_id=sample_event.id,
            planner_ids=[new_planner.id]
        )
        
        assert success is True
        db_session.refresh(sample_event)
        assert len(sample_event.planners) == 1
        assert sample_event.planners[0].id == new_planner.id


class TestAdminServiceCancelEvent:
    """Test suite for admin cancelling events."""
    
    def test_admin_cancel_event_success(self, db_session, sample_admin, sample_event):
        """Test admin successfully cancelling an event."""
        success, message, event_data, status_code = AdminService.cancel_event(
            db_session,
            admin_id=sample_admin.id,
            event_id=sample_event.id
        )
        
        assert success is True
        assert status_code == 200
        
        db_session.refresh(sample_event)
        assert sample_event.status == 10  # cancelled
    
    def test_admin_cancel_nonexistent_event(self, db_session, sample_admin):
        """Test admin cancelling nonexistent event."""
        success, message, event_data, status_code = AdminService.cancel_event(
            db_session,
            admin_id=sample_admin.id,
            event_id=99999
        )
        
        assert success is False
        assert status_code == 404


class TestPlannerServiceGetEvents:
    """Test suite for planner getting assigned events."""
    
    def test_get_planner_events_success(self, db_session, sample_planner, sample_event):
        """Test planner getting assigned events."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        success, message, events_data, status_code = PlannerService.get_planner_events(
            db_session,
            sample_planner.id
        )
        
        assert success is True
        assert status_code == 200
        assert len(events_data) == 1
    
    def test_get_planner_events_empty(self, db_session, sample_planner):
        """Test getting events when planner has none assigned."""
        success, message, events_data, status_code = PlannerService.get_planner_events(
            db_session,
            sample_planner.id
        )
        
        assert success is True
        assert len(events_data) == 0
    
    def test_get_planner_events_sorted_by_date(self, db_session, sample_planner, sample_client):
        """Test that planner events are sorted by date."""
        # Create events with different dates
        dates = [timedelta(days=30), timedelta(days=10), timedelta(days=20)]
        for i, delta in enumerate(dates):
            event = Event(
                client_name=sample_client.user_name,
                client_email=sample_client.user_email,
                client_id=sample_client.id,
                event_date=datetime.utcnow() + delta,
                title=f"Event {i}"
            )
            event.planners.append(sample_planner)
            db_session.add(event)
        db_session.commit()
        
        success, message, events_data, status_code = PlannerService.get_planner_events(
            db_session,
            sample_planner.id
        )
        
        assert success is True
        # Verify sorted
        dates_list = [datetime.fromisoformat(e['event_date']) for e in events_data]
        assert dates_list == sorted(dates_list)


class TestPlannerServiceAcceptEvent:
    """Test suite for planner accepting events."""
    
    def test_accept_event_success(self, db_session, sample_planner, sample_event):
        """Test planner successfully accepting an event."""
        sample_event.planners.append(sample_planner)
        sample_event.set_status(2)  # pre-approval
        db_session.commit()
        
        success, message, event_data, status_code = PlannerService.accept_event(
            db_session,
            user_id=sample_planner.id,
            event_id=sample_event.id
        )
        
        assert success is True
        assert status_code == 200
        assert event_data['status_code'] == 3  # accepted
    
    def test_accept_event_wrong_status(self, db_session, sample_planner, sample_event):
        """Test planner cannot accept event not in pre-approval."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        success, message, event_data, status_code = PlannerService.accept_event(
            db_session,
            user_id=sample_planner.id,
            event_id=sample_event.id
        )
        
        assert success is False
        assert status_code == 400
    
    def test_accept_event_not_assigned(self, db_session, sample_planner, sample_event):
        """Test planner cannot accept event they're not assigned to."""
        sample_event.set_status(2)
        db_session.commit()
        
        success, message, event_data, status_code = PlannerService.accept_event(
            db_session,
            user_id=sample_planner.id,
            event_id=sample_event.id
        )
        
        assert success is False
        assert status_code == 400


class TestPlannerServiceDeclineEvent:
    """Test suite for planner declining events."""
    
    def test_decline_event_success(self, db_session, sample_planner, sample_event):
        """Test planner successfully declining an event."""
        sample_event.planners.append(sample_planner)
        sample_event.set_status(2)  # pre-approval
        db_session.commit()
        
        success, message, event_data, status_code = PlannerService.decline_event(
            db_session,
            user_id=sample_planner.id,
            event_id=sample_event.id
        )
        
        assert success is True
        assert status_code == 200
        assert event_data['status_code'] == 4  # declined
    
    def test_decline_event_removes_assignment(self, db_session, sample_planner, sample_event):
        """Test that declining removes planner from event."""
        sample_event.planners.append(sample_planner)
        sample_event.set_status(2)
        db_session.commit()
        
        PlannerService.decline_event(
            db_session,
            user_id=sample_planner.id,
            event_id=sample_event.id
        )
        
        db_session.refresh(sample_event)
        assert sample_planner not in sample_event.planners
    
    def test_decline_event_invalid_id(self, db_session, sample_planner):
        """Test declining with invalid event ID."""
        success, message, event_data, status_code = PlannerService.decline_event(
            db_session,
            user_id=sample_planner.id,
            event_id="invalid"
        )
        
        assert success is False
        assert status_code == 400
