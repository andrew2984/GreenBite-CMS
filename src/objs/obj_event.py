from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from rich.table import Table
from rich.console import Console
from ..db.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"))
    event_date = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)  # initialised
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(String, nullable=True)
    location = Column(String, nullable=True)
    price_total = Column(Float, default=0.0)
    payment_confirmed = Column(Boolean, default=False)

    user = relationship("CMSClientUser", back_populates="event")

    __status_lookup = [
        "uninitialised",
        "initialised",
        "pre-approval",
        "accepted",
        "declined",
        "awaiting client",
        "awaiting review",
        "payment pending",
        "confirmed",
        "completed",
        "cancelled"
    ]

    def __init__(self, client_name, client_email, client_id, event_date,
                 location=None, notes=None, price_total=0.0):
        self.client_name = client_name
        self.client_email = client_email
        self.client_id = client_id
        self.event_date = event_date
        self.location = location
        self.notes = notes
        self.price_total = price_total
        self.status = 1
        self.payment_confirmed = False

    def get_status(self, verbose=False):
        return self.__status_lookup[self.status] if verbose else self.status

    def set_status(self, new_status):
        if 0 <= new_status < len(self.__status_lookup):
            self.status = new_status
        else:
            raise ValueError(f"Invalid status {new_status}")

    def mark_payment_confirmed(self):
        self.payment_confirmed = True
        if self.status == 7:  # payment pending
            self.set_status(8)  # confirmed

    @classmethod
    def get_by_id(cls, db, event_id):
        return db.query(cls).filter(cls.id == event_id).first()

    @classmethod
    def get_upcoming_events(cls, db):
        return db.query(cls).filter(cls.event_date > datetime.utcnow()).all()

    @classmethod
    def get_events_for_client(cls, db, client_email):
        return db.query(cls).filter(cls.client_email == client_email).all()

    @staticmethod
    def print_events_table(events):
        table = Table(title="[bold cyan]Events[/bold cyan]")
        table.add_column("ID", style="cyan")
        table.add_column("Client", style="cyan")
        table.add_column("Email", style="cyan")
        table.add_column("Event Date", style="cyan")
        table.add_column("Location", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Price", style="cyan")
        table.add_column("Payment", style="cyan")
        
        for event in events:
            table.add_row(
                str(event.id),
                event.client_name,
                event.client_email,
                str(event.event_date),
                event.location or "N/A",
                event.get_status(verbose=True),
                f"£{event.price_total:.2f}",
                "✓" if event.payment_confirmed else "✗"
            )
        
        console = Console()
        console.print(table)

    def __repr__(self):
        self.print_events_table([self])
        # return f"<Event(id={self.id}, client_name={self.client_name}, client_email={self.client_email}, client_id={self.client_id}, event_date={self.event_date}, status={self.get_status(True)}, location={self.location}, notes={self.notes}, price_total={self.price_total}, payment_confirmed={self.payment_confirmed}, created_at={self.created_at}, updated_at={self.updated_at})>"
