---
created: 2026-01-01T15:23:16Z
last_updated: 2026-01-18T15:12:55Z
version: 1.3
author: Claude Code PM System
---

# Project Overview

## Features

### Dashboard & Visualization

| Feature | Description | Status |
|---------|-------------|--------|
| Instance Dashboard | Entry page showing all configured HA instances | Active |
| Main Dashboard | Real-time entity state overview | Active |
| Area Dashboard | Device-centric view organized by rooms | Active |
| Glances Dashboard | System monitoring integration | Active |
| Chart Visualizations | Line, timeline, and block charts | Active |
| HAHistory View | Custom Odoo view for historical data | Active |

### Entity Management

| Feature | Description | Status |
|---------|-------------|--------|
| Entity List | Kanban and list views of entities | Active |
| Entity Control | Toggle switches, lights, climate, etc. | Active |
| Entity History | Time-series data storage and display | Active |
| Entity Grouping | Organize entities into groups | Active |
| Entity Tagging | Tag entities for filtering | Active |
| Related Entities | View entity relationships | Active |
| Entity Sharing | User-based entity sharing (NEW) | Active |

### Portal Access

| Feature | Description | Status |
|---------|-------------|--------|
| Portal Entity View | User-based portal access (login required) | Active |
| Portal Group View | Portal access for entity groups | Active |
| Portal Entity Control | Control switch/light/fan from portal | Active |
| My HA Portal | `/my/ha/*` routes for portal users | Active |
| Share Wizard | Entity sharing wizard | Active |

### Device Types Supported

| Domain | Control Support |
|--------|-----------------|
| switch | On/Off toggle |
| light | On/Off, brightness (partial) |
| climate | Temperature, mode |
| cover | Open/Close/Stop |
| fan | On/Off, speed |
| automation | Enable/Disable, trigger |
| scene | Activate |
| script | Execute |
| sensor | Display only |
| binary_sensor | Display only |

### Multi-Instance Support

| Feature | Description |
|---------|-------------|
| Instance Configuration | URL, token, sync settings |
| Instance Switching | Session-based context switching |
| Instance Isolation | Data separated by instance |
| Access Control | Per-instance user permissions |

### Real-time Updates

| Feature | Description |
|---------|-------------|
| WebSocket Connection | Persistent connection to HA |
| State Subscriptions | Automatic entity state updates |
| Bus Notifications | Frontend notification system |
| Auto-reconnect | Connection recovery on failure |

### Administration

| Feature | Description |
|---------|-------------|
| Entity Sync | Pull entities from Home Assistant |
| Area Sync | Bidirectional area synchronization |
| Connection Health | WebSocket status monitoring |
| Clear Wizard | Data cleanup tools |

## Current State

### Active Development
- Branch: `main`
- Focus: User-based entity sharing, portal improvements

### Recent Changes (2026-01)
- **Share Wizard UI Fix** - 修復 Share Wizard alert 顯示多行的 UI 跑版問題
- **HA User Permission Fix** - ir.rule 快取問題修復，權限變更立即生效 (PR #62)
- **User-based Entity Sharing** - `ha.entity.share` model, share wizard
- **Portal Token Mechanism Removed** - `portal.mixin` removed, user-based access only
- **CCPM Documentation** - Full CCPM system docs added
- **Backlog PRDs** - HA user permission fix, UI improvements

### Previous Changes
- Chart constants extracted to `constants.js`
- Debug utilities replacing console methods
- Timeline block charts for binary/categorical entities
- Time scale support for chart views

### Known Limitations
- Font Awesome 4.x only (no FA5+ icons)
- Some device types have limited control support
- Large entity counts may impact performance
- Portal access requires login (token-based sharing removed)

## Integration Points

### External Systems
```
┌─────────────────┐     REST API      ┌─────────────────┐
│                 │ ◄───────────────► │                 │
│      Odoo       │                   │  Home Assistant │
│   WOOW addon    │ ◄───────────────► │                 │
│                 │    WebSocket      │                 │
└─────────────────┘                   └─────────────────┘
```

### Odoo Modules
- **base:** Core Odoo functionality
- **web:** Web client framework
- **mail:** Notification system (bus)

### Home Assistant APIs
- **REST API:** Entity states, service calls, area/device info
- **WebSocket API:** Real-time subscriptions, event streaming

## Architecture Summary

### Backend (Python)
- **Models:** Entity, Instance, Area, Device, Group, History, EntityShare
- **Controllers:** HTTP endpoints for frontend communication
- **Wizards:** Entity share wizard
- **Services:** WebSocket client, REST client, thread management

### Frontend (JavaScript/OWL)
- **Services:** Data service, chart service, bus bridge
- **Components:** Charts, cards, controllers, dialogs
- **Views:** Custom hahistory view, entity kanban
- **Actions:** Dashboard pages
- **Portal:** Portal entity controller, entity info, group info

## Documentation Resources

| Document | Purpose |
|----------|---------|
| CLAUDE.md | AI assistant guidelines |
| docs/README.md | Documentation index |
| docs/architecture/ | System design |
| docs/architecture/user-based-sharing.md | User-based sharing (NEW) |
| docs/guides/ | Development guides |
| docs/guides/i18n-development.md | i18n development (NEW) |
| docs/implementation/ | Feature details |
| docs/backlog-prd/ | Backlog PRDs (NEW) |
| CHANGELOG.md | Version history |
| README_CCPM.md | CCPM system docs (NEW) |

## Update History
- 2026-01-18: Added Share Wizard UI Fix to recent changes
- 2026-01-18: Added HA User Permission Fix to recent changes (PR #62)
- 2026-01-18: Added Portal Access section, user-based sharing, removed token mechanism
