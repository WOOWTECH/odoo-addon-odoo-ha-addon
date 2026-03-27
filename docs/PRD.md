# WOOW Dashboard - Product Requirements Document

**Product Name**: WOOW Dashboard
**Version**: 18.0.6.2
**Platform**: Odoo 18 (Community & Enterprise)
**Category**: WOOW/Extra Tools
**License**: LGPL-3
**Last Updated**: 2026-03-27

---

## 1. Executive Summary

WOOW Dashboard is an Odoo 18 addon that bridges Home Assistant (HA) IoT infrastructure with the Odoo ERP platform. It enables organizations to monitor, control, and share IoT device data directly within the Odoo user interface. The addon connects to one or more Home Assistant instances via REST API and persistent WebSocket connections, synchronizes entities, devices, areas, and labels into Odoo models, and provides real-time state streaming, historical charting, device control, portal sharing, and system monitoring -- all governed by a two-tier permission model.

The product targets facility managers, building operations teams, and system integrators who need centralized IoT visibility alongside their existing Odoo business workflows.

---

## 2. Product Overview

### 2.1 Problem Statement

Organizations using Home Assistant for IoT management alongside Odoo for business operations face fragmented dashboards, duplicated access control, and no unified audit trail. Operators must switch between systems, and sharing device access with external stakeholders requires granting direct HA credentials.

### 2.2 Solution

WOOW Dashboard embeds the full Home Assistant monitoring and control experience inside Odoo, leveraging Odoo's native user management, portal system, permission groups, and notification infrastructure. It provides:

- Real-time bidirectional synchronization with Home Assistant
- Granular permission-based access for internal users and portal guests
- 10 domain-specific device controllers covering the most common HA entity types
- Historical data charting for trend analysis
- A Glances system-monitoring dashboard for server health
- Blueprint automation wizard for creating HA automations from within Odoo

### 2.3 Dependencies

| Dependency | Purpose |
|---|---|
| `base` | Core Odoo framework |
| `web` | Web client, OWL component system, bus service |
| `mail` | Activity notifications for share expiry alerts |
| `portal` | Portal page infrastructure for external sharing |
| `websockets` (Python) | WebSocket client library (auto-installed via `pre_init_hook`) |
| `pypinyin` (Python) | Chinese character to pinyin conversion for entity ID generation |

---

## 3. Target Users

### 3.1 HA Manager (Administrator)

- Configures Home Assistant instances (API URL, long-lived access token)
- Triggers registry sync (entities, devices, areas, labels)
- Manages entity groups, tags, and organizational structure
- Controls WebSocket service lifecycle (start/stop/restart)
- Shares entities, groups, and devices with internal users and portal users
- Creates automations and scenes via the Blueprint Wizard

### 3.2 HA User (Operator)

- Views entities within authorized entity groups
- Monitors real-time state changes on dashboards
- Controls devices within authorized scope
- Browses area dashboards and Glances system monitors
- Views entity history charts

### 3.3 Portal User (External Guest)

- Receives share invitations from HA Managers
- Views and optionally controls shared entities via the `/my/ha` portal
- Interacts through a simplified IoT-style portal interface
- Access automatically expires based on configurable expiry dates

---

## 4. Feature Specifications

### 4.1 Home Assistant Integration

#### Description

The core connectivity layer establishes and maintains communication with Home Assistant instances through two channels: REST API for synchronous operations and WebSocket for real-time event streaming.

#### User Stories

- As an HA Manager, I can add a new HA instance by providing its API URL and long-lived access token so that Odoo can communicate with my HA server.
- As an HA Manager, I can test the connection to verify both REST API and WebSocket connectivity before activating the instance.
- As an HA Manager, I can trigger a full registry sync to import all entities, devices, areas, and labels from HA into Odoo.

#### Technical Details

**REST API Client** (`models/common/hass_rest_api.py`):
- HTTP GET/POST calls to HA REST API endpoints
- Used for entity state fetching, history retrieval, and service calls
- Configurable timeouts via `ws_config.py` (default: 10s REST, 30s for service execution)

**WebSocket Service** (`models/common/hass_websocket_service.py`, 3010 lines):
- Persistent async WebSocket connection per HA instance
- Authentication handshake with HA long-lived access token
- Event subscription for: `state_changed`, `device_registry_updated`, `area_registry_updated`, `entity_registry_updated`, `label_registry_updated`
- Configurable heartbeat interval for connection health monitoring
- Automatic reconnection with exponential backoff (5 retry attempts)
- Debounced sync for rapid-fire registry events (area, device)

