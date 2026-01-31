# Session-Based Instance Architecture

## Overview

This document explains the Session-Based Instance architecture in the Odoo HA Addon and how to properly use this implicit instance selection mechanism. This architecture ensures clean frontend code while maintaining flexibility.

### Purpose

- **Simplify Frontend Calls**: API calls don't need to explicitly pass `instance_id` parameter in every request
- **Centralized State Management**: Instance selection state is managed by backend session
- **Automatic Fallback Mechanism**: When session is invalid or expired, automatically select a reasonable default instance

### Use Cases

- User operates on a single Home Assistant instance within a single page (most common)
- Need to maintain consistent instance selection across different pages
- Applications where instance switching is infrequent

---

## Architecture Design

### Session-Based vs Parameter-Based Comparison

#### Session-Based (Current Implementation)

```javascript
// Frontend - Simple
const result = await rpc("/odoo_ha_addon/hardware_info");
// No need to manage instanceId, backend uses session automatically
```

```python
# Backend - Automatic Selection
def get_hardware_info(self, ha_instance_id=None):
    # If ha_instance_id is None, read from session
    if ha_instance_id is None:
        ha_instance_id = self._get_current_instance()
```

**Pros**:
- ✅ Clean frontend code, no state management needed
- ✅ Single Source of Truth
- ✅ Follows web application conventions (similar to login state)

**Cons**:
- ❌ Implicit dependency, less readable code
- ❌ Multi-tab synchronization mechanism needed
- ❌ Cannot query multiple instances simultaneously

#### Parameter-Based (Alternative)

```javascript
// Frontend - Explicit but verbose
const result = await rpc("/odoo_ha_addon/hardware_info", {
  ha_instance_id: this.state.currentInstanceId  // Must pass every time
});
```

**Pros**:
- ✅ Explicitly shows which instance is being used
- ✅ Easier to test
- ✅ Can query multiple instances simultaneously

**Cons**:
- ❌ Frontend needs to manage currentInstanceId state
- ❌ High code duplication
- ❌ State synchronization needed across multiple components

### Hybrid Design (Best Practice)

**All API endpoints support both modes**:

```python
def get_hardware_info(self, ha_instance_id=None):
    """
    - If ha_instance_id provided: Use specified instance
    - If None: Use instance from session
    """
    result = self._call_websocket_api(..., instance_id=ha_instance_id)
```

```javascript
// Most cases: Use session (simple)
const result1 = await rpc("/odoo_ha_addon/hardware_info");

// Special cases: Explicitly specify instance (flexible)
const result2 = await rpc("/odoo_ha_addon/hardware_info", {
  ha_instance_id: 2
});
```

---

## Core Components

### 1. `_get_current_instance()` Method

Location: `controllers/controllers.py`

#### Priority Fallback Mechanism

```python
def _get_current_instance(self):
    """
    ⚠️ Architecture Update (2025-11-25): Removed is_default field, using permission-aware 3-level fallback

    Priority:
    1. current_ha_instance_id from Session
    2. User preference (res.users.current_ha_instance_id)
    3. First accessible instance (via get_accessible_instances(), filtered by ir.rule)

    Returns:
        int: HA instance ID, returns None if not found
    """
    from odoo.addons.odoo_ha_addon.models.common.instance_helper import HAInstanceHelper
    return HAInstanceHelper.get_current_instance(request.env, logger=self._logger)
```

#### Fallback Flow Diagram

```
⚠️ **Architecture Update (2025-11-25)**: Removed `is_default` field, using 3-level permission-aware fallback

┌─────────────────────┐
│ API Call            │
│ (ha_instance_id=None)│
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ 1. Check Session    │
│ current_ha_         │
│ instance_id         │
└──────────┬──────────┘
           │
      Valid?│
           ├─ Yes ──> Return Session Instance ID
           │
           └─ No
               │
               v
        ┌──────────────────────┐
        │ Clear Session +      │
        │ Send Bus Notification│
        └──────┬───────────────┘
               │
               v
        ┌──────────────────────┐
        │ 2. User Preference   │
        │ res.users.current_   │
        │ ha_instance_id       │
        └──────┬───────────────┘
               │
          Exists?│
               ├─ Yes ──> Return User Preference Instance ID
               │
               └─ No
                   │
                   v
            ┌────────────────────────┐
            │ 3. First Accessible    │
            │ Instance               │
            │ get_accessible_        │
            │ instances()[0]         │
            │ (filtered by ir.rule)  │
            └────────┬───────────────┘
                     │
                Exists?│
                     ├─ Yes ──> Return First Instance ID
                     │
                     └─ No ──> Return None
                                  │
                                  v
                           ┌──────────────┐
                           │ Error Response:│
                           │ "No active HA│
                           │  instance"   │
                           └──────────────┘
```

