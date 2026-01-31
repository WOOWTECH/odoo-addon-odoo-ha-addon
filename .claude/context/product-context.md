---
created: 2026-01-01T15:23:16Z
last_updated: 2026-01-01T15:23:16Z
version: 1.0
author: Claude Code PM System
---

# Product Context

## Product Definition

**WOOW Dashboard** is an Odoo addon that bridges Home Assistant IoT ecosystems with enterprise resource planning, enabling businesses to monitor, control, and analyze their IoT infrastructure directly within the Odoo interface.

## Target Users

### Primary Personas

#### 1. Facility Manager
- **Profile:** Manages building operations, HVAC, lighting, security
- **Goals:**
  - Monitor all building systems in one place
  - Control devices remotely
  - View historical data for maintenance planning
- **Pain Points:**
  - Switching between multiple dashboards
  - No integration with business workflows

#### 2. Operations Director
- **Profile:** Oversees manufacturing or warehouse operations
- **Goals:**
  - Real-time visibility into sensor data
  - Correlate IoT data with business metrics
  - Generate reports for stakeholders
- **Pain Points:**
  - IoT data isolated from ERP
  - Manual data export/import processes

#### 3. IT Administrator
- **Profile:** Manages enterprise systems and integrations
- **Goals:**
  - Secure, controlled access to IoT data
  - Multi-instance support for different locations
  - Easy configuration and maintenance
- **Pain Points:**
  - Complex multi-system integration
  - User permission management

## Core Functionality

### Feature Categories

#### 1. Real-time Monitoring
- Live entity state display
- WebSocket-based updates
- Multi-instance support
- Area-based organization

#### 2. Device Control
- Switch, light, climate control
- Scene and automation triggers
- Script execution
- Cover and fan control

#### 3. Historical Data
- Entity history tracking
- Chart visualizations
- Timeline views
- Data export capabilities

#### 4. Organization
- Area (room) management
- Device grouping
- Entity tagging
- Label system

#### 5. Administration
- Multi-instance configuration
- User access control
- WebSocket connection management
- Sync operations

## Use Cases

### UC1: Building Climate Monitoring
```
As a Facility Manager
I want to see all HVAC sensors on a dashboard
So that I can quickly identify comfort issues
```

### UC2: Manufacturing Sensor Integration
```
As an Operations Director
I want IoT sensor data in my Odoo reports
So that I can correlate production with environmental conditions
```

### UC3: Multi-site Management
```
As an IT Administrator
I want to connect multiple Home Assistant instances
So that I can manage all locations from one Odoo installation
```

### UC4: Device Troubleshooting
```
As a Facility Manager
I want to view historical sensor data
So that I can diagnose intermittent equipment issues
```

### UC5: Access Control
```
As an IT Administrator
I want to restrict users to specific Home Assistant instances
So that employees only see data relevant to their location
```

## User Journeys

### Journey 1: First-time Setup
1. Install addon in Odoo
2. Configure Home Assistant instance (URL, token)
3. Sync entities from Home Assistant
4. Organize entities by area/group
5. Set up user permissions
6. Access dashboard

### Journey 2: Daily Monitoring
1. Login to Odoo
2. Navigate to WOOW Dashboard
3. Select instance (if multiple)
4. View real-time entity states
5. Interact with controllable devices
6. Check historical trends

### Journey 3: Incident Response
1. Receive notification of anomaly
2. Open relevant dashboard
3. View current and historical data
4. Control affected devices
5. Document incident in Odoo

## Product Requirements

### Functional Requirements
- [x] Connect to Home Assistant via REST API
- [x] Real-time updates via WebSocket
- [x] Multi-instance support
- [x] Entity state display and control
- [x] Historical data visualization
- [x] Area-based organization
- [x] User access control

### Non-functional Requirements
- **Performance:** Real-time updates < 500ms latency
- **Reliability:** Auto-reconnect on connection loss
- **Scalability:** Support 1000+ entities per instance
- **Security:** Token-based authentication, role-based access
- **Usability:** Consistent with Odoo UX patterns

## Constraints

### Technical Constraints
- Requires Odoo 18.0
- Requires Home Assistant with API access enabled
- WebSocket connections may be blocked by some firewalls

### Business Constraints
- LGPL-3 license
- Part of WOOW addon ecosystem

## Success Metrics

| Metric | Target |
|--------|--------|
| Entity sync success rate | >99% |
| WebSocket uptime | >99.5% |
| Control command success | >99% |
| Page load time | <2 seconds |
| User satisfaction | >4/5 rating |