**WebSocket Thread Manager** (`models/common/websocket_thread_manager.py`):
- Manages background threads for WebSocket services across all active instances
- Supports multi-database deployments
- Automatic startup via `post_load_hook` on Odoo restart
- Cron-based health monitor runs every 1 minute to ensure service uptime

**Cross-Process Request Queue** (`ha.ws.request.queue` model):
- Database-backed queue for WebSocket API requests from Odoo HTTP workers
- Enables Odoo's multi-process architecture to communicate with the single-process WebSocket event loop
- Request lifecycle: `pending` -> `processing` -> `done` / `timeout` / `failed`
- Automatic cleanup of stale requests

**Timeout Configuration** (`models/common/ws_config.py`):
- Centralized timeout constants for all operations
- Categories: connection (5s), API requests (10-15s), registry operations (10-15s), service calls (10-15s), history (60-90s)

---

### 4.2 Multi-Instance Support

#### Description

A single Odoo database can connect to multiple Home Assistant instances simultaneously. Each instance maintains its own WebSocket connection, entity pool, device registry, and area hierarchy. Users access instance-scoped data based on entity group authorization.

#### User Stories

- As an HA Manager, I can add multiple HA instances (e.g., office, warehouse, retail) and manage them from a single Odoo installation.
- As an HA Manager, I can switch between instances using the instance dashboard entry page.
- As an HA User, I only see entities from instances where I have been granted access via entity groups.

#### Technical Details

**Instance Model** (`ha.instance`):
- Fields: `name`, `api_url`, `api_token`, `active`, `ws_url` (computed), `ws_heartbeat_interval`
- Sync timestamps: `last_entity_sync`, `last_area_sync`, `last_device_sync`, `last_label_sync`
- Instance fingerprint for change detection
- Connection test action covering both REST and WebSocket

**Instance Selection Priority** (`models/common/instance_helper.py`):
1. Session-stored instance ID (set by explicit switch)
2. User's preferred instance (from `res.users` preference field)
3. First accessible instance (based on permissions)

**Current Instance Filter Mixin** (`models/common/mixins.py`):
- `HACurrentInstanceFilterMixin` automatically filters queries to the active instance
- Applied to `ha.entity`, `ha.area`, `ha.device`, `ha.label`, and related models
- Portal controllers use `sudo()` to bypass this filter for cross-instance share lookups

**Instance Dashboard** (frontend action):
- Entry page showing all accessible instances as cards
- Entity count and area count per instance
- Quick navigation to instance-specific views

---

### 4.3 Entity Management

#### Description

Entities are the core data unit, representing any HA entity (sensor, switch, light, etc.). They are synchronized from HA and presented through list, kanban, form, and custom history views with real-time state updates.

#### User Stories

- As an HA User, I can browse all entities assigned to my groups in a list or kanban view with live state indicators.
- As an HA User, I can view the history of an entity as a time-series chart.
- As an HA User, I can control supported entities (toggle switches, adjust brightness, set temperature) directly from the Odoo interface.
- As an HA Manager, I can organize entities into groups with tags for logical categorization.

#### Technical Details

**Entity Model** (`ha.entity`, 2311 lines):
- Core fields: `entity_id` (HA string ID), `name`, `domain`, `entity_state`, `attributes` (JSON), `last_changed`
- Relationships: `ha_instance_id`, `area_id`, `device_id`, `group_ids` (many2many), `tag_ids` (many2many)
- Scene-specific fields: `scene_entity_ids`, `ha_scene_id`, `blueprint_path`, `blueprint_inputs`
- Bidirectional sync: area assignment, name changes, and label changes propagate to HA
- Entity creation for scenes: generates `entity_id` from name using pinyin conversion

**Entity Group Model** (`ha.entity.group`):
- Fields: `name`, `description`, `entity_ids` (many2many), `tag_ids` (many2many), `user_ids` (many2many)
- Core permission boundary: users access entities only through authorized groups
- Instance-scoped: all entities in a group must belong to the same instance

**Entity Tags** (`ha.entity.tag`):
- Many2many tagging for entity organization
- Color and sequence fields for UI display

**Entity Group Tags** (`ha.entity.group.tag`):
- Separate tagging system for groups
- Color-coded with configurable display order

**Supported Entity Domains** (10 controllers):

