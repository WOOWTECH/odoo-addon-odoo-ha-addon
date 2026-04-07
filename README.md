<p align="center">
  <img src="https://img.shields.io/badge/Odoo-18.0-875A7B?style=for-the-badge&logo=odoo&logoColor=white" alt="Odoo 18"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/License-LGPL--3-blue?style=for-the-badge" alt="LGPL-3"/>
  <img src="https://img.shields.io/badge/Home_Assistant-2024.1+-41BDF5?style=for-the-badge&logo=homeassistant&logoColor=white" alt="Home Assistant"/>
  <img src="https://img.shields.io/badge/WebSocket-Real--time-010101?style=for-the-badge&logo=socketdotio&logoColor=white" alt="WebSocket"/>
  <img src="https://img.shields.io/badge/OWL-Frontend-714B67?style=for-the-badge" alt="OWL"/>
</p>

<h1 align="center">WOOW Dashboard</h1>

<p align="center">
  <strong>Home Assistant Integration for Odoo 18 ERP</strong><br/>
  Real-time IoT device monitoring, control, and sharing — directly in your Odoo backend and portal.
</p>

<p align="center">
  <code>v18.0.6.2</code> &nbsp;·&nbsp;
  <a href="#screenshots">Screenshots</a> &nbsp;·&nbsp;
  <a href="#installation">Installation</a> &nbsp;·&nbsp;
  <a href="#configuration">Configuration</a> &nbsp;·&nbsp;
  <a href="README_zh-TW.md">繁體中文</a>
</p>

---

## Why WOOW Dashboard?

| Challenge | Solution |
|---|---|
| IoT data locked in Home Assistant | Unified dashboard inside your ERP |
| No business-level device sharing | User-based portal sharing with granular permissions |
| Disconnected monitoring tools | Real-time WebSocket bridge — no polling |
| Multi-site HA deployments | Multi-instance support with session-based switching |
| No audit trail for device states | Entity history recording with chart visualization |

---

## Overview

WOOW Dashboard bridges **Home Assistant** and **Odoo ERP**, bringing real-time IoT device monitoring, control, and sharing into your business management platform. It connects to one or more Home Assistant instances via WebSocket and REST API, synchronizes entities, areas, and devices, and exposes them through Odoo's backend views and portal pages.

Whether you manage a smart office, a fleet of industrial sensors, or a building automation system, WOOW Dashboard lets your team monitor and control IoT devices without leaving Odoo — and share device access with external users through a secure portal.

---

## Features

### Core Integration

- **Home Assistant Integration** — Real-time bidirectional communication via WebSocket and REST API with automatic reconnection and state synchronization.
- **Multi-Instance Support** — Connect and manage multiple Home Assistant instances from a single Odoo installation. Session-based instance selection with user preference persistence.
- **Real-time Updates** — Home Assistant state changes stream through the Odoo Bus bridge to connected browser sessions, providing instant UI updates without polling.

### Entity Management

- **Entity Management & Control** — Full control for 10 device domains: switch, light, sensor, climate, cover, fan, automation, scene, script, and a generic fallback.
- **Entity Kanban View** — Custom Odoo kanban view with real-time state display, domain-specific controls, and inline entity interaction.
- **Entity History** — Record and visualize entity state changes over time with a dedicated chart-based timeline view.

### Device & Area Organization

- **Area & Device Management** — Bidirectional sync of areas and devices from Home Assistant. Visual area dashboard with device cards and embedded entity controllers.
- **Device Area Inheritance** — Entities automatically inherit their area from their parent device, with a "Follows Device" toggle for fine-grained control.
- **Glances System Monitoring** — View Home Assistant host system metrics (CPU, memory, disk, network) directly within Odoo through Glances integration.

### Portal & Sharing

- **Portal Sharing** — Share entities and entity groups with portal users. User-based permissions with configurable access levels (read-only or full control) and optional expiry dates.
- **Portal Entity Control** — Full device control on the portal with the same controller components as the backend, adapted for public access.

### Advanced Features

