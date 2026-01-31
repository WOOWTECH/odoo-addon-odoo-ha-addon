---
created: 2026-01-01T15:23:16Z
last_updated: 2026-01-01T15:23:16Z
version: 1.0
author: Claude Code PM System
---

# Project Brief

## What It Is

**WOOW Dashboard** (technical name: `odoo_ha_addon`) is an Odoo 18 addon that integrates Home Assistant IoT ecosystems with Odoo's enterprise platform. It provides real-time monitoring, device control, and historical analysis of IoT entities within the Odoo web interface.

## Why It Exists

### Problem Statement

Organizations using both Odoo ERP and Home Assistant for IoT face challenges:

1. **Data Silos:** IoT data is isolated from business systems
2. **Multiple Interfaces:** Users must switch between platforms
3. **No Integration:** Business workflows can't leverage IoT data
4. **Access Control:** Difficult to manage who sees what IoT data

### Solution

A native Odoo addon that:

- Brings Home Assistant data into Odoo
- Provides familiar Odoo-style interfaces
- Enables device control from Odoo
- Integrates with Odoo's security model
- Supports multiple Home Assistant instances

## Success Criteria

### Must Have

- [x] Connect to Home Assistant instances
- [x] Display real-time entity states
- [x] Control supported devices
- [x] View historical entity data
- [x] Multi-instance support
- [x] Role-based access control

### Should Have

- [x] Area-based organization
- [x] Entity grouping and tagging
- [x] Chart visualizations
- [x] Responsive design
- [x] i18n support (zh_TW)

### Nice to Have

- [ ] Automation triggers from Odoo
- [ ] Entity value alerts
- [ ] Custom dashboard layouts
- [ ] Mobile companion views

## Project Scope

### In Scope

- Home Assistant REST API integration
- Home Assistant WebSocket real-time updates
- Entity state visualization
- Device control interface
- Historical data charts
- Multi-instance management
- Odoo-style access control

### Out of Scope

- Home Assistant configuration from Odoo
- Home Assistant add-on management
- Direct device protocol communication
- Non-Home Assistant IoT platforms
- Mobile native apps

## Key Stakeholders

| Role       | Interest                            |
| ---------- | ----------------------------------- |
| End Users  | Monitor and control IoT devices     |
| IT Admins  | Configure instances, manage access  |
| Developers | Extend functionality, maintain code |
| WOOW Team  | Product direction, quality          |

## Timeline

### Current State

- **Version:** 18.0.5.0
- **Status:** Active development
- **Branch:** `share_entities`

### Recent Milestones

1. Multi-instance support implemented
2. WebSocket real-time updates working
3. Chart visualizations added
4. i18n (zh_TW) completed
5. CCPM system initialized

## Constraints

### Technical

- Must run on Odoo 18.0
- Python 3.10+ required
- PostgreSQL 15+ required
- Home Assistant API access needed

### Organizational

- Part of WOOW addon ecosystem
- LGPL-3 license required
- Chinese Traditional (zh_TW) primary language

## Risks

| Risk                             | Impact | Mitigation                         |
| -------------------------------- | ------ | ---------------------------------- |
| Home Assistant API changes       | High   | Abstract API calls, version checks |
| WebSocket connection instability | Medium | Auto-reconnect, health checks      |
| Performance with many entities   | Medium | Pagination, lazy loading           |
| Odoo version upgrades            | Medium | Follow Odoo development guidelines |

## Communication

### Repository

- **GitHub:** WOOWTECH/odoo-addons
- **Remote:** git@github.com:WOOWTECH/odoo-addons.git

### Documentation

- **Main:** `CLAUDE.md` (AI assistant guidelines)
- **Technical:** `docs/` directory
- **Changelog:** `CHANGELOG.md`, `CHANGELOG-tw.md`
