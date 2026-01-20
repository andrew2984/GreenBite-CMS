# GreenBite CMS - System Architecture Document

## 1. Executive Summary

The GreenBite Content Management System (CMS) is a comprehensive, cloud-native web application designed to manage catering business operations end-to-end. Built as a thin-client architecture, the system provides centralized data management with GDPR-compliant storage, enabling seamless coordination between clients, employees, and management across booking, inventory, scheduling, finance, delivery, and internal communications modules.

---

## 2. High-Level System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        GREENBITE CMS - SYSTEM ARCHITECTURE                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              CLIENT LAYER (Thin Client)                                      │
├───────────────────────┬───────────────────────┬───────────────────────┬─────────────────────────────────────┤
│    Web Browser        │    Mobile Browser     │    Driver Mobile App  │         Admin Dashboard             │
│    (Desktop)          │    (Responsive)       │    (PWA/Native)       │         (Management)                │
│  ┌─────────────────┐  │  ┌─────────────────┐  │  ┌─────────────────┐  │  ┌─────────────────────────────┐    │
│  │ Client Portal   │  │  │ Employee Portal │  │  │ GPS Tracking    │  │  │ Analytics & Reporting       │    │
│  │ - Booking       │  │  │ - Schedule View │  │  │ Route Navigation│  │  │ User Management             │    │
│  │ - Event View    │  │  │ - Event Access  │  │  │ Delivery Status │  │  │ System Configuration        │    │
│  │ - Invoices      │  │  │ - Comms Hub     │  │  │ Event Details   │  │  │ Audit Trail Viewer          │    │
│  └─────────────────┘  │  └─────────────────┘  │  └─────────────────┘  │  └─────────────────────────────┘    │
└───────────────────────┴───────────────────────┴───────────────────────┴─────────────────────────────────────┘
                                                        │
                                                        │ HTTPS/TLS 1.3
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              API GATEWAY / LOAD BALANCER                                     │
│                                    (AWS API Gateway / Azure API Management)                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐    │
│  │  • Rate Limiting  • Request Validation  • SSL Termination  • Request Routing  • API Versioning     │    │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         AUTHENTICATION & AUTHORIZATION LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                                     Auth Service (OAuth 2.0 / JWT)                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐     │    │
│  │  │ User Auth    │  │ Role-Based   │  │ Session      │  │ MFA Support  │  │ Audit Logging      │     │    │
│  │  │ (Login/SSO)  │  │ Access Ctrl  │  │ Management   │  │ (Optional)   │  │ (GDPR Compliance)  │     │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                                              │
│  User Roles: CLIENT | EMPLOYEE | DRIVER | PLANNER | ADMIN                                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           APPLICATION LAYER (Microservices)                                  │
├─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┤
│  BOOKING SERVICE    │  INVENTORY SERVICE  │  SCHEDULING SERVICE │  FINANCE SERVICE    │  DELIVERY SERVICE   │
│  ┌───────────────┐  │  ┌───────────────┐  │  ┌───────────────┐  │  ┌───────────────┐  │  ┌───────────────┐  │
│  │ Event CRUD    │  │  │ Stock Mgmt    │  │  │ Employee      │  │  │ Invoice Gen   │  │  │ Route Optim   │  │
│  │ Validation    │  │  │ Categories    │  │  │ Schedules     │  │  │ Payment       │  │  │ GPS Tracking  │  │
│  │ Pipeline      │  │  │ Usage Track   │  │  │ Shift Mgmt    │  │  │ Tickets       │  │  │ Driver Assign │  │
│  │ Client Comms  │  │  │ Thresholds    │  │  │ Availability  │  │  │ Audit Trail   │  │  │ Real-time Loc │  │
│  │ Planner Assign│  │  │ Reorder Alerts│  │  │ Role-based    │  │  │ Financial Rpt │  │  │ ETA Calc      │  │
│  └───────────────┘  │  └───────────────┘  │  └───────────────┘  │  └───────────────┘  │  └───────────────┘  │
├─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┤
│                                                                                                              │
│  ┌─────────────────────────────────────────┐    ┌─────────────────────────────────────────────────────┐     │
│  │        COMMUNICATION SERVICE            │    │              MENU SERVICE                           │     │
│  │  ┌───────────────────────────────────┐  │    │  ┌───────────────────────────────────────────────┐  │     │
│  │  │ Event Messages & Updates         │  │    │  │ Menu Items & Cuisines                        │  │     │
│  │  │ File Attachments (S3/Blob)       │  │    │  │ Pricing Management                           │  │     │
│  │  │ Internal Notifications           │  │    │  │ Dietary Info & Allergens                     │  │     │
│  │  │ Employee-Event Assignments       │  │    │  │ Availability Tracking                        │  │     │
│  │  └───────────────────────────────────┘  │    │  └───────────────────────────────────────────────┘  │     │
│  └─────────────────────────────────────────┘    └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                            INTEGRATION LAYER                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────┐     │
│  │ Maps API            │  │ Payment Gateway     │  │ Email/SMS Service   │  │ File Storage            │     │
│  │ (Google/Mapbox)     │  │ (Stripe/PayPal)     │  │ (SendGrid/Twilio)   │  │ (AWS S3/Azure Blob)     │     │
│  │ - Route Planning    │  │ - Payment Process   │  │ - Notifications     │  │ - Event Files           │     │
│  │ - Distance Calc     │  │ - Refunds           │  │ - Confirmations     │  │ - Invoices/Docs         │     │
│  │ - Traffic Data      │  │ - Transaction Log   │  │ - Reminders         │  │ - Encrypted Storage     │     │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  └─────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              DATA LAYER                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                           CENTRALIZED DATABASE (PostgreSQL / MySQL)                                 │    │
│  │                                                                                                     │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │  │   EVENTS    │ │   USERS     │ │ EMPLOYEES   │ │  INVENTORY  │ │  DELIVERY   │ │  FINANCE    │   │    │
│  │  │─────────────│ │─────────────│ │─────────────│ │─────────────│ │─────────────│ │─────────────│   │    │
│  │  │ events      │ │ users       │ │ employees   │ │ inventory_  │ │ delivery_   │ │ invoices    │   │    │
│  │  │ event_      │ │             │ │ employee_   │ │ categories  │ │ routes      │ │ payment_    │   │    │
│  │  │ planner     │ │             │ │ schedules   │ │ inventory_  │ │ route_events│ │ tickets     │   │    │
│  │  │ event_files │ │             │ │ event_      │ │ items       │ │ delivery_   │ │ orders      │   │    │
│  │  │ event_      │ │             │ │ assignments │ │ inventory_  │ │ assignments │ │             │   │    │
│  │  │ messages    │ │             │ │             │ │ usage       │ │ gps_tracking│ │             │   │    │
│  │  │ event_info  │ │             │ │             │ │ menu_items  │ │             │ │             │   │    │
│  │  │             │ │             │ │             │ │ cuisines    │ │             │ │             │   │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                                              │
│  ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────────────────┐    │
│  │ Redis Cache               │  │ Message Queue             │  │ Audit Log Storage                     │    │
│  │ - Session Storage         │  │ (RabbitMQ/AWS SQS)        │  │ - User Actions                        │    │
│  │ - Real-time GPS Cache     │  │ - Async Processing        │  │ - Data Access Logs                    │    │
│  │ - Frequently Accessed Data│  │ - Event-Driven Updates    │  │ - GDPR Compliance Records             │    │
│  └───────────────────────────┘  └───────────────────────────┘  └───────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        INFRASTRUCTURE LAYER                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                              CLOUD HOSTING (AWS / Azure / Local)                                    │    │
│  │                                                                                                     │    │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────────────────────────┐  │    │
│  │  │ PRODUCTION          │  │ STAGING             │  │ LOCAL DEVELOPMENT                           │  │    │
│  │  │ AWS EC2/ECS or      │  │ Scaled-down Prod    │  │ Docker Compose                              │  │    │
│  │  │ Azure App Service   │  │ Environment         │  │ Local PostgreSQL                            │  │    │
│  │  │ Auto-scaling        │  │ Testing & QA        │  │ Hot Reload Dev Server                       │  │    │
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────────────────────────────┘  │    │
│  │                                                                                                     │    │
│  │  Security: VPC | Security Groups | WAF | DDoS Protection | Encryption at Rest & Transit           │    │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Architectural Components

