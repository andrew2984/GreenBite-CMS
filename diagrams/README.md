# GreenBite CMS - C4 PlantUML Diagrams

This directory contains C4 model diagrams for the GreenBite CMS architecture using PlantUML.

## Diagram Files

### 1. System Context Diagram
**File:** `c4-system-context.puml`

Shows the big picture of the GreenBite CMS system, including:
- User types (Client, Employee, Driver, Planner, Admin)
- The GreenBite CMS system as a single box
- External systems (Maps API, Payment Gateway, Notification Service, Cloud Storage)
- High-level relationships between users and systems

### 2. Container Diagram
**File:** `c4-container.puml`

Zooms into the GreenBite CMS system boundary, showing:
- Web Application and Mobile App (client containers)
- API Gateway
- Authentication Service
- Microservices (Booking, Inventory, Scheduling, Finance, Delivery, Communication)
- Data stores (PostgreSQL Database, Redis Cache, Message Queue, Audit Storage)
- Relationships and communication protocols between containers

### 3. Component Diagram - Booking Service
**File:** `c4-component-booking.puml`

Focuses on the Booking Service container, showing:
- Booking Controller (HTTP request handler)
- Validation Pipeline (multi-stage validation)
- Event Manager (CRUD operations)
- Client Communications
- Planner Assignment logic
- Booking Repository (data access layer)
- Interactions with other services and database

### 4. Deployment Diagram (AWS)
**File:** `c4-deployment.puml`

Shows the physical deployment architecture on AWS:
- User devices (desktop, mobile)
- AWS infrastructure (Route 53, CloudFront, VPC, subnets)
- Application Load Balancer
- ECS cluster with containerized services
- RDS PostgreSQL (Multi-AZ with read replica)
- ElastiCache Redis
- S3 for file storage
- SQS for message queueing
- External third-party services
- Network relationships and protocols

## How to Render These Diagrams

### Online Rendering
1. Visit [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
2. Copy the contents of any `.puml` file
3. Paste into the text box
4. Click "Submit" to generate the diagram

### VS Code Extension
1. Install the **PlantUML** extension by jebbs
2. Open any `.puml` file
3. Press `Alt+D` to preview the diagram
4. Right-click and select "Export Current Diagram" to save as PNG/SVG

### Command Line (Local)
```bash
# Install PlantUML (requires Java)
# Download plantuml.jar from https://plantuml.com/download

# Generate PNG
java -jar plantuml.jar c4-system-context.puml

# Generate SVG
java -jar plantuml.jar -tsvg c4-system-context.puml

# Generate all diagrams
java -jar plantuml.jar *.puml
```

### Docker
```bash
# Pull PlantUML Docker image
docker pull plantuml/plantuml

# Generate diagrams
docker run --rm -v ${PWD}:/data plantuml/plantuml -tpng /data/*.puml
```

## C4 Model Levels

The C4 model provides a hierarchical approach to visualizing software architecture:

| Level | Abstraction | Audience | Diagram File |
|-------|-------------|----------|--------------|
| **Level 1: System Context** | Highest - Shows the system in its environment | Non-technical stakeholders | `c4-system-context.puml` |
| **Level 2: Container** | High - Shows major components/services | Technical stakeholders, architects | `c4-container.puml` |
| **Level 3: Component** | Medium - Shows components within containers | Developers, architects | `c4-component-booking.puml` |
| **Level 4: Code** | Low - Shows class/code structure | Developers | *(Not included - code level)* |

## Additional Diagram: Deployment

The deployment diagram shows the runtime infrastructure and is complementary to the C4 model levels.

## Notes

- All diagrams use the official C4-PlantUML library
- Diagrams follow the C4 model conventions (colors, shapes, stereotypes)
- The container diagram shows the **thin-client architecture** with all business logic server-side
- The deployment diagram specifically shows **AWS deployment**, but Azure/local deployments follow similar patterns (see SYSTEM_ARCHITECTURE.md)
- GDPR compliance components are highlighted (Audit Log Storage, encryption, access control)

## Customization

To modify these diagrams:

1. Edit the `.puml` files with any text editor
2. Follow PlantUML C4 syntax: [C4-PlantUML Documentation](https://github.com/plantuml-stdlib/C4-PlantUML)
3. Test rendering before committing changes

## References

- [C4 Model](https://c4model.com/)
- [PlantUML](https://plantuml.com/)
- [C4-PlantUML GitHub](https://github.com/plantuml-stdlib/C4-PlantUML)
- [System Architecture Document](../SYSTEM_ARCHITECTURE.md)
