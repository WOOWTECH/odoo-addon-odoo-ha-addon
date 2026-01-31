# Development Guide

This document contains common development patterns and guidelines for the Odoo HA Addon.

## Adding New Entity Types

1. Create model inheriting from `ha.entity`
2. Add domain-specific fields and methods
3. Update `__init__.py` imports
4. Create corresponding views in `views/` directory
5. **Update `uninstall_hook`**: Add cleanup logic for new model (see below)

## Module Installation Hooks

The addon uses several hooks defined in `hooks.py` for lifecycle management:

### `pre_init_hook(cr)` - Auto-Install Dependencies

Automatically installs required Python packages before module installation:

```python
# hooks.py
def pre_init_hook(cr):
    # Auto-installs: websockets>=10.0
    # Uses --break-system-packages for Debian/Ubuntu compatibility
```

- Runs before Odoo loads the module
- Installs `websockets` library for Home Assistant WebSocket communication
- Fallback mechanism if `--break-system-packages` flag fails

### `post_init_hook(env)` - Auto-Grant Admin Permissions

Automatically grants HA Manager permissions to admin user after installation:

```python
# hooks.py
def post_init_hook(env):
    # Adds admin user (base.user_admin) to group_ha_manager
    # Ensures immediate access to HA settings after fresh install
```

- Runs after module is fully installed
- Follows Odoo best practices (similar to POS, Sales modules)
- Logs success/failure to Odoo logs for debugging

## Module Uninstallation Hook

**IMPORTANT**: When adding new models to the addon, you MUST update the `uninstall_hook()` in `hooks.py` to ensure complete data cleanup.

### Current Cleanup Order (10 steps)

The `uninstall_hook()` follows a strict dependency order to avoid foreign key constraint violations:

```python
# hooks.py:62-179
def uninstall_hook(env):
    # 1. Stop WebSocket services (background threads)
    # 2. Clear WebSocket request queue (ha.ws.request.queue)
    # 3. Clear historical data (ha.entity.history)
    # 4. Clear entity group tags (ha.entity.group.tag) - before groups
    # 5. Clear entity groups (ha.entity.group) - before entities
    # 6. Clear entities (ha.entity)
    # 7. Clear areas (ha.area)
    # 8. Clear realtime update records (ha.realtime.update)
    # 9. Clear HA instances (ha.instance) - LAST, all tables depend on this
    # 10. Clear config parameters (ir.config_parameter with odoo_ha_addon.*)
```

### Adding New Model Cleanup

When creating a new model with `ha_instance_id` foreign key:

1. **Identify dependency level**: Determine where your model fits in the dependency chain
2. **Insert cleanup step**: Add cleanup code in the correct position based on dependencies
3. **Follow the pattern**:
   ```python
   # X. Clean up your new model
   try:
       _logger.info("Step X/N: Cleaning [Model Description]...")
       records = env['your.model.name'].search([])
       count = len(records)
       records.unlink()
       _logger.info(f"Deleted {count} [model] records")
   except Exception as e:
       _logger.warning(f"Failed to clean [model]: {e}")
   ```
4. **Update step numbers**: Renumber all subsequent steps and update the header comment

### Dependency Rules

- **Child tables BEFORE parent tables**: Delete `ha.entity.group.tag` before `ha.entity.group`
- **Many2many relationships**: Delete junction table data before either side
- **`ha.instance` ALWAYS LAST**: It's the root dependency for all multi-instance tables
- **WebSocket service ALWAYS FIRST**: Stop background threads before data cleanup

### Testing Uninstallation

Always test the uninstall hook:

```bash
# 1. Install the addon with test data
docker compose -f docker-compose-18.yml exec web odoo -d odoo -i odoo_ha_addon

# 2. Create test records for all models

# 3. Uninstall and check logs
docker compose -f docker-compose-18.yml exec web odoo -d odoo --uninstall odoo_ha_addon

# 4. Verify all data is cleaned
```

## Frontend Component Development

- Follow OWL component structure with separate `.js` and `.xml` files
- Register components in main registry
- **Use services for data access**: `useService("ha_data")` for HA data, `useService("chart")` for charts
- **Avoid direct RPC calls**: All API communication should go through service layer
- Place components in organized subdirectories:
  - Views: `static/src/views/`
  - Reusable components: `static/src/components/`
  - Services: `static/src/services/`
  - Utilities: `static/src/util/`

## Chart Component Usage

| Aspect | Recommendation |
|--------|---------------|
| **Primary** | Use `UnifiedChart` component for all new chart implementations |
| **Import** | `import { UnifiedChart } from "../../components/charts/unified_chart/unified_chart"` |
| **Props** | `type` (string), `data` (object), `options` (object) |
| **Example** | `<UnifiedChart type="'line'" data="state.chartData" options="{}"/>` |
| **Legacy** | `ha_chart` and `line_chart` components exist for backwards compatibility |

