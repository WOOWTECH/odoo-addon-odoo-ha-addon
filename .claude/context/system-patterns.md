---
created: 2026-01-01T15:23:16Z
last_updated: 2026-01-01T15:23:16Z
version: 1.0
author: Claude Code PM System
---

# System Patterns

## Architectural Style

### Multi-tier Architecture
```
┌─────────────────────────────────────────────────────┐
│                   Odoo Frontend                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Actions   │  │    Views    │  │ Components  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                │                │         │
│  ┌──────┴────────────────┴────────────────┴──────┐  │
│  │              Service Layer                     │  │
│  │    (ha_data_service, chart_service)           │  │
│  └─────────────────────────┬─────────────────────┘  │
└────────────────────────────┼────────────────────────┘
                             │ JSON-RPC
┌────────────────────────────┼────────────────────────┐
│  ┌─────────────────────────┴─────────────────────┐  │
│  │              Controllers (HTTP)               │  │
│  └─────────────────────────┬─────────────────────┘  │
│                            │                        │
│  ┌─────────────────────────┴─────────────────────┐  │
│  │                  Models                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐   │  │
│  │  │ Instance │ │  Entity  │ │InstanceHelper│   │  │
│  │  └────┬─────┘ └────┬─────┘ └──────┬───────┘   │  │
│  └───────┼────────────┼──────────────┼───────────┘  │
│          │            │              │              │
│  ┌───────┴────────────┴──────────────┴───────────┐  │
│  │           Common Utilities                     │  │
│  │  (WebSocket, REST API, Thread Manager)         │  │
│  └───────────────────────────────────────────────┘  │
│                    Odoo Backend                      │
└──────────────────────┬───────────────────────────────┘
                       │ WebSocket / REST
┌──────────────────────┴───────────────────────────────┐
│                  Home Assistant                       │
└──────────────────────────────────────────────────────┘
```

## Design Patterns

### 1. Service-First Pattern (Frontend)
- All data access through service layer
- Never call RPC directly from components
- Services manage caching and state

```javascript
// Correct
const haDataService = useService("ha_data");
const data = await haDataService.getEntities();

// Incorrect
await this.orm.call("ha.entity", "search_read", [...]);
```

### 2. Single Source of Truth (Instance Selection)
- `HAInstanceHelper` manages instance context
- Priority: Session → User Preference → First Accessible

```python
# models/common/instance_helper.py
class HAInstanceHelper:
    @classmethod
    def get_current_instance(cls, env):
        # 1. Check session
        # 2. Check user preference
        # 3. Return first accessible
```

### 3. Bus Notification Pattern (Real-time Updates)
- Use `bus_service.subscribe()` for notifications
- NOT `useBus()` hook (deprecated pattern)

```javascript
// Correct
this.busService.subscribe("ha_entity_update", this.onUpdate);

// Incorrect
useBus(this.bus, "ha_entity_update", this.onUpdate);
```

### 4. Reactive State Pattern
- Use `useState()` for component state
- Combine with service callbacks for reactivity

```javascript
setup() {
    this.state = useState({ entities: [], loading: true });
    this.haDataService.onUpdate((data) => {
        this.state.entities = data;
        this.state.loading = false;
    });
}
```

### 5. Component Composition Pattern
- Prefer composition over inheritance
- Use hooks for shared behavior

```javascript
// Hook pattern
export function useEntityControl(entity) {
    const haDataService = useService("ha_data");
    return {
        toggle: () => haDataService.callService(...),
        state: entity.state
    };
}
```

## Data Flow Patterns

### Entity State Update Flow
```
Home Assistant → WebSocket → ha_realtime_update → Bus → Frontend
                    │
                    └→ ha_entity_history (historical data)
```

### Instance Selection Flow
```
User Action → Session Store → HAInstanceHelper → All Components
                  │
                  └→ User Preference (persistent)
```

### Device Control Flow
```
UI Action → EntityController → ha_data_service → Controller → HA REST API
                                                      │
                                                      └→ WebSocket confirmation
```

## Security Patterns

### Two-tier Permission System
1. **Model-level:** Odoo ACL (ir.model.access)
2. **Instance-level:** Instance-based access control

```python
# Access check pattern
def _check_access(self):
    instance = HAInstanceHelper.get_current_instance(self.env)
    if not instance or instance.id not in self.allowed_instance_ids:
        raise AccessError(...)
```

### Session-based Instance Isolation
- Each user session has isolated instance context
- Cross-instance data access blocked at ORM level

## Error Handling Patterns

### Frontend Error Handling
```javascript
try {
    await this.haDataService.fetchData();
} catch (error) {
    this.notification.add(_t("Failed to fetch data"), { type: "danger" });
    debugWarn("Data fetch error:", error);
}
```

### Backend Error Handling
```python
from odoo.exceptions import UserError, AccessError

def action_sync(self):
    try:
        self._perform_sync()
    except ConnectionError as e:
        raise UserError(_("Failed to connect to Home Assistant: %s") % str(e))
```

## Caching Patterns

### Chart Service Caching
- Charts cached by canvas ID
- Explicit cleanup on component unmount

```javascript
// Cleanup pattern
onWillUnmount() {
    ChartService.destroyChart(this.chartId);
}
```

### Data Service Caching
- Entity data cached per-instance
- Invalidated on bus notifications

## Thread Management Patterns

### WebSocket Thread Pool
```python
# One WebSocket thread per instance
class WebSocketThreadManager:
    _threads = {}  # instance_id -> thread

    @classmethod
    def get_or_create(cls, instance):
        if instance.id not in cls._threads:
            cls._threads[instance.id] = cls._create_thread(instance)
        return cls._threads[instance.id]
```

### Cleanup on Uninstall
```python
def uninstall_hook(cr, registry):
    # Stop all WebSocket threads
    WebSocketThreadManager.stop_all()
```
