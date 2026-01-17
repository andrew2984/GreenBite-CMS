"""
Integration tests for complete event workflow
Tests the interaction between services, models, and database
"""
import pytest
from datetime import datetime, timedelta
from src.services.auth_service import AuthService
from src.services.event_service import EventService
from src.services.admin_service import AdminService
from src.services.planner_service import PlannerService
from src.objs.obj_event import Event


class TestEventLifecycleIntegration:
    """Test complete event lifecycle from creation to completion."""
    
    def test_complete_event_workflow(self, db_session):
        """Test complete workflow: register users, create event, assign planner, accept, complete."""
        # Step 1: Register client
        success, _, client_data, _ = AuthService.register_user(
            db_session,
            username="integrationclient",
            email="integration@client.com",
            password="TestPassword123",
            role="client"
        )
        assert success is True
        client_id = client_data['user']['id']
        
        # Step 2: Register planner
        success, _, planner_data, _ = AuthService.register_user(
            db_session,
            username="integrationplanner",
            email="integration@planner.com",
            password="TestPassword123",
            role="planner"
        )
        assert success is True
        planner_id = planner_data['user']['id']
        
        # Step 3: Register admin
        success, _, admin_data, _ = AuthService.register_user(
            db_session,
            username="integrationadmin",
            email="integration@admin.com",
            password="TestPassword123",
            role="admin"
        )
        assert success is True
        admin_id = admin_data['user']['id']
        
        # Step 4: Client creates event
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        success, _, event_data, _ = EventService.create_event(
            db_session,
            user_id=client_id,
            event_date_str=event_date,
            title="Integration Test Event",
            location="Test Location",
            price_total=200.0
        )
        assert success is True
        event_id = event_data['id']
        
        # Verify event is in initialised state
        event = Event.get_by_id(db_session, event_id)
        assert event.status == 1  # initialised
        
        # Step 5: Admin assigns planner to event
        success, _, event_data, _ = AdminService.assign_planner_to_event(
            db_session,
            admin_id=admin_id,
            event_id=event_id,
            planner_id=planner_id
        )
        assert success is True
        
        # Verify event is now in pre-approval state
        event = Event.get_by_id(db_session, event_id)
        assert event.status == 2  # pre-approval
        assert len(event.planners) == 1
        
        # Step 6: Planner accepts event
        success, _, event_data, _ = PlannerService.accept_event(
            db_session,
            user_id=planner_id,
            event_id=event_id
        )
        assert success is True
        
        # Verify event is now accepted
        event = Event.get_by_id(db_session, event_id)
        assert event.status == 3  # accepted
        
        # Step 7: Admin moves to payment pending
        event.set_status(7)  # payment pending
        db_session.commit()
        
        # Step 8: Client pays for event
        from src.objs.user.obj_client import CMSClientUser
        client = db_session.query(CMSClientUser).filter_by(id=client_id).first()
        result = client.pay_for_event(db_session, event_id)
        assert result is True
        
        # Verify event is confirmed
        event = Event.get_by_id(db_session, event_id)
        assert event.status == 8  # confirmed
        assert event.payment_confirmed is True
        
        # Step 9: Mark as completed
        event.set_status(9)  # completed
        db_session.commit()
        
        assert event.status == 9
    
    def test_event_decline_workflow(self, db_session):
        """Test workflow when planner declines event."""
        # Register users
        success, _, client_data, _ = AuthService.register_user(
            db_session, "client2", "client2@test.com", "TestPassword123", "client"
        )
        client_id = client_data['user']['id']
        
        success, _, planner_data, _ = AuthService.register_user(
            db_session, "planner2", "planner2@test.com", "TestPassword123", "planner"
        )
        planner_id = planner_data['user']['id']
        
        success, _, admin_data, _ = AuthService.register_user(
            db_session, "admin2", "admin2@test.com", "TestPassword123", "admin"
        )
        admin_id = admin_data['user']['id']
        
        # Create event
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        success, _, event_data, _ = EventService.create_event(
            db_session, client_id, event_date, title="Decline Test Event"
        )
        event_id = event_data['id']
        
        # Admin assigns planner
        AdminService.assign_planner_to_event(
            db_session, admin_id, event_id, planner_id
        )
        
        # Planner declines
        success, _, event_data, _ = PlannerService.decline_event(
            db_session, planner_id, event_id
        )
        assert success is True
        
        # Verify event is declined and planner removed
        event = Event.get_by_id(db_session, event_id)
        assert event.status == 4  # declined
        assert len(event.planners) == 0
    
    def test_event_cancellation_workflow(self, db_session):
        """Test workflow when client cancels event."""
        # Register client
        success, _, client_data, _ = AuthService.register_user(
            db_session, "client3", "client3@test.com", "TestPassword123", "client"
        )
        client_id = client_data['user']['id']
        
        # Create event
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        success, _, event_data, _ = EventService.create_event(
            db_session, client_id, event_date, title="Cancel Test Event"
        )
        event_id = event_data['id']
        
        # Client cancels event
        success, _, _ = EventService.cancel_event(
            db_session, client_id, event_id
        )
        assert success is True
        
        # Verify event is cancelled
        event = Event.get_by_id(db_session, event_id)
        assert event.status == 10  # cancelled