### 3.1 Client Layer (Thin Client Architecture)

The system employs a **thin-client architecture** where all business logic resides server-side, with clients only handling presentation.

| Client Type | Target Users | Key Features |
|-------------|--------------|--------------|
| **Web Browser (Desktop)** | Clients, Admins, Planners | Full booking interface, dashboards, reporting |
| **Mobile Browser (Responsive)** | Employees | Schedule viewing, event access, communications |
| **Driver Mobile App** | Delivery Drivers | GPS tracking, route navigation, delivery status |
| **Admin Dashboard** | System Administrators | User management, configuration, audit trails |

### 3.2 API Gateway Layer

Centralized entry point managing all client-server communications:

- **Request Routing**: Directs requests to appropriate microservices
- **Rate Limiting**: Prevents abuse and ensures fair usage
- **SSL Termination**: Handles HTTPS encryption/decryption
- **API Versioning**: Supports backward compatibility
- **Request Validation**: Schema validation before processing

### 3.3 Authentication & Authorization Layer

GDPR-compliant security implementation:

```
┌─────────────────────────────────────────────────────────────┐
│                    USER PERMISSION MATRIX                    │
├──────────────┬───────┬──────────┬────────┬─────────┬────────┤
│ Feature      │ Client│ Employee │ Driver │ Planner │ Admin  │
├──────────────┼───────┼──────────┼────────┼─────────┼────────┤
│ Create Book  │   ✓   │    ✗     │   ✗    │    ✓    │   ✓    │
│ View Events  │  Own  │ Assigned │Assigned│   All   │  All   │
│ GPS Tracking │   ✗   │    ✗     │   ✓    │    ✓    │   ✓    │
│ Scheduling   │   ✗   │  View    │  View  │  Edit   │  Full  │
│ Finance      │  Own  │    ✗     │   ✗    │  View   │  Full  │
│ Inventory    │   ✗   │    ✗     │   ✗    │   ✓     │   ✓    │
│ User Mgmt    │   ✗   │    ✗     │   ✗    │    ✗    │   ✓    │
│ Audit Logs   │   ✗   │    ✗     │   ✗    │    ✗    │   ✓    │
└──────────────┴───────┴──────────┴────────┴─────────┴────────┘
```