| Domain | Controller Capabilities |
|---|---|
| `switch` | Toggle on/off |
| `light` | Toggle, brightness slider, color temperature |
| `sensor` | Read-only value display (numeric and binary) |
| `climate` | Temperature set point, HVAC mode, fan mode |
| `cover` | Open/close/stop, position slider |
| `fan` | Toggle, speed percentage, preset mode, direction, oscillation |
| `automation` | Toggle enable/disable, manual trigger |
| `scene` | Activate button |
| `script` | Execute, toggle on/off |
| `generic` | Fallback for unsupported domains |

**Entity Controller Architecture** (frontend):
- Shared hook `useEntityControl` provides domain-agnostic control logic
- `EntityController` OWL component renders domain-specific templates
- `buildActionsFromConfig` helper constructs action definitions declaratively
- Same hook powers both backend and portal controllers

**Custom Views**:
- **Entity Kanban View**: Real-time entity cards with inline controls, extending Odoo's standard kanban
- **HAHistory View**: Custom OWL view type (Model -> Renderer -> ArchParser -> Controller -> View) for entity history charting using `UnifiedChart`

---

### 4.4 Entity History & Charting

#### Description

Entity history records are fetched from HA and stored locally for charting and analysis. A custom HAHistory view type renders time-series data using Chart.js through the UnifiedChart component.

#### User Stories

- As an HA User, I can view the state history of any entity over time as a line chart.
- As an HA Manager, I can trigger a history sync to pull historical data from HA into Odoo.

#### Technical Details

**History Model** (`ha.entity.history`):
- Fields: `entity_id` (FK), `entity_state`, `num_state` (computed numeric), `last_changed`, `entity_id_string`
- Dual fetch paths: WebSocket subscription stream (preferred) or REST API fallback
- Parallel history sync with configurable thread pool (ThreadPoolExecutor)
- Batch deduplication to prevent duplicate records on re-sync

**Chart Service** (frontend, `services/chart_service.js`):
- Lifecycle management for Chart.js instances
- `destroyChart()` must be called before creating new instances to prevent memory leaks

**UnifiedChart Component** (frontend):
- Wraps Chart.js with Odoo OWL integration
- Supports line, bar, and other chart types
- Used by HAHistory renderer and dashboard widgets

---

### 4.5 Device & Area Management

#### Description

Devices and areas are synchronized from HA's device and area registries. Areas serve as the organizational hierarchy for the area-based dashboard. Both support bidirectional sync -- changes in Odoo propagate back to HA.

#### User Stories

- As an HA Manager, I can view all HA devices with their manufacturer, model, and firmware information.
- As an HA User, I can browse the area dashboard to see devices organized by physical location.
- As an HA Manager, I can create, rename, or delete areas in Odoo and have those changes sync to HA.

#### Technical Details

**Area Model** (`ha.area`, bidirectional sync):
- Fields: `area_id` (HA string ID), `name`, `ha_instance_id`
- Odoo-to-HA sync: `create` -> `config/area_registry/create`, `write` -> `config/area_registry/update`, `unlink` -> `config/area_registry/delete`
- HA-to-Odoo sync: WebSocket `area_registry_updated` events with debounced processing
- Initial sync on WebSocket connection startup

**Device Model** (`ha.device`, 821 lines):
- Fields: `device_id`, `name`, `manufacturer`, `model`, `sw_version`, `hw_version`, `via_device_id`
- Computed relations: `related_automation_ids`, `related_script_ids`, `related_scene_ids`
- Device tags for custom organization
- Bidirectional name/area sync with HA device registry
- Cron job syncs related items (automations, scripts, scenes) every 15 minutes

**Label Model** (`ha.label`):
- Synced from HA label registry
- Bidirectional sync: create/update/delete propagates to HA
- Used for entity and device categorization

**Area Dashboard** (frontend action):
- Device-card based layout grouped by area
- Standalone entity cards for unassigned entities
- Real-time state updates via bus notifications

---

### 4.6 Glances System Monitoring

#### Description

The Glances integration auto-discovers Glances monitoring agents registered as HA devices and presents CPU, memory, disk, and network metrics in a dedicated dashboard.

#### User Stories

- As an HA User, I can see all Glances-monitored servers in the HA Info dashboard.
- As an HA User, I can drill into a specific server to view CPU, memory, disk, and network entity groups with color-coded status.

#### Technical Details

**Backend API Endpoints**:
- `/odoo_ha_addon/glances_devices`: Discovers Glances devices from HA device registry (filters by `integration: glances`)
- `/odoo_ha_addon/glances_device_entities`: Fetches device entities grouped by type (CPU, memory, disk, network, etc.)