class TestMultiPlannerIntegration:
    """Test scenarios with multiple planners."""
    
    def test_assign_multiple_planners_to_event(self, db_session):
        """Test assigning multiple planners to same event."""
        # Register users
        success, _, client_data, _ = AuthService.register_user(
            db_session, "multiclient", "multi@client.com", "TestPassword123", "client"
        )
        client_id = client_data['user']['id']
        
        success, _, admin_data, _ = AuthService.register_user(
            db_session, "multiadmin", "multi@admin.com", "TestPassword123", "admin"
        )
        admin_id = admin_data['user']['id']
        
        # Register multiple planners
        planner_ids = []
        for i in range(3):
            success, _, planner_data, _ = AuthService.register_user(
                db_session,
                f"multiplanner{i}",
                f"multi{i}@planner.com",
                "TestPassword123",
                "planner"
            )
            planner_ids.append(planner_data['user']['id'])
        
        # Create event
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        success, _, event_data, _ = EventService.create_event(
            db_session, client_id, event_date, title="Multi Planner Event"
        )
        event_id = event_data['id']
        
        # Assign all planners
        success, _, event_data, _ = AdminService.assign_multiple_planners(
            db_session, admin_id, event_id, planner_ids
        )
        assert success is True
        assert event_data['assigned_count'] == 3
        
        # Verify all planners are assigned
        event = Event.get_by_id(db_session, event_id)
        assert len(event.planners) == 3
    
    def test_replace_planner_assignment(self, db_session):
        """Test replacing planner assignment."""
        # Register users
        success, _, client_data, _ = AuthService.register_user(
            db_session, "replaceclient", "replace@client.com", "TestPassword123", "client"
        )
        client_id = client_data['user']['id']
        
        success, _, admin_data, _ = AuthService.register_user(
            db_session, "replaceadmin", "replace@admin.com", "TestPassword123", "admin"
        )
        admin_id = admin_data['user']['id']
        
        success, _, planner1_data, _ = AuthService.register_user(
            db_session, "planner1", "planner1@test.com", "TestPassword123", "planner"
        )
        planner1_id = planner1_data['user']['id']
        
        success, _, planner2_data, _ = AuthService.register_user(
            db_session, "planner2", "planner2@test.com", "TestPassword123", "planner"
        )
        planner2_id = planner2_data['user']['id']
        
        # Create event
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        success, _, event_data, _ = EventService.create_event(
            db_session, client_id, event_date, title="Replace Planner Event"
        )
        event_id = event_data['id']
        
        # Assign first planner
        AdminService.assign_planner_to_event(
            db_session, admin_id, event_id, planner1_id
        )
        
        # Replace with second planner
        AdminService.assign_multiple_planners(
            db_session, admin_id, event_id, [planner2_id]
        )
        
        # Verify only second planner is assigned
        event = Event.get_by_id(db_session, event_id)
        assert len(event.planners) == 1
        assert event.planners[0].id == planner2_id


class TestAuthenticationIntegration:
    """Test authentication flow integration."""
    
    def test_register_and_login_workflow(self, db_session):
        """Test registering and then logging in."""
        # Register
        success, _, register_data, _ = AuthService.register_user(
            db_session,
            username="authtest",
            email="auth@test.com",
            password="TestPassword123",
            role="client"
        )
        assert success is True
        register_token = register_data['token']
        
        # Login
        success, _, login_data, _ = AuthService.login_user(
            db_session,
            email="auth@test.com",
            password="TestPassword123",
            ip_address="127.0.0.1"
        )
        assert success is True
        login_token = login_data['token']
        
        # Both tokens should be valid (though different)
        assert register_token != login_token
        assert len(register_token) > 0
        assert len(login_token) > 0
    
    def test_wrong_password_after_registration(self, db_session):
        """Test that wrong password fails after registration."""
        # Register
        AuthService.register_user(
            db_session, "wrongpwd", "wrongpwd@test.com", "CorrectPassword123", "client"
        )
        
        # Try to login with wrong password
        success, _, _, status_code = AuthService.login_user(
            db_session, "wrongpwd@test.com", "WrongPassword123", "127.0.0.1"
        )
        assert success is False
        assert status_code == 401


class TestDataConsistencyIntegration:
    """Test data consistency across operations."""
    
    def test_event_count_consistency(self, db_session):
        """Test that event counts remain consistent."""
        # Register client
        success, _, client_data, _ = AuthService.register_user(
            db_session, "countclient", "count@client.com", "TestPassword123", "client"
        )
        client_id = client_data['user']['id']
        
        # Create multiple events
        event_ids = []
        for i in range(5):
            event_date = (datetime.utcnow() + timedelta(days=i+1)).isoformat()
            success, _, event_data, _ = EventService.create_event(
                db_session, client_id, event_date, title=f"Event {i}"
            )
            event_ids.append(event_data['id'])
        
        # Get client events
        success, _, events_data, _ = EventService.get_client_events(
            db_session, client_id
        )
        assert len(events_data) == 5
        
        # Cancel one event
        EventService.cancel_event(db_session, client_id, event_ids[0])
        
        # Count should still be 5 (cancelled events are still listed)
        success, _, events_data, _ = EventService.get_client_events(
            db_session, client_id
        )
        assert len(events_data) == 5
        
        # Verify one is cancelled
        cancelled_count = sum(1 for e in events_data if e['status_code'] == 10)
        assert cancelled_count == 1