### 3.4 Application Layer (Core Services)

#### 3.4.1 Booking Service
```
┌────────────────────────────────────────────────────────────┐
│                  BOOKING VALIDATION PIPELINE                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [Client Request] ──► [Availability Check] ──► [Menu      │
│                            │                    Selection] │
│                            ▼                        │      │
│                    [Capacity Validation]            │      │
│                            │                        ▼      │
│                            └────────► [Invoice Generation] │
│                                              │             │
│                                              ▼             │
│                                    [Payment Ticket]        │
│                                              │             │
│                                              ▼             │
│                            [Event Creation (Validated)]    │
│                                              │             │
│                                              ▼             │
│                              [Planner Assignment]          │
│                                              │             │
│                                              ▼             │
│                          [Employee Notifications]          │
└────────────────────────────────────────────────────────────┘
```

#### 3.4.2 Inventory Management Service
- Real-time stock level tracking
- Category-based organization
- Usage tracking linked to events/orders
- Automated reorder threshold alerts
- Supplier contact management

#### 3.4.3 Employee Scheduling Service
- Shift management with role assignments
- Schedule viewing (employee self-service)
- Schedule management (employer controls)
- Event-to-employee assignment
- Availability tracking

#### 3.4.4 Finance Service
- Automated invoice generation
- Payment ticket creation and tracking
- Multiple payment method support
- Financial reporting
- Payment status tracking