---

### 2. Session Storage Format

#### Session Structure

```python
# Odoo session (request.session)
{
    'uid': 2,  # User ID
    'login': 'admin',
    'current_ha_instance_id': 5,  # ← Target HA instance ID
    # ... other session data
}
```

#### Storage Location

- **Session Backend**: PostgreSQL or Redis (depends on Odoo configuration)
- **Table**: `http_session` (PostgreSQL)
- **Lifetime**: Based on Odoo `session_timeout` setting (default 7 days)

#### Set and Read

**Set Session**:

```python
# In switch_instance endpoint
request.session['current_ha_instance_id'] = instance.id
```

**Read Session**:

```python
# In any endpoint
session_instance_id = request.session.get('current_ha_instance_id')
```

**Clear Session**:

```python
# When instance is invalid
request.session.pop('current_ha_instance_id', None)
```

---

### 3. Frontend HaDataService Integration

Location: `static/src/services/ha_data_service.js`

#### Instance Switching Flow

```javascript
/**
 * Switch HA Instance
 * 1. Call backend API to update session
 * 2. Clear frontend cache
 * 3. Trigger global event
 */
async switchInstance(instanceId) {
  try {
    // Step 1: Update backend session
    const result = await rpc("/odoo_ha_addon/switch_instance", {
      instance_id: instanceId
    });

    if (result.success) {
      // Step 2: Clear cache (different instance data)
      this.clearCache();

      // Step 3: Trigger global event
      this.triggerGlobalCallbacks('instance_switched', {
        instanceId: instanceId,
        instanceName: result.data.instance_name
      });

      console.log(`[HaDataService] Switched to instance: ${result.data.instance_name}`);
    }

    return result;
  } catch (error) {
    console.error("Failed to switch instance:", error);
    throw error;
  }
}
```

#### Global Event System

```javascript
// Component subscribes to instance switch event
setup() {
  const haDataService = useService("ha_data");

  this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
    console.log('Instance switched to', instanceName);
    this.reloadAllData();  // Reload all data
  };

  haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

  onWillUnmount(() => {
    haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
  });
}
```

---

## API Usage Guide

### 8 Endpoints Supporting Session Instance

| Endpoint | Function | Parameters |
|----------|----------|------------|
| `/odoo_ha_addon/hardware_info` | Get hardware info | `ha_instance_id` (optional) |
| `/odoo_ha_addon/network_info` | Get network info | `ha_instance_id` (optional) |
| `/odoo_ha_addon/ha_urls` | Get HA URLs | `ha_instance_id` (optional) |
| `/odoo_ha_addon/websocket_status` | Get WebSocket status | `ha_instance_id` (optional) |
| `/odoo_ha_addon/websocket_restart` | Restart WebSocket | `ha_instance_id` (optional), `force` |
| `/odoo_ha_addon/areas` | Get all areas | `ha_instance_id` (optional) |
| `/odoo_ha_addon/entities_by_area` | Get entities by area | `area_id`, `ha_instance_id` (optional) |
| `/odoo_ha_addon/call_service` | Call HA service | `domain`, `service`, `service_data`, `ha_instance_id` (optional) |

### Usage Examples

#### Mode 1: Using Session Instance (Recommended)

```javascript
// Dashboard component
async loadHardwareInfo() {
  // Don't pass ha_instance_id, automatically uses session
  const result = await rpc("/odoo_ha_addon/hardware_info");

  if (result.success) {
    this.state.hardware.data = result.data;
  } else {
    this.state.hardware.error = result.error;
  }
}

async loadNetworkInfo() {
  const result = await rpc("/odoo_ha_addon/network_info");
  // Uses same session instance
}

async callService(domain, service, serviceData) {
  const result = await rpc("/odoo_ha_addon/call_service", {
    domain,
    service,
    service_data: serviceData
    // Don't pass ha_instance_id
  });
  // Service executes on session instance
}
```

#### Mode 2: Explicit Instance (Special Cases)

```javascript
// Compare hardware info of two instances
async compareInstances(instanceId1, instanceId2) {
  const [result1, result2] = await Promise.all([
    rpc("/odoo_ha_addon/hardware_info", { ha_instance_id: instanceId1 }),
    rpc("/odoo_ha_addon/hardware_info", { ha_instance_id: instanceId2 }),
  ]);

  // Compare instance data
  this.displayComparison(result1.data, result2.data);
}

// Admin operation: Restart specific instance
async adminRestartInstance(instanceId) {
  const result = await rpc("/odoo_ha_addon/websocket_restart", {
    ha_instance_id: instanceId,  // Explicitly specify
    force: true
  });
}
```

#### Mode 3: Hybrid Usage