**Frontend Components**:
- `GlancesBlock`: Device card component for the HA Info dashboard overview
- `GlancesDeviceDashboard`: Full-page action with entity type grouping and color-coded status indicators

**Cache Management**:
- Event-driven invalidation: Glances cache clears when `device_registry_updated` events arrive
- Prevents stale data when devices are added or removed

---

### 4.7 Portal Sharing System

#### Description

The portal sharing system allows HA Managers to share individual entities, entity groups, and devices with Odoo portal users (external guests) or internal users. Access is controlled through `ha.entity.share` records with configurable permission levels and optional expiration.

#### User Stories

- As an HA Manager, I can share an entity or group with a specific user at either "View Only" or "Can Control" permission level.
- As an HA Manager, I can set an expiry date on shares and receive notifications 7 days before expiry.
- As a Portal User, I can view all items shared with me at `/my/ha` organized by HA instance.
- As a Portal User with "Control" permission, I can toggle switches, adjust brightness, and control devices from the portal interface.

#### Technical Details

**Share Model** (`ha.entity.share`):
- Target (mutually exclusive): `entity_id`, `group_id`, or `device_id`
- Fields: `user_id`, `permission` (view/control), `expiry_date`, `notification_sent`
- SQL constraints enforce mutual exclusivity and unique user combinations
- Computed `ha_instance_id` derived from the shared target
- Helper methods: `get_shares_for_user()`, `get_shared_entities_for_user()`, `get_shared_groups_for_user()`, `get_shared_devices_for_user()`

**Share Wizard** (`ha.entity.share.wizard`):
- TransientModel for batch sharing with multiple users
- Context-aware defaults from entity/group/device form views
- Duplicate detection: updates existing shares instead of creating duplicates

**Portal Controller** (`controllers/portal.py`, 897 lines):
- All routes use `auth='user'` requiring Odoo login
- Routes:
  - `/my/ha` -- Share overview page with instance navigation
  - `/my/ha/<instance_id>` -- Instance-specific shares with entity/group tabs
  - `/portal/entity/<id>` -- Entity detail page with live status
  - `/portal/entity/<id>/state` -- JSON polling endpoint for real-time updates
  - `/portal/call-service` -- Service call endpoint with permission and whitelist validation
  - `/portal/entity_group/<id>` -- Group detail page with entity grid
  - `/portal/entity_group/<id>/state` -- Group entities state polling
  - `/portal/device/<id>` -- Device detail page
  - `/portal/device/<id>/state` -- Device entities state polling

**Portal Frontend Components** (OWL, registered as `public_components`):
- `PortalEntityController`: Renders domain-specific controls using shared `usePortalEntityControl` hook
- `PortalEntityInfo`: Entity info card with auto-polling state refresh
- `PortalGroupInfo`: Group info with entity table display
- `PortalLiveStatus`: Sidebar component showing real-time entity state

**Portal Styling**:
- CSS Custom Properties theme system
- IoT-style toggle switches for binary controls
- Value sliders for brightness/speed/position
- Responsive breakpoints with touch target optimization
- WCAG AA color contrast compliance

**Expiry Management** (cron jobs):
- Daily: `_cron_check_expiring_shares()` -- sends mail.activity notifications 7 days before expiry
- Weekly: `_cron_cleanup_expired_shares()` -- removes shares expired for 30+ days

---

### 4.8 Real-Time Architecture

#### Description

The real-time data pipeline propagates HA state changes from the WebSocket service through the Odoo bus to connected browser clients with sub-second latency.

#### User Stories

- As an HA User, I see entity state changes reflected in my dashboard within seconds, without manual refresh.
- As a Portal User, I see live status updates on shared entity pages.

#### Technical Details

**Data Flow**:
```
HA WebSocket -> HassWebSocketService -> Odoo Models (write)
                                     -> ha.realtime.update -> Odoo Bus -> Browser
```

**HaBusBridge** (frontend service, `services/ha_bus_bridge.js`):
- Subscribes to Odoo bus channels for HA notification types
- Notification types: `ha_entity_state_changed`, `ha_websocket_status`, `ha_instance_invalidated`, `ha_instance_fallback`, `ha_instance_switched`, `ha_device_registry_update`, `ha_area_registry_update`
- Dispatches events to frontend components via reactive state management

