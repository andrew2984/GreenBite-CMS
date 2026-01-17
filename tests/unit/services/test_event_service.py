"""
Unit tests for EventService
"""
import pytest
from datetime import datetime, timedelta
from src.services.event_service import EventService
from src.objs.obj_event import Event


class TestEventServiceGetClientEvents:
    """Test suite for getting client events."""
    
    def test_get_client_events_success(self, db_session, sample_client, sample_event):
        """Test successfully getting client events."""
        success, message, events_data, status_code = EventService.get_client_events(
            db_session,
            sample_client.id
        )
        
        assert success is True
        assert status_code == 200
        assert isinstance(events_data, list)
        assert len(events_data) >= 1
    
    def test_get_client_events_empty(self, db_session, sample_client):
        """Test getting events when client has none."""
        # Delete any existing events
        db_session.query(Event).filter_by(client_id=sample_client.id).delete()
        db_session.commit()
        
        success, message, events_data, status_code = EventService.get_client_events(
            db_session,
            sample_client.id
        )
        
        assert success is True
        assert len(events_data) == 0
    
    def test_get_client_events_multiple(self, db_session, sample_client):
        """Test getting multiple events for client."""
        # Create multiple events
        for i in range(3):
            event = Event(
                client_name=sample_client.user_name,
                client_email=sample_client.user_email,
                client_id=sample_client.id,
                event_date=datetime.utcnow() + timedelta(days=i+1),
                title=f"Event {i+1}"
            )
            db_session.add(event)
        db_session.commit()
        
        success, message, events_data, status_code = EventService.get_client_events(
            db_session,
            sample_client.id
        )
        
        assert success is True
        assert len(events_data) == 3


class TestEventServiceCreateEvent:
    """Test suite for creating events."""
    
    def test_create_event_success(self, db_session, sample_client):
        """Test successfully creating an event."""
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        success, message, event_data, status_code = EventService.create_event(
            db_session,
            user_id=sample_client.id,
            event_date_str=event_date,
            title="Test Event",
            location="Test Location",
            notes="Test notes",
            price_total=150.0
        )
        
        assert success is True
        assert status_code == 201
        assert event_data['title'] == "Test Event"
        assert event_data['location'] == "Test Location"
        assert event_data['price_total'] == 150.0
    
    def test_create_event_minimal_data(self, db_session, sample_client):
        """Test creating event with minimal data."""
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        success, message, event_data, status_code = EventService.create_event(
            db_session,
            user_id=sample_client.id,
            event_date_str=event_date
        )
        
        assert success is True
        assert status_code == 201
        assert 'id' in event_data
    
    def test_create_event_missing_date(self, db_session, sample_client):
        """Test creating event without date."""
        success, message, event_data, status_code = EventService.create_event(
            db_session,
            user_id=sample_client.id,
            event_date_str=""
        )
        
        assert success is False
        assert status_code == 400
        assert "date is required" in message.lower()
    
    def test_create_event_invalid_date_format(self, db_session, sample_client):
        """Test creating event with invalid date format."""
        success, message, event_data, status_code = EventService.create_event(
            db_session,
            user_id=sample_client.id,
            event_date_str="invalid-date"
        )
        
        assert success is False
        assert status_code == 400
        assert "date format" in message.lower()
    
    def test_create_event_negative_price(self, db_session, sample_client):
        """Test creating event with negative price."""
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        success, message, event_data, status_code = EventService.create_event(
            db_session,
            user_id=sample_client.id,
            event_date_str=event_date,
            price_total=-100.0
        )
        
        assert success is False
        assert status_code == 400
        assert "negative" in message.lower()
    
    def test_create_event_invalid_price(self, db_session, sample_client):
        """Test creating event with invalid price format."""
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        success, message, event_data, status_code = EventService.create_event(
            db_session,
            user_id=sample_client.id,
            event_date_str=event_date,
            price_total="invalid"
        )
        
        assert success is False
        assert status_code == 400
    
    def test_create_event_nonexistent_user(self, db_session):
        """Test creating event for nonexistent user."""
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        success, message, event_data, status_code = EventService.create_event(
            db_session,
            user_id=99999,
            event_date_str=event_date
        )
        
        assert success is False
        assert status_code == 404
    
    def test_create_event_sanitizes_inputs(self, db_session, sample_client):
        """Test that event creation sanitizes HTML inputs."""
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        success, message, event_data, status_code = EventService.create_event(
            db_session,
            user_id=sample_client.id,
            event_date_str=event_date,
            title="<script>alert('xss')</script>Test",
            notes="<b>Notes</b>"
        )
        
        assert success is True
        assert "<script>" not in event_data['title']
        assert "&lt;script&gt;" in event_data['title']


class TestEventServiceCancelEvent:
    """Test suite for cancelling events."""
    
    def test_cancel_event_success(self, db_session, sample_client, sample_event):
        """Test successfully cancelling an event."""
        success, message, status_code = EventService.cancel_event(
            db_session,
            user_id=sample_client.id,
            event_id=sample_event.id
        )
        
        assert success is True
        assert status_code == 200
        
        # Verify status changed
        db_session.refresh(sample_event)
        assert sample_event.status == 10  # cancelled
    
    def test_cancel_event_not_owned(self, db_session, sample_client):
        """Test cancelling event not owned by user."""
        # Create another client and event
        from src.objs.user.obj_client import CMSClientUser
        other_client = CMSClientUser(
            user_name="other_client",
            user_email="other@test.com",
            user_pswd="",
            permission_lvl=0
        )
        other_client.set_password("Password123")
        db_session.add(other_client)
        db_session.commit()
        
        other_event = Event(
            client_name=other_client.user_name,
            client_email=other_client.user_email,
            client_id=other_client.id,
            event_date=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(other_event)
        db_session.commit()
        
        success, message, status_code = EventService.cancel_event(
            db_session,
            user_id=sample_client.id,
            event_id=other_event.id
        )
        
        assert success is False
        assert status_code == 404
    
    def test_cancel_event_nonexistent(self, db_session, sample_client):
        """Test cancelling nonexistent event."""
        success, message, status_code = EventService.cancel_event(
            db_session,
            user_id=sample_client.id,
            event_id=99999
        )
        
        assert success is False
        assert status_code == 404
    
    def test_cancel_event_invalid_id(self, db_session, sample_client):
        """Test cancelling with invalid event ID."""
        success, message, status_code = EventService.cancel_event(
            db_session,
            user_id=sample_client.id,
            event_id="invalid"
        )
        
        assert success is False
        assert status_code == 400


class TestEventServiceGetEventById:
    """Test suite for getting event by ID."""
    
    def test_get_event_by_id_success(self, db_session, sample_event):
        """Test getting event by ID."""
        event = EventService.get_event_by_id(db_session, sample_event.id)
        
        assert event is not None
        assert event.id == sample_event.id
        assert event.title == sample_event.title
    
    def test_get_event_by_id_nonexistent(self, db_session):
        """Test getting nonexistent event."""
        event = EventService.get_event_by_id(db_session, 99999)
        assert event is None