```javascript
// General case uses session
async loadCurrentInstanceData() {
  const hardware = await rpc("/odoo_ha_addon/hardware_info");
  const network = await rpc("/odoo_ha_addon/network_info");
  return { hardware, network };
}

// Specific needs explicitly specify
async loadTestInstanceData() {
  const testInstanceId = 99;  // Test environment instance
  const hardware = await rpc("/odoo_ha_addon/hardware_info", {
    ha_instance_id: testInstanceId
  });
  return hardware;
}
```

### Parameter Passing Pattern Summary

| Scenario | Pass instance_id | Reason |
|----------|------------------|--------|
| Dashboard displays current instance data | ❌ No | Use session, simple |
| User switches instance and reloads data | ❌ No | Session already updated |
| Compare multiple instance data | ✅ Yes | Need simultaneous query |
| Test specific instance | ✅ Yes | Don't affect session |
| Admin operates on specific instance | ✅ Yes | Clear target |

---

## Error Handling

### 1. Session Invalidation Handling

#### Scenario: Session Expired or Cleared

**Problem**:
```
User inactive for long time → Session expires → current_ha_instance_id lost
```

**Backend Handling**:

```python
def _get_current_instance(self):
    session_instance_id = request.session.get('current_ha_instance_id')

    if session_instance_id:
        instance = request.env['ha.instance'].sudo().search([
            ('id', '=', session_instance_id),
            ('active', '=', True)
        ], limit=1)

        if not instance:
            # Session instance invalid, clear and fallback
            self._logger.warning(f"Session instance {session_instance_id} invalid")
            request.session.pop('current_ha_instance_id', None)

            # ✨ Trigger Bus notification (Phase 3 implementation)
            # self.env['ha.realtime.update'].notify_session_fallback(...)

    # Automatically fallback to default or first active instance
    return self._fallback_to_default_instance()
```

**Frontend Handling** (Phase 3 Enhancement):

```javascript
// Subscribe to session invalidation notification
setup() {
  this.haDataService.onGlobalState('session_fallback', ({ instanceId, instanceName, reason }) => {
    console.warn(`[Component] Session fallback: ${reason}`);
    console.log(`[Component] Now using: ${instanceName}`);

    // Show notification to user
    this.notification.add(
      `Session expired, automatically switched to ${instanceName}`,
      { type: 'warning' }
    );

    // Reload data
    this.reloadAllData();
  });
}
```

---

## Best Practices

### 1. When to Use Session, When to Pass Parameters

#### ✅ Use Session (Recommended Scenarios)

| Scenario | Reason |
|----------|--------|
| Dashboard displays current instance | Simple, matches user expectation |
| Single page application data loading | No need to manage additional state |
| User active operations | Automatically takes effect after switching instance |
| Most UI components | Reduce code complexity |

**Example**:

```javascript
// ✓ Good practice
class Dashboard extends Component {
  async loadAllData() {
    await Promise.all([
      this.loadHardwareInfo(),  // Use session
      this.loadNetworkInfo(),   // Use session
      this.loadHaUrls(),        // Use session
    ]);
  }
}
```

#### ✅ Explicitly Pass Parameters (Special Scenarios)

| Scenario | Reason |
|----------|--------|
| Compare multiple instances | Need simultaneous query |
| Testing and debugging | Don't affect session |
| Admin tools | Clear target instance |
| Background tasks | Don't depend on user session |

**Example**:

```javascript
// ✓ Good practice
class InstanceComparison extends Component {
  async compareInstances(id1, id2) {
    const [data1, data2] = await Promise.all([
      rpc("/odoo_ha_addon/hardware_info", { ha_instance_id: id1 }),
      rpc("/odoo_ha_addon/hardware_info", { ha_instance_id: id2 }),
    ]);
    this.displayComparison(data1, data2);
  }
}
```

---

## Related Documents

- **Instance Switching Event Handling**: [instance-switching.md](instance-switching.md) - How frontend components respond to instance switching
  - Applicable scenarios: Implementing switch-responsive components, debugging event issues
  - Key content: Global callback system, component lifecycle, common errors
- **Bus Notification Mechanism**: [../guides/bus-mechanisms.md](../guides/bus-mechanisms.md)
- **WebSocket Subscription Mechanism**: [websocket-subscription.md](websocket-subscription.md)
- **Project Guide**: `/CLAUDE.md`

---

## Version History

- **v1.0** (2025-11-03): Initial version
  - Complete Session-Based Instance architecture explanation
  - Usage guide for 8 endpoints
  - Error handling and best practices
  - Troubleshooting guide
  - Based on Phase 3/4 multi-instance support implementation experience
- **v1.1** (2025-11-25): Architecture update
  - Removed `is_default` field
  - Changed to 3-level permission-aware fallback mechanism
  - Updated all flow diagrams and examples