**ha.realtime.update Model**:
- Inherits `bus.listener.mixin` for Odoo bus integration
- Methods: `notify_entity_state_change()`, `notify_ha_websocket_status()`, `notify_instance_invalidated()`, `notify_instance_fallback()`, `notify_instance_switched()`, `notify_device_registry_update()`, `notify_area_registry_update()`

**Frontend Data Service** (`services/ha_data_service.js`):
- Centralized RPC proxy for all backend API calls
- Caching layer with event-driven invalidation
- Methods for areas, entities, instances, Glances devices, entity related info, and service calls

**Key Pattern**: Frontend components must use `useService("ha_data")` and subscribe via `bus_service.subscribe()`. Direct RPC calls and `useBus()` hooks are prohibited to maintain consistency.

---

### 4.9 Internationalization (i18n)

#### Description

The addon provides complete Traditional Chinese (zh_TW) translation coverage alongside the English source strings. All user-facing strings in Python, JavaScript, and QWeb templates are marked for translation.

#### User Stories

- As a Taiwanese user, I can use the full addon interface in Traditional Chinese.
- As a developer, I can add new translatable strings following established patterns.

#### Technical Details

**Translation Files**:
- `i18n/odoo_ha_addon.pot` -- Source template
- `i18n/zh_TW.po` -- Traditional Chinese translations (100% coverage)

**Translation Patterns**:

| Context | Method | Example |
|---|---|---|
| Python | `_()` | `_("Entity not found")` |
| JavaScript/OWL | `_t()` | `_t("Loading...")` |
| QWeb XML templates | Automatic | `<span>Hello</span>` (auto-extracted) |
| XML string attributes | Automatic | `string="Entity Name"` |

---

### 4.10 Security Model

#### Description

The addon implements a two-tier permission system inspired by Odoo's Point of Sale module, combined with field whitelists and service whitelists for portal data exposure control.

#### Permission Groups

| Group | Internal ID | Capabilities |
|---|---|---|
| **HA User** | `group_ha_user` | Read-only access to authorized entity groups and their data |
| **HA Manager** | `group_ha_manager` | Full CRUD on instances, entities, areas, devices, labels, groups, tags; implies HA User |

#### Record Rules (14 rules)

| # | Model | Group | Access | Scope |
|---|---|---|---|---|
| 1 | `ha.instance` | HA User | Read | Instances reachable via user's entity groups |
| 2 | `ha.instance` | HA Manager | Full CRUD | All instances |
| 3 | `ha.entity` | HA User | Read | Entities in user's authorized groups |
| 4 | `ha.entity` | HA Manager | Read | All entities (write via WebSocket sync only) |
| 5 | `ha.entity.history` | HA User | Read | History for entities in authorized groups |
| 6 | `ha.entity.history` | HA Manager | Full CRUD | All history |
| 7 | `ha.area` | HA User | Read | Areas of instances reachable via groups |
| 8 | `ha.area` | HA Manager | Full CRUD | All areas |
| 9 | `ha.entity.group` | HA User | Full CRUD | Public groups OR groups assigned to user |
| 10 | `ha.entity.group` | HA Manager | Full CRUD | All groups |
| 11-12 | `ha.entity.group.tag` | User/Manager | Read / Full | Tags reachable via groups / All tags |
| 13-14 | `ha.entity.tag` | User/Manager | Read / Full | Tags on authorized entities / All tags |

#### Portal Security

- **Authentication**: All portal routes require `auth='user'` (Odoo login)
- **Access control**: Verified via `ha.entity.share` records; expired shares return 403
- **Field whitelists**: `PORTAL_ENTITY_FIELDS` (8 fields), `PORTAL_GROUP_FIELDS` (5 fields)
- **Attribute sanitization**: `PORTAL_SENSITIVE_ATTRIBUTE_KEYS` blocklist strips `access_token`, `password`, `ip_address`, `mac_address`, `latitude`, `longitude`, and other sensitive keys
- **Service whitelist**: `PORTAL_CONTROL_SERVICES` dict restricts which HA services can be called per domain from portal
- **sudo() discipline**: Used only for read operations; never for write

#### API Token Protection

- HA API tokens stored in `ha.instance` model, accessible only to HA Manager group
- Tokens never exposed in debug logs or frontend responses
- WebSocket authentication uses token only within the server-side async connection

---

### 4.11 Blueprint Wizard

#### Description

The Blueprint Wizard allows HA Managers to create new HA automations and scripts from within Odoo using existing HA blueprints. The wizard dynamically generates a form based on the blueprint's input schema.