#### 3.4.5 Delivery Service
```
┌────────────────────────────────────────────────────────────┐
│                    DELIVERY SYSTEM FLOW                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [Validated Event] ──► [Delivery Assignment Created]       │
│                                    │                       │
│                                    ▼                       │
│                         [Driver Assigned]                  │
│                                    │                       │
│                                    ▼                       │
│                    [Route Optimization Algorithm]          │
│                    (Multi-event route planning)            │
│                                    │                       │
│                                    ▼                       │
│               [GPS Tracking Initiated on Pickup]           │
│                           │                                │
│            ┌──────────────┼──────────────┐                │
│            ▼              ▼              ▼                 │
│      [Real-time      [Event Staff   [Client               │
│       Location]       Can Track]     Updates]             │
│            │              │              │                 │
│            └──────────────┼──────────────┘                │
│                           ▼                                │
│                    [Delivery Complete]                     │
│                           │                                │
│                           ▼                                │
│                   [Status Updated]                         │
└────────────────────────────────────────────────────────────┘
```

#### 3.4.6 Communication Service
- Event-specific message boards
- File attachment support
- Employee assignment notifications
- Real-time updates for event changes
- Internal communication hub

---

## 4. Data Architecture

### 4.1 Database Schema Overview

Based on the ER diagram, the database is organized into logical domains:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATABASE DOMAIN MODEL                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐         ┌─────────────────┐                   │
│  │  EVENT DOMAIN   │────────►│  USER DOMAIN    │                   │
│  │                 │         │                 │                   │
│  │ • events        │         │ • users         │                   │
│  │ • event_planner │◄────────│                 │                   │
│  │ • event_files   │         └────────┬────────┘                   │
│  │ • event_messages│                  │                            │
│  │ • event_info    │                  ▼                            │
│  └────────┬────────┘         ┌─────────────────┐                   │
│           │                  │ EMPLOYEE DOMAIN │                   │
│           │                  │                 │                   │
│           │                  │ • employees     │                   │
│           │                  │ • employee_     │                   │
│           │                  │   schedules     │                   │
│           │                  │ • event_        │                   │
│           └─────────────────►│   assignments   │                   │
│                              └────────┬────────┘                   │
│                                       │                            │
│  ┌─────────────────┐                  │     ┌─────────────────┐    │
│  │ FINANCE DOMAIN  │◄─────────────────┼────►│ DELIVERY DOMAIN │    │
│  │                 │                  │     │                 │    │
│  │ • invoices      │                  │     │ • delivery_     │    │
│  │ • payment_      │                  │     │   routes        │    │
│  │   tickets       │                  │     │ • route_events  │    │
│  │ • orders        │                  │     │ • delivery_     │    │
│  └─────────────────┘                  │     │   assignments   │    │
│                                       │     │ • gps_tracking  │    │
│  ┌─────────────────┐                  │     └─────────────────┘    │
│  │ INVENTORY DOMAIN│◄─────────────────┘                            │
│  │                 │                                               │
│  │ • inventory_    │         ┌─────────────────┐                   │
│  │   categories    │         │  MENU DOMAIN    │                   │
│  │ • inventory_    │◄───────►│                 │                   │
│  │   items         │         │ • menu_items    │                   │
│  │ • inventory_    │         │ • cuisines      │                   │
│  │   usage         │         └─────────────────┘                   │
│  └─────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Key Entity Relationships