- **Blueprint Wizard** — Create Home Assistant automations from blueprints with a guided form wizard directly in Odoo.
- **Internationalization** — Full Traditional Chinese (zh_TW) translation coverage. All backend and portal interfaces support multi-language display.
- **Custom Views** — Purpose-built Odoo views including entity history timeline, entity kanban with real-time state, and area dashboard with device-first layout.

---

## Supported Entity Domains

| Domain | Capabilities |
|---|---|
| **switch** | Toggle on/off |
| **light** | Toggle, brightness, color temperature |
| **sensor** | Read-only value display with attributes |
| **climate** | Temperature target, HVAC mode, fan mode |
| **cover** | Open, close, stop, position slider |
| **fan** | Toggle, speed control, oscillation |
| **automation** | Toggle enable/disable, manual trigger |
| **scene** | Activate scene |
| **script** | Execute, toggle on/off |
| **generic** | Basic state display for unsupported domains |

---

## Screenshots

### Instance Dashboard

The entry page showing connected Home Assistant instances with connection status, entity/area counts, and quick navigation buttons.

<p align="center">
  <img src="docs/screenshots/instance_dashboard.png" alt="Instance Dashboard" width="720"/>
</p>

### HA Info Dashboard

System information panel with WebSocket connection status, hardware details, storage, and network monitoring.

<p align="center">
  <img src="docs/screenshots/ha_info_dashboard.png" alt="HA Info Dashboard" width="720"/>
</p>

### Area Dashboard

Device cards organized by Home Assistant areas with area tabs. Each card shows embedded entity controllers for direct interaction — toggle lights, activate scenes, adjust settings.

<p align="center">
  <img src="docs/screenshots/area_dashboard.png" alt="Area Dashboard" width="720"/>
</p>

<p align="center">
  <img src="docs/screenshots/area_dashboard_controls.png" alt="Area Dashboard Controls" width="720"/>
</p>

### Entity List & Kanban

All synchronized entities with real-time state display, domain filtering, area assignment, and group/tag organization. Switch between list and kanban views.

<p align="center">
  <img src="docs/screenshots/entity_list.png" alt="Entity List View" width="720"/>
</p>

<p align="center">
  <img src="docs/screenshots/entity_kanban.png" alt="Entity Kanban View" width="720"/>
</p>

### Entity Form

Detailed entity view showing state, domain, area assignment (with "Follows Device" toggle), groups, tags, labels, and custom properties. Includes "Share with Users" action for portal sharing.

<p align="center">
  <img src="docs/screenshots/entity_form.png" alt="Entity Form View" width="720"/>
</p>

### Device Management

All Home Assistant devices with manufacturer, model, area assignment, and associated entities.

<p align="center">
  <img src="docs/screenshots/device_list.png" alt="Device List" width="720"/>
</p>

### Instance Configuration

HA instance form with connection settings, sync controls (Test Connection, Sync Registry, Sync Entities, Restart WebSocket), and instance identification.

<p align="center">
  <img src="docs/screenshots/ha_instance_form.png" alt="HA Instance Configuration" width="720"/>
</p>

### Settings

WebSocket configuration page with connection status, instance management, API URL, and access token settings.

<p align="center">
  <img src="docs/screenshots/settings.png" alt="Settings" width="720"/>
</p>

### Portal (User-Facing)

Portal users can view and control shared entities through a secure, responsive interface.

| Screenshot | Description |
|:---:|---|
| ![Portal Home](docs/screenshots/portal/01-portal-home.png) | **Portal Home** — User's portal landing page with shared instance summary. |
| ![Instance List](docs/screenshots/portal/02-instance-list.png) | **Instance List** — Shared HA instances with entity and group counts. |
| ![Instance Detail](docs/screenshots/portal/03-instance-detail.png) | **Instance Detail** — Shared entities with permission badges. |
| ![Entity Control](docs/screenshots/portal/04-entity-control.png) | **Entity Control** — Light entity with brightness slider and toggle. |
| ![Entity Group](docs/screenshots/portal/05-entity-group.png) | **Entity Group** — Responsive card grid with individual controllers. |
| ![Sensor View](docs/screenshots/portal/06-entity-sensor.png) | **Sensor View** — Read-only sensor with value, unit, and attributes. |

