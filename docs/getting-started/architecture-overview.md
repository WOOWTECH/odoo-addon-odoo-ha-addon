# Architecture Overview for Beginners

A high-level introduction to the Odoo HA Addon architecture for new team members.

## What Does This Addon Do?

The Odoo HA Addon integrates Home Assistant (a popular home automation platform) with Odoo (an ERP system). It allows you to:
- View IoT device data in Odoo's interface
- Control smart home devices from within Odoo
- Monitor multiple Home Assistant instances
- Create dashboards showing real-time sensor data

## High-Level Architecture

```
┌─────────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Odoo Frontend      │  HTTP   │  Odoo Backend    │ WebSocket│ Home Assistant  │
│  (Browser/OWL)      │ ──────> │  (Python)        │<────────>│  (IoT Hub)      │
│                     │         │                  │          │                 │
│  - Dashboard UI     │         │  - Controllers   │          │  - Entities     │
│  - Charts           │         │  - Models        │          │  - Sensors      │
│  - Services         │         │  - WebSocket Svc │          │  - Switches     │
└─────────────────────┘         └──────────────────┘         └─────────────────┘
```

## Key Components

### 1. Frontend (What Users See)

**Location**: `static/src/`

**What it does**:
- Displays dashboard with IoT device data
- Shows charts and graphs
- Allows switching between multiple Home Assistant instances
- Provides controls to manipulate devices

**Key Technologies**:
- **OWL (Odoo Web Library)**: Component framework (like React/Vue)
- **Chart.js**: For displaying sensor data graphs
- **Services**: Reusable logic layer (like API clients)

**Example**:
```javascript
// Dashboard component shows hardware info
async loadHardwareInfo() {
  const result = await rpc("/odoo_ha_addon/hardware_info");
  this.state.data = result.data;
}
```

### 2. Backend (Business Logic)

**Location**: `models/`, `controllers/`

**What it does**:
- Connects to Home Assistant via WebSocket
- Stores entity data in PostgreSQL database
- Manages user permissions
- Provides HTTP APIs for frontend

**Key Components**:
- **Models**: Database tables (ha.entity, ha.instance, etc.)
- **Controllers**: HTTP endpoints that frontend calls
- **WebSocket Service**: Real-time connection to Home Assistant

**Example**:
```python
# Fetch entities from Home Assistant
def fetch_states(self):
    ws_client = HassWebSocketClient(self.env, instance_id)
    states = ws_client.get_states()
    # Store in database
```

### 3. Home Assistant (External Service)

**What it is**:
- Open-source home automation platform
- Manages IoT devices (lights, sensors, switches, etc.)
- Provides REST API and WebSocket API

**How we connect**:
- REST API: For simple requests (get entity list)
- WebSocket API: For real-time updates (entity state changes)

## Data Flow Example: Loading Dashboard

Let's trace what happens when you open the dashboard:

```
1. User opens Dashboard
   └─> Browser loads dashboard component

2. Component calls Service
   └─> haDataService.getHardwareInfo()

3. Service makes RPC call
   └─> rpc("/odoo_ha_addon/hardware_info")

4. Backend Controller receives request
   └─> @http.route('/odoo_ha_addon/hardware_info')

5. Controller gets current instance
   └─> instance_id = self._get_current_instance()
   └─> Uses session storage (like cookies)

6. Controller calls WebSocket service
   └─> ws_client = HassWebSocketClient(env, instance_id)
   └─> result = ws_client.get_hardware_info()

7. WebSocket service connects to Home Assistant
   └─> Opens WebSocket connection
   └─> Sends: {"type": "config/hardware_info"}
   └─> Receives: {"result": {...hardware data...}}

8. Backend returns data to frontend
   └─> return {"success": True, "data": result}

9. Frontend displays data
   └─> this.state.hardwareInfo = result.data
   └─> OWL re-renders component automatically
```

## Key Concepts for Developers

### 1. Multi-Instance Support

**Problem**: Users may have multiple Home Assistant setups (home, office, vacation home)

**Solution**:
- Each instance has its own connection, entities, and data
- User selects active instance via dropdown (Systray)
- Backend stores current instance in session (like a cookie)

**Priority Chain**:
```
1. Session (what user just selected)
2. User Preference (user's default choice)
3. First Accessible Instance (automatic fallback)
```

### 2. Security Model

**Two Permission Levels**:
1. **HA User** (`group_ha_user`): Can view authorized entities
2. **HA Manager** (`group_ha_manager`): Can manage everything

**Access Control**:
- Users access instances through **Entity Groups**
- Entity Groups act like "folders" of entities
- Administrators assign users to entity groups

**Example**:
```
User "John"
  └─ Has group_ha_user permission
  └─ Assigned to "Living Room Devices" entity group
  └─ Can see: Living room lights, thermostat
  └─ Cannot see: Bedroom devices, garage
```

### 3. Real-Time Updates

**Problem**: How does frontend know when entity state changes?

**Solution**: Odoo Bus Notification System