| Relationship | Description |
|--------------|-------------|
| `events` → `event_planner` | Each event is assigned to planners |
| `events` → `event_assignments` | Multiple employees assigned per event |
| `events` → `invoices` | Each validated booking generates an invoice |
| `invoices` → `payment_tickets` | Invoices have associated payment tickets |
| `events` → `delivery_assignments` | Events linked to delivery logistics |
| `delivery_assignments` → `gps_tracking` | Real-time location data per delivery |
| `delivery_routes` → `route_events` | Optimized routes contain multiple events |
| `inventory_items` → `inventory_usage` | Stock depletion tracked per usage |
| `employees` → `employee_schedules` | Staff scheduling and shifts |

---

## 5. GDPR Compliance Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      GDPR COMPLIANCE FRAMEWORK                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ DATA GOVERNANCE │  │ ACCESS CONTROL  │  │ AUDIT TRAILS    │     │
│  │                 │  │                 │  │                 │     │
│  │ • Data          │  │ • Role-based    │  │ • All user      │     │
│  │   classification│  │   permissions   │  │   actions logged│     │
│  │ • Retention     │  │ • Principle of  │  │ • Data access   │     │
│  │   policies      │  │   least         │  │   tracking      │     │
│  │ • Encryption    │  │   privilege     │  │ • Modification  │     │
│  │   standards     │  │ • Session       │  │   history       │     │
│  │                 │  │   management    │  │ • Export        │     │
│  │                 │  │                 │  │   capability    │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ USER RIGHTS     │  │ DATA PROTECTION │  │ BREACH RESPONSE │     │
│  │                 │  │                 │  │                 │     │
│  │ • Right to      │  │ • Encryption at │  │ • Detection     │     │
│  │   access        │  │   rest (AES-256)│  │   monitoring    │     │
│  │ • Right to      │  │ • Encryption in │  │ • 72-hour       │     │
│  │   erasure       │  │   transit (TLS) │  │   notification  │     │
│  │ • Data          │  │ • Pseudonymiz-  │  │ • Incident      │     │
│  │   portability   │  │   ation         │  │   response plan │     │
│  │ • Consent       │  │ • Secure backup │  │                 │     │
│  │   management    │  │                 │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Deployment Architecture