---

## Architecture

```
┌───────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   Browser (OWL)   │  <───>  │   Odoo Server    │  <───>  │  Home Assistant   │
├───────────────────┤         ├──────────────────┤         ├──────────────────┤
│ OWL Components    │         │ Models           │         │ WebSocket API    │
│ ha_data_service   │  RPC    │ ha_entity        │  WS/    │ REST API         │
│ ha_bus_bridge     │ <────>  │ ha_instance      │  REST   │ State Machine    │
│ Entity Controllers│         │ ha_area/device   │ <────>  │                  │
│ Chart Service     │         │ HA API Client    │         │                  │
└───────────────────┘         └──────────────────┘         └──────────────────┘
        ▲                             │
        │      Odoo Bus Bridge        │
        └─────────────────────────────┘
           (Real-time state propagation)
```

### Data Flow

- **Backend**: Odoo models communicate with Home Assistant through a dedicated API client supporting both WebSocket subscriptions and REST calls.
- **Frontend**: OWL components consume data through a service layer (`ha_data_service`) that handles RPC calls, caching, and reactive state management.
- **Real-time**: A WebSocket bridge subscribes to Home Assistant state changes and relays them through the Odoo Bus to all connected browser sessions.
- **Portal**: Dedicated controllers serve portal pages with user-based access validation, fetching entity state through the same backend API client.

### Key Design Patterns

| Pattern | Usage |
|---|---|
| **Service-First** | Use `useService("ha_data")`, never direct RPC |
| **Bus Notifications** | Use `bus_service.subscribe()` for real-time updates |
| **Reactive State** | `useState()` + service callbacks |
| **Entity Control** | Shared `useEntityControl` hook across backend and portal |

---

## Installation

### Prerequisites

| Component | Version |
|---|---|
| Odoo | 18.0+ (Community or Enterprise) |
| Home Assistant | 2024.1+ |
| Python | 3.10+ |
| websockets | Auto-installed via `pre_init_hook` |

### Odoo Module Dependencies

- `base`, `web`, `mail`, `portal`

### From Source

This repository **is** the Odoo addon. Clone or download it directly into your Odoo addons directory:

```bash
# Clone into your Odoo addons path, renaming to odoo_ha_addon
git clone https://github.com/WOOWTECH/odoo-addon-odoo-ha-addon.git \
  /path/to/odoo/addons/odoo_ha_addon

# Or download and extract the ZIP from GitHub Releases
```

Then in Odoo:

1. Go to **Apps** and click **Update Apps List**
2. Search for and install **WOOW Dashboard**

> The Python dependency `websockets` is automatically installed via the `pre_init_hook` — no manual pip install is required.

### Using Docker (Development)

```bash
# Clone the repository
git clone https://github.com/WOOWTECH/odoo-addon-odoo-ha-addon.git
cd odoo-addon-odoo-ha-addon

# Set up environment
cp .env.example .env

# Start services
docker compose up -d

# Access Odoo at http://localhost:8069
```

---

## Configuration

1. Navigate to **Settings** > **WOOW HA**
2. Click **+ New Instance** and enter:
   - **Instance Name**: A descriptive label for the Home Assistant instance
   - **API URL**: Home Assistant base URL (e.g., `http://homeassistant.local:8123`)
   - **Access Token**: A [Long-Lived Access Token](https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token) generated in Home Assistant
3. Click **Test Connection** to verify connectivity
4. Click **Sync Registry** to import areas, devices, and labels
5. Click **Sync Entities** to import all entities

The WebSocket connection will be established automatically, providing real-time state updates.

---

## Project Structure