**Flow**:
```
1. Home Assistant WebSocket receives entity update
   └─> Light turned on

2. Backend broadcasts Odoo Bus notification
   └─> ha.realtime.update.notify_entity_state_change()

3. Frontend HaBusBridge receives notification
   └─> Subscribed via bus_service.subscribe()

4. Service distributes to components
   └─> haDataService.triggerGlobalCallbacks()

5. Component updates UI
   └─> useState() triggers automatic re-render
```

### 4. Session-Based Instance Selection

**Why?**: So frontend doesn't need to pass `instance_id` in every API call

**How it works**:
```python
# Backend stores in session
request.session['current_ha_instance_id'] = 5

# Frontend just calls API
await rpc("/odoo_ha_addon/hardware_info")
# Backend automatically uses instance_id from session
```

**Benefits**:
- Frontend code is simpler
- Consistent across all pages
- Automatic multi-tab synchronization

## Common Development Patterns

### 1. Creating a New Component

```javascript
// 1. Define component
class MyComponent extends Component {
  setup() {
    this.haData = useService("ha_data");
    this.state = useState({ data: null });

    // Subscribe to events
    this.instanceSwitched = (data) => this.reload();
    this.haData.onGlobalState('instance_switched', this.instanceSwitched);

    onWillUnmount(() => {
      this.haData.offGlobalState('instance_switched', this.instanceSwitched);
    });
  }

  async reload() {
    const result = await this.haData.getMyData();
    this.state.data = result;
  }
}

// 2. Register component
registry.category("actions").add("my_component", MyComponent);
```

### 2. Adding a New Backend Endpoint

```python
# 1. Add controller method
@http.route('/odoo_ha_addon/my_endpoint', type='json', auth='user')
def my_endpoint(self, **kwargs):
    # Get current instance (from session)
    instance_id = self._get_current_instance()

    # Call WebSocket API
    result = self._call_websocket_api(
        message_type="my_api_call",
        payload={},
        instance_id=instance_id
    )

    # Return standardized response
    return self._standardize_response({
        'success': True,
        'data': result
    })
```

### 3. Adding Real-Time Updates

```python
# Backend: Broadcast notification
self.env['ha.realtime.update'].notify_my_event(
    data={'entity_id': 'light.bedroom', 'state': 'on'}
)
```

```javascript
// Frontend: Subscribe to notification
this.haData.onGlobalState('my_event', (data) => {
  console.log('Event received:', data);
  this.updateUI(data);
});
```

## Project Structure

```
odoo_ha_addon/
├── models/               # Backend database models
│   ├── ha_entity.py     # Entity data model
│   ├── ha_instance.py   # Instance configuration
│   └── common/          # Shared utilities
│       ├── hass_rest_api.py          # REST API client
│       ├── hass_websocket_service.py # WebSocket client
│       └── instance_helper.py        # Instance selection logic
│
├── controllers/          # HTTP endpoints
│   └── controllers.py   # Main API routes
│
├── views/               # XML view definitions
│   ├── ha_entity_views.xml
│   └── ha_instance_views.xml
│
├── static/src/          # Frontend code
│   ├── services/        # Service layer
│   │   ├── ha_data_service.js    # Main API service
│   │   └── ha_bus_bridge.js      # Real-time notifications
│   ├── actions/         # Page components
│   │   └── dashboard/
│   ├── components/      # Reusable UI components
│   │   └── charts/
│   └── views/           # Custom view types
│
├── security/            # Access control
│   ├── security.xml     # Groups and rules
│   └── ir.model.access.csv  # Model permissions
│
└── data/                # Initial data
    └── menus.xml        # Menu structure
```

## Next Steps

Now that you understand the high-level architecture:

1. **Deep Dive into Architecture**: [../architecture/overview.md](../architecture/overview.md)
2. **Learn Development Patterns**: [../guides/development.md](../guides/development.md)
3. **Understand Security**: [../architecture/security.md](../architecture/security.md)
4. **Session Management**: [../architecture/session-instance.md](../architecture/session-instance.md)

## Quick Reference

### Useful Commands

```bash
# Start Odoo with development mode
./scripts/start-dev.sh
# 或
docker compose up

# Restart after Python changes
docker compose restart web

# Update addon
docker compose exec web odoo -d odoo -u odoo_ha_addon --dev xml

# View logs
docker compose logs -f web
```

### Important Files

| File | Purpose |
|------|---------|
| `models/common/instance_helper.py` | Instance selection logic (Single Source of Truth) |
| `controllers/controllers.py` | All HTTP API endpoints |
| `static/src/services/ha_data_service.js` | Frontend API service |
| `static/src/services/ha_bus_bridge.js` | Real-time event handling |
| `security/security.xml` | Permission configuration |

### Key Patterns

- **Service-First**: Always use `useService("ha_data")`, never direct RPC
- **Bus Notifications**: Use `bus_service.subscribe()`, NOT `useBus()`
- **Reactive State**: Use `useState()` for automatic re-render
- **Clean Up**: Always unsubscribe in `onWillUnmount()`

---

**Ready to start coding?** Check out the [Development Guide](../guides/development.md) for detailed patterns and examples.