### 6.1 Cloud Deployment (AWS)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS DEPLOYMENT MODEL                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─── Public Subnet ─────────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  [Route 53]──►[CloudFront CDN]──►[Application Load Balancer] │  │
│  │                                              │                │  │
│  └──────────────────────────────────────────────┼────────────────┘  │
│                                                 │                   │
│  ┌─── Private Subnet ───────────────────────────┼────────────────┐  │
│  │                                              ▼                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │  │
│  │  │ ECS/EKS    │  │ ECS/EKS    │  │ ECS/EKS    │           │  │
│  │  │ Service A  │  │ Service B  │  │ Service C  │           │  │
│  │  │ (Booking)  │  │ (Inventory)│  │ (Delivery) │           │  │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘           │  │
│  │         │               │               │                  │  │
│  │         └───────────────┼───────────────┘                  │  │
│  │                         ▼                                  │  │
│  │  ┌─────────────────────────────────────────────────────┐   │  │
│  │  │              RDS PostgreSQL (Multi-AZ)              │   │  │
│  │  └─────────────────────────────────────────────────────┘   │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │  │
│  │  │ ElastiCache │  │    SQS       │  │     S3       │     │  │
│  │  │  (Redis)    │  │  (Queues)    │  │  (Storage)   │     │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  [AWS WAF] [AWS Shield] [CloudWatch] [CloudTrail]                │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Cloud Deployment (Azure)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       AZURE DEPLOYMENT MODEL                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Azure DNS]──►[Azure Front Door]──►[Azure Application Gateway]    │
│                                              │                      │
│                                              ▼                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Azure App Service Plan                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │ Web App    │  │ Web App    │  │ Web App    │          │   │
│  │  │ (Booking)  │  │ (Inventory)│  │ (Delivery) │          │   │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘          │   │
│  └─────────┼───────────────┼───────────────┼────────────────────┘   │
│            │               │               │                        │
│            └───────────────┼───────────────┘                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │         Azure Database for PostgreSQL (Flexible)            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [Azure Cache Redis]  [Service Bus]  [Blob Storage]                │
│  [Azure Monitor]  [Azure Sentinel]  [Key Vault]                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 Local Development Environment

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LOCAL DEVELOPMENT SETUP                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  docker-compose.yml                                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │  services:                                                  │   │
│  │    app:           # Flask/FastAPI Application               │   │
│  │      ports: 5000                                            │   │
│  │      volumes: ./src:/app                                    │   │
│  │      environment: DATABASE_URL, SECRET_KEY                  │   │
│  │                                                             │   │
│  │    db:            # PostgreSQL Database                     │   │
│  │      image: postgres:15                                     │   │
│  │      ports: 5432                                            │   │
│  │      volumes: pgdata:/var/lib/postgresql/data               │   │
│  │                                                             │   │
│  │    redis:         # Cache & Session Storage                 │   │
│  │      image: redis:alpine                                    │   │
│  │      ports: 6379                                            │   │
│  │                                                             │   │
│  │    web:           # Nginx (optional) or direct Flask        │   │
│  │      ports: 80                                              │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Alternative: Direct Python execution                               │
│  $ conda activate greenbite-cms                                     │
│  $ python auth_server.py                                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Security Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYERS                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER 1: PERIMETER SECURITY                                        │
│  ├─ Web Application Firewall (WAF)                                  │
│  ├─ DDoS Protection                                                 │
│  ├─ Rate Limiting                                                   │
│  └─ IP Whitelisting (Admin functions)                               │
│                                                                     │
│  LAYER 2: TRANSPORT SECURITY                                        │
│  ├─ TLS 1.3 Encryption                                              │
│  ├─ Certificate Management                                          │
│  └─ HSTS Enforcement                                                │
│                                                                     │
│  LAYER 3: APPLICATION SECURITY                                      │
│  ├─ JWT Token Authentication                                        │
│  ├─ Role-Based Access Control (RBAC)                                │
│  ├─ Input Validation & Sanitization                                 │
│  ├─ CSRF Protection                                                 │
│  └─ SQL Injection Prevention (Parameterized Queries)                │
│                                                                     │
│  LAYER 4: DATA SECURITY                                             │
│  ├─ AES-256 Encryption at Rest                                      │
│  ├─ Password Hashing (bcrypt/Argon2)                                │
│  ├─ PII Data Masking                                                │
│  └─ Secure Key Management                                           │
│                                                                     │
│  LAYER 5: MONITORING & RESPONSE                                     │
│  ├─ Security Event Logging                                          │
│  ├─ Intrusion Detection                                             │
│  ├─ Automated Alerting                                              │
│  └─ Incident Response Procedures                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Integration Points

### 8.1 External API Integrations

| Integration | Purpose | Provider Options |
|-------------|---------|------------------|
| **Maps & Routing** | Route optimization, distance calculation, real-time traffic | Google Maps API, Mapbox, HERE |
| **Payment Processing** | Invoice payments, refunds, transaction logging | Stripe, PayPal, Square |
| **Notifications** | Email confirmations, SMS alerts, push notifications | SendGrid, Twilio, AWS SNS |
| **File Storage** | Event documents, invoices, attachments | AWS S3, Azure Blob, Google Cloud Storage |

### 8.2 Internal Service Communication

