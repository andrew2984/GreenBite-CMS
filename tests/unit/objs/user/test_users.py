"""
Unit tests for User models - CMSUser, CMSClientUser, CMSEventPlanner, CMSAdminUser
"""
import pytest
from datetime import datetime, timedelta
from src.objs.user.obj_user import CMSUser
from src.objs.user.obj_client import CMSClientUser
from src.objs.user.obj_planner import CMSEventPLanner
from src.objs.user.obj_admin import CMSAdminUser
from src.objs.obj_event import Event


class TestCMSUser:
    """Test suite for base CMSUser model."""
    
    def test_user_creation(self, db_session):
        """Test basic user creation."""
        user = CMSUser(
            user_name="testuser",
            user_email="test@test.com",
            user_pswd="",
            permission_lvl=0
        )
        user.set_password("TestPassword123")
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.user_name == "testuser"
        assert user.user_email == "test@test.com"
        assert user.permission_lvl == 0
        assert user.user_pswd != "TestPassword123"  # Password should be hashed
    
    def test_set_password(self, db_session):
        """Test password hashing."""
        user = CMSUser(
            user_name="testuser",
            user_email="test@test.com",
            user_pswd="",
            permission_lvl=0
        )
        password = "MySecurePassword123"
        user.set_password(password)
        
        assert user.user_pswd != password
        assert len(user.user_pswd) > 0
    
    def test_check_password_correct(self, sample_client):
        """Test password verification with correct password."""
        assert sample_client.check_password("TestPassword123") is True
    
    def test_check_password_incorrect(self, sample_client):
        """Test password verification with incorrect password."""
        assert sample_client.check_password("WrongPassword") is False
    
    def test_login_success(self, db_session, sample_client):
        """Test successful login."""
        user = CMSUser.login(db_session, "client@test.com", "TestPassword123")
        
        assert user is not None
        assert user.user_email == "client@test.com"
    
    def test_login_wrong_password(self, db_session, sample_client):
        """Test login with wrong password."""
        user = CMSUser.login(db_session, "client@test.com", "WrongPassword")
        assert user is None
    
    def test_login_nonexistent_user(self, db_session):
        """Test login with nonexistent user."""
        user = CMSUser.login(db_session, "nonexistent@test.com", "Password123")
        assert user is None
    
    def test_email_unique_constraint(self, db_session, sample_client):
        """Test that email must be unique."""
        duplicate_user = CMSUser(
            user_name="another_user",
            user_email="client@test.com",  # Same email as sample_client
            user_pswd="",
            permission_lvl=0
        )
        duplicate_user.set_password("Password123")
        
        db_session.add(duplicate_user)
        
        with pytest.raises(Exception):  # SQLAlchemy will raise an exception
            db_session.commit()