#### User Stories

- As an HA Manager, I can browse available blueprints from HA, select one, fill in the inputs, and create a new automation or script.
- As an HA Manager, I can see the dynamically generated form fields based on the blueprint's schema.

#### Technical Details

**Wizard Model** (`ha.blueprint.wizard`, TransientModel):
- Three-step flow: select domain -> select blueprint -> configure inputs -> create
- Fields: `ha_instance_id`, `domain` (automation/script), `blueprint_path`, `blueprint_inputs` (JSON), `name`
- Fetches blueprint list from HA via WebSocket (`config/automation/config/list` / blueprint API)
- Dynamically constructs HA service call data from wizard inputs

**Frontend Widgets**:
- `BlueprintSelector`: Custom OWL widget for browsing and selecting blueprints
- `BlueprintInputs`: Dynamic form generation from blueprint input schema (JSON schema -> form fields)

---

### 4.12 Custom OWL Views & Components

#### Description

The addon extends Odoo's OWL framework with custom view types and reusable components that go beyond standard list/form/kanban views.

#### HAHistory View

Custom view type implementing the full Odoo view architecture:
- `HaHistoryModel`: Data model fetching history records and preparing chart datasets
- `HaHistoryRenderer`: Renders the chart UI using `UnifiedChart`
- `HaHistoryArchParser`: Parses the view's XML arch definition
- `HaHistoryController`: Coordinates model, renderer, and search panel
- `HaHistoryView`: Registers the view type with Odoo's view registry

#### Entity Kanban View

Extended kanban view with real-time entity controls:
- `EntityKanbanController`: Injects real-time update handling into the standard kanban
- `EntityKanbanView`: Registered as a custom view type

#### Reusable Components

| Component | Purpose |
|---|---|
| `UnifiedChart` | Chart.js wrapper for all chart rendering |
| `HaChart` / `LineChart` | Specialized chart variants |
| `DashboardItem` | Card container for dashboard widgets |
| `InstanceSelector` | Instance picker dropdown |
| `EntityController` | Domain-specific device control panel |
| `DeviceCard` | Device summary card for area dashboard |
| `StandaloneEntityCard` | Entity card for unassigned entities |
| `GlancesBlock` | Glances device summary for info dashboard |
| `RelatedEntityDialog` | Modal showing entity's related automations/scripts/scenes |
| `EntityDemo` | Development/testing wrapper for entity controller |

---

## 5. Architecture Overview

### 5.1 Backend Architecture

```
Odoo Models Layer
  ha.instance            -- HA server connection configuration
  ha.entity              -- Synchronized HA entities (800+ per instance)
  ha.entity.history      -- Time-series state history
  ha.entity.group        -- User-defined entity groupings (permission boundary)
  ha.entity.group.tag    -- Group tags
  ha.entity.tag          -- Entity tags
  ha.area                -- HA area registry (bidirectional sync)
  ha.device              -- HA device registry
  ha.device.tag          -- Device tags
  ha.label               -- HA label registry (bidirectional sync)
  ha.entity.share        -- Share records for portal access
  ha.ws.request.queue    -- Cross-process WebSocket request queue
  ha.realtime.update     -- Bus notification dispatcher
  ha.blueprint.wizard    -- Transient model for blueprint creation

Common Utilities
  hass_rest_api.py       -- REST API client
  hass_websocket_service.py  -- WebSocket event loop (3010 lines)
  websocket_client.py    -- Synchronous WebSocket API wrapper
  websocket_thread_manager.py  -- Background thread lifecycle
  instance_helper.py     -- Session-based instance resolution
  mixins.py              -- HACurrentInstanceFilterMixin
  ws_config.py           -- Centralized timeout configuration
  utils.py               -- Date parsing, domain extraction helpers

Controllers
  controllers.py         -- Backend JSON-RPC API (18 endpoints)
  portal.py              -- Portal routes (12 endpoints)
```

### 5.2 Frontend Architecture