```
┌─────────────────────────────────────────────────────────────────────┐
│               SERVICE COMMUNICATION PATTERNS                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SYNCHRONOUS (REST API):                                            │
│  ┌──────────┐  HTTP/JSON  ┌──────────┐                             │
│  │ Booking  │────────────►│ Finance  │  (Invoice generation)       │
│  │ Service  │◄────────────│ Service  │                             │
│  └──────────┘             └──────────┘                             │
│                                                                     │
│  ASYNCHRONOUS (Message Queue):                                      │
│  ┌──────────┐   Event    ┌──────────┐   Event   ┌──────────┐       │
│  │ Booking  │───Created──►│  Queue   │──────────►│ Delivery │       │
│  │ Service  │            │          │           │ Service  │       │
│  └──────────┘            └──────────┘           └──────────┘       │
│                                │                                    │
│                                ▼                                    │
│                          ┌──────────┐                              │
│                          │ Notifier │                              │
│                          │ Service  │                              │
│                          └──────────┘                              │
│                                                                     │
│  REAL-TIME (WebSocket):                                            │
│  ┌──────────┐  WebSocket  ┌──────────┐                             │
│  │ Driver   │◄───────────►│ Tracking │  (GPS Updates)              │
│  │ App      │             │ Service  │                             │
│  └──────────┘             └──────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Scalability Considerations

### 9.1 Horizontal Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SCALING ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                    ┌─────────────────────┐                          │
│                    │   Load Balancer     │                          │
│                    └──────────┬──────────┘                          │
│                               │                                     │
│        ┌──────────────────────┼──────────────────────┐             │
│        │                      │                      │             │
│        ▼                      ▼                      ▼             │
│  ┌──────────┐          ┌──────────┐          ┌──────────┐          │
│  │ App      │          │ App      │          │ App      │          │
│  │ Instance │          │ Instance │          │ Instance │          │
│  │    1     │          │    2     │          │    N     │          │
│  └────┬─────┘          └────┬─────┘          └────┬─────┘          │
│       │                     │                     │                │
│       └─────────────────────┼─────────────────────┘                │
│                             │                                      │
│                             ▼                                      │
│                    ┌─────────────────┐                             │
│                    │  Redis Cluster  │  (Session & Cache)          │
│                    └────────┬────────┘                             │
│                             │                                      │
│                             ▼                                      │
│        ┌─────────────────────────────────────────┐                 │
│        │        Database (Read Replicas)         │                 │
│        │  ┌─────────┐   ┌─────────┐   ┌───────┐ │                 │
│        │  │ Primary │──►│ Replica │   │Replica│ │                 │
│        │  │  (RW)   │   │  (R)    │   │  (R)  │ │                 │
│        │  └─────────┘   └─────────┘   └───────┘ │                 │
│        └─────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Auto-Scaling Triggers

| Metric | Scale Up Threshold | Scale Down Threshold |
|--------|-------------------|---------------------|
| CPU Utilization | > 70% for 5 min | < 30% for 10 min |
| Memory Usage | > 80% | < 40% |
| Request Count | > 1000 req/min | < 200 req/min |
| Response Time | > 500ms avg | < 100ms avg |

---

## 10. Technology Stack Summary

| Layer | Technology Options |
|-------|-------------------|
| **Frontend** | HTML5, CSS3, JavaScript, React/Vue.js (optional) |
| **Backend** | Python (Flask/FastAPI), Node.js (alternative) |
| **Database** | PostgreSQL (primary), Redis (cache) |
| **Authentication** | JWT, OAuth 2.0, bcrypt |
| **Message Queue** | RabbitMQ, AWS SQS, Azure Service Bus |
| **File Storage** | AWS S3, Azure Blob Storage |
| **Containerization** | Docker, Kubernetes (production) |
| **CI/CD** | GitHub Actions, Azure DevOps, AWS CodePipeline |
| **Monitoring** | CloudWatch, Azure Monitor, Prometheus/Grafana |

---

## 11. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-18 | GreenBite Team | Initial architecture document |

---

*This document provides a high-level overview of the GreenBite CMS architecture. Detailed implementation specifications for individual components should be referenced in their respective technical documentation.*
