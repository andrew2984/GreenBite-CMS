"""
Unit tests for Event model
"""
import pytest
from datetime import datetime, timedelta
from src.objs.obj_event import Event


class TestEventModel:
    """Test suite for Event model."""
    
    def test_event_creation(self, db_session, sample_client):
        """Test basic event creation."""
        event_date = datetime.utcnow() + timedelta(days=30)
        event = Event(
            client_name=sample_client.user_name,
            client_email=sample_client.user_email,
            client_id=sample_client.id,
            event_date=event_date,
            title="Test Event",
            location="Test Location",
            notes="Test notes",
            price_total=100.0
        )
        
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        assert event.id is not None
        assert event.client_name == sample_client.user_name
        assert event.client_email == sample_client.user_email
        assert event.title == "Test Event"
        assert event.status == 1  # initialised
        assert event.payment_confirmed is False
    
    def test_event_default_values(self, db_session, sample_client):
        """Test event creation with default values."""
        event_date = datetime.utcnow() + timedelta(days=30)
        event = Event(
            client_name=sample_client.user_name,
            client_email=sample_client.user_email,
            client_id=sample_client.id,
            event_date=event_date
        )
        
        db_session.add(event)
        db_session.commit()
        
        assert event.title is None
        assert event.location is None
        assert event.notes is None
        assert event.price_total == 0.0
        assert event.status == 1
        assert event.payment_confirmed is False
    
    def test_get_status_verbose(self, sample_event):
        """Test getting event status in verbose mode."""
        assert sample_event.get_status(verbose=True) == "initialised"
        
        sample_event.set_status(3)
        assert sample_event.get_status(verbose=True) == "accepted"
    
    def test_get_status_numeric(self, sample_event):
        """Test getting event status as numeric."""
        assert sample_event.get_status(verbose=False) == 1
        
        sample_event.set_status(3)
        assert sample_event.get_status(verbose=False) == 3
    
    def test_set_status_valid(self, sample_event):
        """Test setting valid event status."""
        sample_event.set_status(2)  # pre-approval
        assert sample_event.status == 2
        
        sample_event.set_status(3)  # accepted
        assert sample_event.status == 3
    
    def test_set_status_invalid(self, sample_event):
        """Test setting invalid event status."""
        with pytest.raises(ValueError):
            sample_event.set_status(99)
        
        with pytest.raises(ValueError):
            sample_event.set_status(-1)
    
    def test_mark_payment_confirmed(self, sample_event, db_session):
        """Test marking payment as confirmed."""
        sample_event.set_status(7)  # payment pending
        sample_event.mark_payment_confirmed()
        
        assert sample_event.payment_confirmed is True
        assert sample_event.status == 8  # confirmed
    
    def test_mark_payment_confirmed_wrong_status(self, sample_event):
        """Test marking payment confirmed when not in payment pending status."""
        initial_status = sample_event.status
        sample_event.mark_payment_confirmed()
        
        assert sample_event.payment_confirmed is True
        assert sample_event.status == initial_status  # Status shouldn't change
    
    def test_get_by_id(self, db_session, sample_event):
        """Test getting event by ID."""
        retrieved_event = Event.get_by_id(db_session, sample_event.id)
        
        assert retrieved_event is not None
        assert retrieved_event.id == sample_event.id
        assert retrieved_event.title == sample_event.title
    
    def test_get_by_id_nonexistent(self, db_session):
        """Test getting event by nonexistent ID."""
        retrieved_event = Event.get_by_id(db_session, 99999)
        assert retrieved_event is None
    
    def test_get_upcoming_events(self, db_session, sample_client):
        """Test getting upcoming events."""
        # Create past event
        past_event = Event(
            client_name=sample_client.user_name,
            client_email=sample_client.user_email,
            client_id=sample_client.id,
            event_date=datetime.utcnow() - timedelta(days=1),
            title="Past Event"
        )
        db_session.add(past_event)
        
        # Create future event
        future_event = Event(
            client_name=sample_client.user_name,
            client_email=sample_client.user_email,
            client_id=sample_client.id,
            event_date=datetime.utcnow() + timedelta(days=30),
            title="Future Event"
        )
        db_session.add(future_event)
        db_session.commit()
        
        upcoming = Event.get_upcoming_events(db_session)
        
        assert len(upcoming) >= 1
        assert all(e.event_date > datetime.utcnow() for e in upcoming)
    
    def test_get_events_for_client(self, db_session, sample_client):
        """Test getting events for specific client."""
        # Create multiple events for the client
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
        
        events = Event.get_events_for_client(db_session, sample_client.user_email)
        
        assert len(events) == 3
        assert all(e.client_email == sample_client.user_email for e in events)
    
    def test_event_timestamps(self, db_session, sample_event):
        """Test that timestamps are set correctly."""
        assert sample_event.created_at is not None
        assert sample_event.updated_at is not None
        assert isinstance(sample_event.created_at, datetime)
        assert isinstance(sample_event.updated_at, datetime)


class TestEventStatusTransitions:
    """Test suite for event status transitions."""
    
    def test_status_progression(self, sample_event):
        """Test typical status progression."""
        # Initial state
        assert sample_event.status == 1  # initialised
        
        # Pre-approval
        sample_event.set_status(2)
        assert sample_event.status == 2
        
        # Accepted
        sample_event.set_status(3)
        assert sample_event.status == 3
        
        # Payment pending
        sample_event.set_status(7)
        assert sample_event.status == 7
        
        # Confirmed
        sample_event.set_status(8)
        assert sample_event.status == 8
        
        # Completed
        sample_event.set_status(9)
        assert sample_event.status == 9
    
    def test_declined_status(self, sample_event):
        """Test declined status."""
        sample_event.set_status(2)  # pre-approval
        sample_event.set_status(4)  # declined
        assert sample_event.status == 4
    
    def test_cancelled_status(self, sample_event):
        """Test cancelled status."""
        sample_event.set_status(10)  # cancelled
        assert sample_event.status == 10
