# Architecture Overview

This document describes the overall architecture of the Odoo HA Addon.

## Backend (Python)

### Models

Core entities for HA integration:

**Multi-Instance Support**:
- `ha.instance`: Manages multiple Home Assistant instances
  - Stores connection credentials (api_url, api_token)
  - Supports `test_connection()` via WebSocket
  - Batch restart WebSocket service
  - **Permission-based access**: Users access instances through authorized `ha.entity.group`
  - **No global default**: Each user gets first accessible instance (sorted by sequence, id)
- `res.users`: Extended with `current_ha_instance_id` for user preference

**Entity Models**:
- `ha.entity`: Stores Home Assistant entity states (multi-instance aware)
- `ha.entity.history`: Historical data tracking (related to entity's instance)
- `ha.area`: Home Assistant areas (multi-instance aware)
- `ha.entity.group`: Entity grouping (multi-instance aware with validation)
- `ha.entity.group.tag`: Group tags (multi-instance aware with validation)

**WebSocket Integration**:
- `ha.ws.request.queue`: WebSocket message queue (multi-instance aware)

**Notification System**:
- `ha.realtime.update` - Bus notification broadcaster
  - `notify_instance_invalidated()`: Notifies when session instance becomes invalid
  - `notify_instance_fallback()`: Notifies when system falls back to user preference or first accessible instance
  - `notify_instance_switched()`: Notifies all tabs when instance is switched
  - Inherits `bus.listener.mixin` for official Odoo 18 bus pattern

### API Integration

- `models/common/hass_rest_api.py` handles Home Assistant REST API communication

### Controllers

HTTP endpoints at `/odoo_ha_addon/*` for frontend data fetching:
- All endpoints use standardized response format: `{success: bool, data: dict, error: str}`
- `_standardize_response()` wrapper ensures consistent API responses
- `_validate_instance()` provides unified instance validation
  - Checks instance existence, active status, and configuration completeness
  - Returns structured error types: `instance_not_found`, `instance_inactive`, `instance_not_configured`
- `_get_current_instance()` sends Bus notifications on fallback

### Configuration

Settings stored in `ir.config_parameter` (ha_api_url, ha_api_token)

## Frontend (JavaScript/OWL)

### Service Layer

Centralized data and chart management:

**`services/ha_data_service.js`**: Home Assistant data API with caching
- Integrated Odoo notification service for automatic error/success notifications
- Depends on `notification` service for displaying toast messages
- Provides methods: `showSuccess()`, `showError()`, `showWarning()`, `showInfo()`
- Session invalidation handling via Bus notifications
- Multi-tab synchronization with 300ms debounce mechanism

**`services/chart_service.js`**: Chart.js instance management and optimization

### Actions

Action/page components:
- `actions/dashboard/`: Main dashboard action (registry.category("actions"))

### Views

View type implementations:
- `views/hahistory/`: Historical data view (registry.category("views"))
- `views/entity_kanban/`: Entity kanban view (registry.category("views"))

### Components

Reusable UI components:
- `components/charts/unified_chart/`: Modern unified chart component (primary)
- `components/charts/chart/`: Legacy chart components (ha_chart)
- `components/charts/line_chart/`: Legacy line chart components
- `components/dashboard_item/`: Individual dashboard widgets
- `components/entity_demo/`: Demo widgets for entities

### Utilities

- `util/debug.js`: Development debugging utilities

### Assets

All frontend assets bundled via `web.assets_backend` with optimized loading order

## Data Flow

1. HA entities synced via `fetch_states()` method (REST API and WebSocket)
2. Frontend components use `HaDataService` for all data requests with intelligent caching
3. `HaDataService` handles REST API calls to `/odoo_ha_addon/ha_data` and other endpoints
4. `ChartService` manages Chart.js instances to avoid performance issues
5. **Real-time updates flow**:
   - Backend events -> `ha.realtime.update.notify_*()` methods
   - Odoo Bus broadcasts to all user partner channels
   - `HaBusBridge` receives via `bus_service.subscribe()`
   - `HaDataService` triggers callbacks to subscribed components
   - Components re-render automatically via `useState()`
6. Updates displayed through unified chart components

## WebSocket Integration

The addon supports real-time updates through WebSocket connection to Home Assistant:

- **WebSocket Service**: `models/common/hass_websocket_service.py` manages WebSocket connections
- **Thread Manager**: `models/common/websocket_thread_manager.py` handles background processing
- **Queue System**: `models/ha_ws_request_queue.py` manages WebSocket message queuing
- **Auto-start**: WebSocket service starts automatically via `post_load_hook` in `hooks.py`
- **Dependencies**: Uses `websockets` library (auto-installed via `pre_init_hook`)

## Real-Time Bus Notification System

The addon implements Odoo 18's bus notification system for real-time backend-to-frontend communication using the **Bus Bridge Pattern**.

### Architecture Overview

**Backend -> Odoo Bus -> Frontend** flow:

1. Backend events (e.g., WebSocket status changes) trigger notifications
2. `ha.realtime.update` model broadcasts to all users via `bus.listener.mixin`
3. `HaBusBridge` component subscribes to all notification types
4. `HaDataService` distributes updates to components via callbacks
5. Components update reactively using `useState()`

### Key Components

**Backend (Python)**:

- **`models/ha_realtime_update.py`**:
  - Inherits `bus.listener.mixin` for official Odoo 18 bus pattern
  - Implements `_bus_channel()` returning user's partner_id (auto-subscribed)
  - Provides `_broadcast_to_users()` to send notifications to all online users
  - Methods: `notify_entity_state_change()`, `notify_ha_websocket_status()`, `notify_device_registry_update()`, `notify_instance_*()` (invalidated/fallback/switched)
  - **MUST be Model, not TransientModel** (bus.listener.mixin requirement)

**Frontend (JavaScript)**:

- **`static/src/services/ha_bus_bridge.js`**:
  - Centralized subscription point for ALL Odoo Bus events
  - Registered in `registry.category("main_components")` for auto-initialization
  - Uses `bus_service.subscribe()` (NOT `useBus()`) to receive backend notifications
  - Forwards events to `HaDataService` for distribution

- **`static/src/services/ha_data_service.js`**:
  - Implements callback system for components to subscribe to updates
  - Methods: `onGlobalState()`, `offGlobalState()`, `triggerGlobalCallbacks()`
  - Handles: `websocket_status`, `history_update`, `entity_update_all` events

### Critical Implementation Details

**Common Pitfalls**:

1. **NEVER use `useBus()` for backend notifications**
   - `useBus()` is only for OWL's frontend EventBus (`this.env.bus`)
   - Backend Odoo Bus requires `bus_service.subscribe()` + `busService.start()`

2. **Bus Channel Must Be Partner**
   - `_bus_channel()` MUST return `self.env.user.partner_id`
   - Partner channels are automatically subscribed by Odoo
   - To broadcast to all users, loop through users and send to each partner_id

3. **Model Type Matters**
   - `ha.realtime.update` MUST be `models.Model` (not TransientModel)
   - `bus.listener.mixin` requires persistent model for proper channel management

4. **WebSocket Proxy Required**
   - Nginx reverse proxy routes `/websocket` to gevent port 8072
   - Configuration in `data/nginx/odoo.conf`
   - Without proxy, `/bus/websocket_worker_bundle` connection fails

### Benefits of Bus Bridge Pattern

1. **No Duplicate Subscriptions**: Single subscription point prevents N*4 redundant listeners
2. **Reactive UI**: Components use `useState()` for automatic re-render
3. **Centralized Error Handling**: Service layer catches and logs all bus errors
4. **Clean Component Code**: Components only subscribe to service callbacks
5. **Easy Debugging**: All bus traffic logged in one place (HaBusBridge)

## Related Documentation

- **Bus Mechanisms**: [guides/bus-mechanisms.md](../guides/bus-mechanisms.md) - Complete guide to `useBus()` vs `bus_service.subscribe()`
- **Instance Switching**: [instance-switching.md](instance-switching.md) - Instance switching event handling patterns
- **Session Instance**: [session-instance.md](session-instance.md) - Session-based instance architecture