```
odoo_ha_addon/                   # ← This repo (clone as odoo_ha_addon)
├── __manifest__.py              # Odoo module manifest (v18.0.6.2)
├── __init__.py                  # Python package init
├── hooks.py                     # Install/uninstall hooks
├── models/                      # Backend models & business logic
│   ├── common/                  # Shared utilities (API client, helpers)
│   ├── ha_instance.py           # HA instance management
│   ├── ha_entity.py             # Entity model & WebSocket sync
│   ├── ha_area.py               # Area bidirectional sync
│   ├── ha_device.py             # Device management
│   ├── ha_entity_share.py       # Portal sharing model
│   └── ...                      # Other models
├── controllers/                 # HTTP & portal controllers
├── views/                       # XML view definitions & templates
├── static/src/                  # Frontend (OWL components, JS, SCSS)
│   ├── services/                # Service layer (ha_data, chart, bus bridge)
│   ├── actions/                 # Client action pages (dashboards)
│   ├── views/                   # Custom view types (hahistory, entity_kanban)
│   ├── components/              # Reusable UI components
│   ├── portal/                  # Portal-specific components
│   └── hooks/                   # Shared hooks (entity control)
├── security/                    # Access rights & record rules
├── data/                        # Initial data, menus, cron jobs
├── i18n/                        # Translation files (zh_TW)
├── wizard/                      # Wizard views (blueprint, clear instance)
├── tests/                       # Unit, integration & E2E tests
├── docs/                        # Technical documentation & screenshots
├── scripts/                     # Development automation scripts
├── config/                      # Docker & Nginx configuration
├── docker-compose.yml           # Docker development environment
├── CHANGELOG.md                 # Release history (English)
└── CHANGELOG-tw.md              # Release history (繁體中文)
```

---

## Security

### Two-Tier Permission System

- **Backend Access**: HA Admin and HA User groups with record-level security rules. Admins can manage instances and sync data; users can view and control assigned entities.
- **Portal Access**: User-based sharing with per-entity and per-group permission records. Supports read-only and full-control access levels with optional expiry dates.

### API Security

- All Home Assistant API calls use Long-Lived Access Tokens stored in Odoo's encrypted credential store
- Portal entity access is validated against sharing records with `hmac.compare_digest()` for timing-attack prevention
- WebSocket connections use authenticated sessions with automatic token rotation

---

## API Reference

All backend API endpoints follow a standard response format:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### Key Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/ha/entity/state` | POST | Get entity current state |
| `/ha/entity/control` | POST | Send control command to entity |
| `/ha/instance/sync` | POST | Trigger entity synchronization |
| `/portal/entity/<id>/state` | GET | Portal entity state (JSON polling) |

For complete API documentation, see [docs/architecture/overview.md](docs/architecture/overview.md).

---

## Testing

```bash
# Run unit tests
python -m pytest tests/ -v

# Run with Odoo test runner
./odoo-bin -d test_db -i odoo_ha_addon --test-enable --stop-after-init

# E2E tests (Playwright)
# See tests/e2e_tests/ for configuration
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history.

### Recent Highlights

- **v18.0.6.2** — Portal breadcrumbs, live status sidebar, entity form control panel
- **v18.0.6.1** — User-based sharing migration (token → user permissions)
- **v18.0.6.0** — Portal sharing system, entity groups, portal controllers
- **v18.0.5.0** — Blueprint wizard, Glances integration, entity history

---

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes with clear messages
4. Ensure all tests pass
5. Submit a pull request

For development setup details, see the [Development Guide](docs/guides/development.md).

---

## License

This project is licensed under the **GNU Lesser General Public License v3.0 (LGPL-3)**.

See the [LICENSE](https://www.gnu.org/licenses/lgpl-3.0.html) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/WOOWTECH/odoo-addon-odoo-ha-addon/issues)
- **Documentation**: [docs/](docs/)
- **Developer Guide**: [docs/guides/development.md](docs/guides/development.md)
- **Troubleshooting**: [docs/guides/troubleshooting.md](docs/guides/troubleshooting.md)

---

<p align="center">
  Developed and maintained by <strong><a href="https://github.com/WOOWTECH">WOOWTECH</a></strong>
</p>