```
Services
  ha_data_service.js     -- Centralized RPC proxy with caching
  chart_service.js       -- Chart.js lifecycle management
  ha_bus_bridge.js       -- Odoo bus -> component event dispatch

Hooks
  entity_control/core.js     -- Shared control logic
  entity_control/domain_config.js  -- Domain-specific configurations
  entity_control/index.js    -- Export barrel

Views
  hahistory/             -- Custom HAHistory view type (5 files)
  entity_kanban/         -- Extended kanban with real-time controls (3 files)

Actions
  ha_instance_dashboard/ -- Instance entry page
  dashboard/             -- HA Info overview dashboard
  area_dashboard/        -- Area-based device dashboard
  glances_device_dashboard/  -- Glances server detail page

Components
  entity_controller/     -- 10 domain-specific controller templates
  charts/                -- UnifiedChart, HaChart, LineChart
  device_card/           -- Area dashboard device cards
  glances_block/         -- Glances overview cards
  blueprint_wizard/      -- Blueprint selector and inputs widgets
  instance_selector/     -- Instance picker
  related_entity_dialog/ -- Entity relation modal
  dashboard_item/        -- Generic dashboard card container

Portal (web.assets_frontend)
  portal_entity_service.js      -- Token-free user-based API client
  portal_entity_controller.js   -- Portal device controls (10 domains)
  portal_entity_info.js         -- Entity info card with polling
  portal_group_info.js          -- Group info with entity table
  portal_live_status.js         -- Sidebar live status component
  hooks/usePortalEntityControl.js  -- Portal-specific control hook
```

### 5.3 Data Flow Diagram

```
                    ┌─────────────────┐
                    │  Home Assistant  │
                    │    Instance(s)   │
                    └────┬───────┬────┘
                         │       │
                    REST API   WebSocket
                         │       │
              ┌──────────┘       └──────────┐
              ▼                              ▼
     ┌─────────────┐             ┌───────────────────┐
     │  Sync Jobs   │             │  HassWebSocket    │
     │  (on demand) │             │  Service (async)  │
     └──────┬──────┘             └─────────┬─────────┘
            │                              │
            ▼                              ▼
     ┌─────────────────────────────────────────────┐
     │              Odoo Models                     │
     │  ha.entity, ha.area, ha.device, ha.label    │
     │  ha.entity.history, ha.entity.group         │
     └──────┬─────────────────────────────┬────────┘
            │                             │
            ▼                             ▼
     ┌──────────────┐          ┌──────────────────┐
     │  Controllers  │          │ ha.realtime.update│
     │  (JSON-RPC)   │          │  -> Odoo Bus     │
     └──────┬───────┘          └────────┬─────────┘
            │                           │
            ▼                           ▼
     ┌──────────────────────────────────────────┐
     │            Browser (OWL Frontend)         │
     │  ha_data_service -> Components/Views      │
     │  ha_bus_bridge -> Real-time Updates        │
     └──────────────────────────────────────────┘
```

---

## 6. Non-Functional Requirements

### 6.1 Performance

- WebSocket heartbeat monitor runs every 1 minute (cron)
- Device related items sync runs every 15 minutes (cron)
- History sync supports parallel thread pool for multi-entity fetching
- PostgreSQL serialization conflict retry mechanism for concurrent area dashboard queries
- Event-driven cache invalidation prevents stale data without polling overhead
- Odoo cron worker 120-second hard limit respected; sync operations use individual sub-timeouts

### 6.2 Reliability

- WebSocket auto-reconnection with 5 retry attempts and exponential backoff
- Restart cooldown protection prevents rapid restart loops
- Graceful degradation: REST API fallback when WebSocket is unavailable
- Cross-process request queue survives Odoo worker restarts
- Comprehensive uninstall hook cleans up all data in correct dependency order (13 steps)

### 6.3 Scalability

- Tested with 800+ entities per instance
- Multi-instance support with independent WebSocket connections
- Batch operations for entity state updates, history deduplication, and registry sync
- ThreadPoolExecutor for parallel history fetching

### 6.4 Accessibility

- ARIA alert roles standardized across all interactive components
- State change animations support `prefers-reduced-motion`
- Touch target optimization for mobile portal users
- WCAG AA color contrast compliance (5.48:1 for primary action buttons)
- Font Awesome 4.x icons throughout (no FA5+ icons for Odoo compatibility)

### 6.5 Compatibility

- Odoo 18 Community and Enterprise editions
- Python 3.10+ (Odoo 18 requirement)
- `websockets` library v10.0+ (auto-installed)
- Home Assistant 2023.x+ (WebSocket API v2)
- Nginx reverse proxy with WebSocket upgrade support
- Docker Compose development environment included

### 6.6 Internationalization

- 100% zh_TW (Traditional Chinese) translation coverage
- Translation template (.pot) auto-generated from source
- All user-facing strings use proper i18n markers

---

## 7. Infrastructure & Deployment