## Real-Time Notifications

### Backend (Python)

Broadcast events to all frontend clients:

```python
# In any model method
self.env['ha.realtime.update'].notify_ha_websocket_status('connected', 'Service is online')
self.env['ha.realtime.update'].notify_entity_state_change(
    'sensor.temperature',
    old_state={'state': '21.0'},
    new_state={'state': '22.5'},
    ha_instance_id=1
)
```

### Frontend (JavaScript)

Subscribe to notifications in components:

```javascript
setup() {
  const haDataService = useService("ha_data");
  const state = useState({ status: 'unknown' });

  // Subscribe to service callback (NOT direct bus)
  const callback = (data) => {
    state.status = data.status;  // Triggers automatic re-render
  };
  haDataService.onGlobalState('websocket_status', callback);

  onWillUnmount(() => {
    haDataService.offGlobalState('websocket_status', callback);
  });
}
```

### Key Rules

- Components subscribe to `HaDataService` callbacks, never directly to bus
- Use `useState()` for automatic re-render, never manual DOM updates
- Always clean up subscriptions in `onWillUnmount()`

## Instance Switching Pattern

**Multi-Instance Support**: The addon supports multiple Home Assistant instances with seamless switching via Systray component.

**Event-Driven Architecture**: All components respond to `instance_switched` global event for automatic data reload.

```javascript
setup() {
  const haDataService = useService("ha_data");
  const state = useState({ data: null });

  // Subscribe to instance switch event
  this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
    console.log('Instance switched to', instanceName);
    this.reloadAllData();  // Reload component data
  };
  haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

  onWillUnmount(() => {
    haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
  });
}
```

**Critical Requirements**:

- **Always subscribe** to `instance_switched` if component displays instance-specific data
- **Always clean up** subscriptions in `onWillUnmount()` to prevent memory leaks
- **Reload all data** after instance switch, don't rely on cached data
- **Use reactive state** (`useState()`) for automatic UI updates

For detailed implementation guide, see **`docs/tech/instance-switching.md`**.

## Session-Based Instance Architecture

The addon uses a **Session-Based Implicit Instance** design where the current instance is stored in the user's session rather than passed explicitly in every API call.

### Instance Selection Priority

```python
# Backend: HAInstanceHelper.get_current_instance()
# Location: models/common/instance_helper.py
1. Session: request.session['current_ha_instance_id']
   | (if invalid, clear session + send Bus notification)
2. User Preference: res.users.current_ha_instance_id
   |
3. First Accessible Instance: get_accessible_instances()[0]
   | (ordered by sequence, id, filtered by user permissions via ir.rule)
```

### API Usage Patterns

**Pattern 1: Using Session (Recommended)**
```javascript
// Frontend - No parameters needed
async loadHardwareInfo() {
  const result = await rpc("/odoo_ha_addon/hardware_info");
}
```

**Pattern 2: Explicit Instance (Special cases)**
```javascript
async loadSpecificInstanceHardware(instanceId) {
  const result = await rpc("/odoo_ha_addon/hardware_info", {
    ha_instance_id: instanceId
  });
}
```

For comprehensive technical details, see **`docs/tech/session-instance.md`**.

## API Response Format Standard

All HTTP endpoints follow a unified response format:

**Success Response**:
```python
{
    'success': True,
    'data': {
        # Endpoint-specific data here
    }
}
```

**Error Response**:
```python
{
    'success': False,
    'error': 'Error message description'
}
```

**Implementation**:
- Backend: Use `_standardize_response()` wrapper for all `@http.route` endpoints
- Frontend: Access data via `result.data.*` and errors via `result.error`

## Development Guidelines

| Aspect | Guideline |
|--------|-----------|
| **File Paths** | All static assets must be in `/static/src/`, `/static/lib/`, or `/static/test/` |
| **Imports** | Use relative paths from component location (e.g., `"../../util/debug"`) |
| **Debug Usage** | Import from `"../../util/debug"` and use `debug()` for development logging |
| **Chart Implementation** | Always use `UnifiedChart` for new charts |
| **Service Integration** | Components should only use services, never direct API calls |
| **API Response Handling** | Always check `result.success` and access data via `result.data.*` |
| **Memory Management** | Properly destroy chart instances in component `willUnmount()` lifecycle |
| **Icon Usage** | Odoo 18 uses Font Awesome 4.x - only use FA4 compatible icons |

## Notification Usage

HaDataService automatically handles notifications for all API calls:

- **Automatic**: `switchInstance()`, `getInstances()`, `getAreas()`, `getEntitiesByArea()`, `callService()` automatically show error/success notifications
- **Manual**: Access notification methods via `haDataService.showSuccess()`, `showError()`, `showWarning()`, `showInfo()`
- **Silent Mode**: Use `callService(domain, service, data, { silent: true })` to suppress success notifications
- **No Manual Display Needed**: Components using HaDataService don't need to implement their own error UI