class TestCMSClientUser:
    """Test suite for CMSClientUser model."""
    
    def test_client_creation(self, db_session):
        """Test client user creation."""
        client = CMSClientUser(
            user_name="client_test",
            user_email="client_test@test.com",
            user_pswd="",
            permission_lvl=0
        )
        client.set_password("Password123")
        
        db_session.add(client)
        db_session.commit()
        
        assert client.id is not None
        assert client.permission_lvl == 0
    
    def test_request_event(self, db_session, sample_client):
        """Test client requesting an event."""
        event_date = datetime.utcnow() + timedelta(days=30)
        event = sample_client.request_event(
            db_session,
            event_date=event_date,
            title="Test Event",
            location="Test Location",
            notes="Test notes",
            price_total=150.0
        )
        
        assert event.id is not None
        assert event.client_id == sample_client.id
        assert event.title == "Test Event"
        assert event.status == 1  # initialised
    
    def test_cancel_event(self, db_session, sample_client, sample_event):
        """Test client cancelling their own event."""
        result = sample_client.cancel_event(db_session, sample_event.id)
        
        assert result is True
        assert sample_event.status == 10  # cancelled
    
    def test_cancel_event_not_owned(self, db_session, sample_client):
        """Test client cannot cancel event they don't own."""
        # Create another client
        other_client = CMSClientUser(
            user_name="other_client",
            user_email="other@test.com",
            user_pswd="",
            permission_lvl=0
        )
        other_client.set_password("Password123")
        db_session.add(other_client)
        db_session.commit()
        
        # Create event for other client
        event = Event(
            client_name=other_client.user_name,
            client_email=other_client.user_email,
            client_id=other_client.id,
            event_date=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(event)
        db_session.commit()
        
        # Try to cancel with wrong client
        result = sample_client.cancel_event(db_session, event.id)
        assert result is False
    
    def test_check_event_status(self, db_session, sample_client, sample_event):
        """Test checking event status."""
        status = sample_client.check_event_status(db_session, sample_event.id)
        
        assert status == "initialised"
    
    def test_check_event_status_not_owned(self, db_session, sample_client):
        """Test checking status of event not owned."""
        status = sample_client.check_event_status(db_session, 99999)
        assert status is None
    
    def test_pay_for_event(self, db_session, sample_client, sample_event):
        """Test paying for event in payment pending status."""
        sample_event.set_status(7)  # payment pending
        db_session.commit()
        
        result = sample_client.pay_for_event(db_session, sample_event.id)
        
        assert result is True
        assert sample_event.payment_confirmed is True
        assert sample_event.status == 8  # confirmed
    
    def test_pay_for_event_wrong_status(self, db_session, sample_client, sample_event):
        """Test paying for event not in payment pending status."""
        result = sample_client.pay_for_event(db_session, sample_event.id)
        
        assert result is False


class TestCMSEventPlanner:
    """Test suite for CMSEventPlanner model."""
    
    def test_planner_creation(self, db_session):
        """Test planner user creation."""
        planner = CMSEventPLanner(
            user_name="planner_test",
            user_email="planner_test@test.com",
            user_pswd="",
            permission_lvl=1
        )
        planner.set_password("Password123")
        
        db_session.add(planner)
        db_session.commit()
        
        assert planner.id is not None
        assert planner.permission_lvl == 1
    
    def test_get_assigned_events(self, db_session, sample_planner, sample_event):
        """Test getting planner's assigned events."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        events = sample_planner.get_assigned_events(db_session)
        
        assert len(events) == 1
        assert events[0].id == sample_event.id
    
    def test_accept_event(self, db_session, sample_planner, sample_event):
        """Test planner accepting an event."""
        sample_event.planners.append(sample_planner)
        sample_event.set_status(2)  # pre-approval
        db_session.commit()
        
        result = sample_planner.accept_event(db_session, sample_event.id)
        
        assert result is True
        assert sample_event.status == 3  # accepted
    
    def test_accept_event_wrong_status(self, db_session, sample_planner, sample_event):
        """Test planner cannot accept event not in pre-approval."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        result = sample_planner.accept_event(db_session, sample_event.id)
        
        assert result is False
    
    def test_accept_event_not_assigned(self, db_session, sample_planner, sample_event):
        """Test planner cannot accept event they're not assigned to."""
        sample_event.set_status(2)  # pre-approval
        db_session.commit()
        
        result = sample_planner.accept_event(db_session, sample_event.id)
        
        assert result is False
    
    def test_decline_event(self, db_session, sample_planner, sample_event):
        """Test planner declining an event."""
        sample_event.planners.append(sample_planner)
        sample_event.set_status(2)  # pre-approval
        db_session.commit()
        
        result = sample_planner.decline_event(db_session, sample_event.id)
        
        assert result is True
        assert sample_event.status == 4  # declined
        assert sample_planner not in sample_event.planners
    
    def test_decline_event_wrong_status(self, db_session, sample_planner, sample_event):
        """Test planner cannot decline event not in pre-approval."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        result = sample_planner.decline_event(db_session, sample_event.id)
        
        assert result is False


class TestCMSAdminUser:
    """Test suite for CMSAdminUser model."""
    
    def test_admin_creation(self, db_session):
        """Test admin user creation."""
        admin = CMSAdminUser(
            user_name="admin_test",
            user_email="admin_test@test.com",
            user_pswd="",
            permission_lvl=2
        )
        admin.set_password("Password123")
        
        db_session.add(admin)
        db_session.commit()
        
        assert admin.id is not None
        assert admin.permission_lvl == 2
    
    def test_assign_planner_to_event(self, db_session, sample_admin, sample_planner, sample_event):
        """Test admin assigning planner to event."""
        result = sample_admin.assign_planner_to_event(
            db_session,
            sample_event.id,
            sample_planner.id
        )
        
        assert result is True
        assert sample_planner in sample_event.planners
        assert sample_event.status == 2  # pre-approval
    
    def test_assign_planner_already_assigned(self, db_session, sample_admin, sample_planner, sample_event):
        """Test assigning planner already assigned to event."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        result = sample_admin.assign_planner_to_event(
            db_session,
            sample_event.id,
            sample_planner.id
        )
        
        assert result is False
    
    def test_assign_planner_insufficient_permission(self, db_session, sample_client, sample_planner, sample_event):
        """Test non-admin cannot assign planners."""
        with pytest.raises(PermissionError):
            sample_client.assign_planner_to_event(
                db_session,
                sample_event.id,
                sample_planner.id
            )
    
    def test_remove_planner_from_event(self, db_session, sample_admin, sample_planner, sample_event):
        """Test admin removing planner from event."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        result = sample_admin.remove_planner_from_event(
            db_session,
            sample_event.id,
            sample_planner.id
        )
        
        assert result is True
        assert sample_planner not in sample_event.planners
    
    def test_remove_planner_not_assigned(self, db_session, sample_admin, sample_planner, sample_event):
        """Test removing planner not assigned to event."""
        result = sample_admin.remove_planner_from_event(
            db_session,
            sample_event.id,
            sample_planner.id
        )
        
        assert result is False
    
    def test_get_event_planners(self, db_session, sample_admin, sample_planner, sample_event):
        """Test getting planners for an event."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        planners = sample_admin.get_event_planners(db_session, sample_event.id)
        
        assert len(planners) == 1
        assert planners[0].id == sample_planner.id
    
    def test_get_planner_events(self, db_session, sample_admin, sample_planner, sample_event):
        """Test getting events for a planner."""
        sample_event.planners.append(sample_planner)
        db_session.commit()
        
        events = sample_admin.get_planner_events(db_session, sample_planner.id)
        
        assert len(events) == 1
        assert events[0].id == sample_event.id