### 7.1 Installation

1. Place addon in Odoo addons path
2. Update module list in Odoo
3. Install "WOOW Dashboard" from Apps menu
4. `pre_init_hook` auto-installs Python dependencies (`websockets`, `pypinyin`)
5. `post_init_hook` grants admin user HA Manager permissions
6. `post_load_hook` starts WebSocket services for all active instances on Odoo boot

### 7.2 Docker Compose Environment

- Odoo 18 container with addon mounted
- PostgreSQL database container
- Nginx reverse proxy with WebSocket upgrade support
- Worktree-based parallel development support (unique ports, isolated databases)

### 7.3 Cron Jobs

| Job | Model | Interval | Purpose |
|---|---|---|---|
| WebSocket Service Monitor | `ha.entity` | 1 minute | Ensures WebSocket service is running |
| Device Related Items Sync | `ha.device` | 15 minutes | Syncs automations, scripts, scenes per device |
| Check Expiring Shares | `ha.entity.share` | Daily | Notifies creators of shares expiring within 7 days |
| Cleanup Expired Shares | `ha.entity.share` | Weekly | Removes shares expired for 30+ days |

---

## 8. Testing

### 8.1 Unit & Integration Tests

| Test File | Coverage |
|---|---|
| `test_controllers.py` | Backend API controller tests |
| `test_entity_share.py` | Share model CRUD and constraints |
| `test_portal_controller.py` | Portal route integration tests |
| `test_portal_my_ha.py` | Portal /my/ha page tests |
| `test_portal_user_sharing.py` | End-to-end user sharing flow |
| `test_scene_area_sync.py` | Scene and area bidirectional sync |
| `test_security.py` | Permission and record rule tests |
| `test_share_permissions.py` | Share permission level enforcement |
| `test_share_wizard.py` | Share wizard batch operations |

### 8.2 Stability Tests

Located in `tests/stability/` for long-running reliability validation.

### 8.3 E2E Tests

Located in `tests/e2e_tests/` with Playwright MCP integration:
- Configuration in `e2e_config.yaml` with test entity definitions
- Covers all 10 domain controllers
- Tests both backend `entity_controller` and `portal_entity_controller` components

---

## 9. Release History

| Version | Date | Highlights |
|---|---|---|
| **18.0.6.2** | 2026-01-21 | Portal breadcrumbs, PortalLiveStatus, entity form control panel, attribute sanitization, group share fallback |
| **18.0.6.1** | 2026-01-18 | Token-to-user migration for portal, ha.entity.share model, share wizard, permission levels (view/control), expiry management, /my/ha portal |
| **18.0.6.0** | 2025-01-10 | Initial portal sharing (token-based), portal UI redesign (IoT-style), parallel history sync, Playwright E2E tests |
| **18.0.5.0** | 2025-12-03 | Glances dashboard integration, event-driven cache invalidation, device registry event subscription |
| **18.0.4.2** | 2025-11-27 | Multi-instance support, POS-style settings, group-based permissions, i18n (zh_TW), auto-install dependencies |
| **18.0.2.2** | 2025-10-28 | Layout fixes for dashboard and entity views |
| **18.0.2.1** | 2025-10-28 | Cover, fan, automation, scene, script controllers; network dashboard; PostgreSQL retry mechanism |
| **18.0.2.0** | 2025-10-22 | WebSocket integration, history streaming, HaBusBridge, entity groups/tags, device control, area dashboard |
| **18.0.1.1** | Prior | Initial release with basic REST API entity sync and dashboard |

---

## 10. Glossary

| Term | Definition |
|---|---|
| **Entity** | A single Home Assistant entity (e.g., `sensor.temperature`, `switch.office_light`) |
| **Domain** | The entity type prefix (e.g., `switch`, `light`, `sensor`, `climate`) |
| **Instance** | A configured connection to a Home Assistant server |
| **Entity Group** | An Odoo-side grouping of entities used as the permission boundary for HA Users |
| **Share** | An `ha.entity.share` record granting a specific user access to an entity, group, or device |
| **Blueprint** | A reusable automation/script template defined in Home Assistant |
| **Glances** | A cross-platform system monitoring tool that integrates with HA |
| **HAHistory** | The custom Odoo OWL view type for entity history charting |
| **HaBusBridge** | The frontend service that relays Odoo bus notifications to OWL components |
| **WebSocket Request Queue** | Database-backed queue enabling Odoo HTTP workers to communicate with the async WebSocket event loop |
