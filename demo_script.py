"""
Demo script that creates clients, an admin, a planner, and assigns events to the planner.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.db.database import engine, Base
from src.objs.user.obj_client import CMSClientUser
from src.objs.user.obj_admin import CMSAdminUser
from src.objs.user.obj_planner import CMSEventPLanner
from src.objs.obj_event import Event

# Create tables
Base.metadata.create_all(bind=engine)

# Create a database session
db = Session(bind=engine)


def main():
    print("=== GreenBite CMS Demo ===\n")

    # Create clients
    print("Creating clients...")
    clients = []
    client_data = [
        ("John Smith", "client123", "john@example.com"),
        ("Sarah Johnson", "client456", "sarah@example.com"),
        ("Michael Brown", "client789", "michael@example.com"),
        ("Emily Davis", "emily123", "emily@example.com"),
        ("David Wilson", "david456", "david@example.com"),
        ("Jennifer Martinez", "jennifer789", "jennifer@example.com"),
        ("Robert Taylor", "robert123", "robert@example.com"),
        ("Lisa Anderson", "lisa456", "lisa@example.com"),
        ("James Thomas", "james789", "james@example.com"),
        ("Patricia Jackson", "patricia123", "patricia@example.com"),
        ("Christopher White", "chris456", "chris@example.com"),
        ("Mary Harris", "mary789", "mary@example.com"),
        ("Daniel Martin", "daniel123", "daniel@example.com"),
    ]

    for name, pwd, email in client_data:
        client = CMSClientUser(
            user_name=name, user_pswd=pwd, user_email=email, permission_lvl=0
        )
        clients.append(client)
        db.add(client)

    db.commit()
    print(f"✓ Created {len(clients)} clients\n")

    # Create an admin
    print("Creating admin...")
    admin = CMSAdminUser(
        user_name="Admin User",
        user_pswd="admin123",
        user_email="admin@example.com",
        permission_lvl=2,
    )
    db.add(admin)
    db.commit()
    print(f"✓ Created admin: {admin.user_name}\n")

    # Create planners
    print("Creating event planners...")
    planners = []
    planner_data = [
        ("Event Planner Alice", "alice123", "alice@greenbite.com"),
        ("Event Planner Bob", "bob456", "bob@greenbite.com"),
        ("Event Planner Carol", "carol789", "carol@greenbite.com"),
        ("Event Planner David", "david123", "david@greenbite.com"),
        ("Event Planner Eva", "eva456", "eva@greenbite.com"),
        ("Event Planner Frank", "frank789", "frank@greenbite.com"),
        ("Event Planner Grace", "grace123", "grace@greenbite.com"),
        ("Event Planner Henry", "henry456", "henry@greenbite.com"),
        ("Event Planner Iris", "iris789", "iris@greenbite.com"),
        ("Event Planner Jack", "jack123", "jack@greenbite.com"),
        ("Event Planner Kelly", "kelly456", "kelly@greenbite.com"),
    ]

    for name, pwd, email in planner_data:
        planner = CMSEventPLanner(
            user_name=name, user_pswd=pwd, user_email=email, permission_lvl=1
        )
        planners.append(planner)
        db.add(planner)

    db.commit()
    print(f"✓ Created {len(planners)} planners\n")

    # Create events from clients
    print("Creating events from clients...")
    events = []
    event_data = [
        (
            clients[0],
            "Annual Corporate Lunch",
            "Downtown Venue",
            "Corporate lunch event",
            500.0,
            30,
        ),
        (
            clients[1],
            "Sarah & Tom's Wedding",
            "Garden Hall",
            "Wedding reception",
            2000.0,
            45,
        ),
        (
            clients[2],
            "Michael's 30th Birthday Bash",
            "Community Center",
            "Birthday party",
            300.0,
            60,
        ),
        (
            clients[3],
            "Tech Conference 2026",
            "Convention Center",
            "Annual tech summit",
            1500.0,
            75,
        ),
        (
            clients[4],
            "Charity Gala Dinner",
            "Elegant Ballroom",
            "Fundraiser event",
            3000.0,
            90,
        ),
        (
            clients[5],
            "Product Launch Party",
            "Modern Gallery",
            "New product reveal",
            2500.0,
            35,
        ),
        (
            clients[6],
            "Family Reunion Picnic",
            "Riverside Park",
            "Extended family gathering",
            800.0,
            120,
        ),
        (
            clients[7],
            "Corporate Team Building",
            "Adventure Zone",
            "Outdoor team activities",
            1200.0,
            55,
        ),
        (
            clients[8],
            "Art Exhibition Opening",
            "Fine Arts Museum",
            "Contemporary art showcase",
            1000.0,
            20,
        ),
        (
            clients[9],
            "Anniversary Celebration",
            "Rooftop Restaurant",
            "Golden wedding anniversary",
            1500.0,
            40,
        ),
        (
            clients[10],
            "Graduation Party",
            "Beach Resort",
            "Celebratory graduation event",
            2200.0,
            65,
        ),
        (
            clients[11],
            "Holiday Festival",
            "Town Square",
            "Season celebration with festivities",
            5000.0,
            10,
        ),
        (
            clients[12],
            "Networking Breakfast",
            "Business Club",
            "Professional networking event",
            600.0,
            50,
        ),
    ]

    for client, title, location, notes, price, days in event_data:
        event = client.request_event(
            db,
            event_date=datetime.utcnow() + timedelta(days=days),
            title=title,
            location=location,
            notes=notes,
            price_total=price,
        )
        events.append(event)

    print(f"✓ Created {len(events)} events\n")

    # Assign events to planners using admin
    print("Assigning events to planners (via admin)...")
    for i, event in enumerate(events):
        planner = planners[i % len(planners)]
        admin.assign_planner_to_event(db, event.id, planner.id)
    print(f"✓ Assigned all {len(events)} events to planners\n")

    # Display planner's assigned events
    print("Events assigned to each planner:")
    for planner in planners:
        planner.get_assigned_events_list(db)

    db.close()


if __name__ == "__main__":
    main()
