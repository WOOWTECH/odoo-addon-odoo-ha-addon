# Troubleshooting Guide

This guide covers common issues and their solutions for the Odoo HA Addon.

## Quick Diagnosis

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| WebSocket shows "Disconnected" | Invalid API credentials | Check System Parameters |
| Entities not syncing | WebSocket connection issue | Restart WebSocket service |
| Dashboard shows wrong data | Session/cache issue | Clear session, switch instance |
| Permission denied errors | Missing group assignment | Assign `group_ha_user` |
| Multi-tab data mismatch | Bus notification issue | Check Nginx proxy config |
| Installation fails with pip error | Auto-install dependency failed | Manual pip install (see below) |
| Admin can't access HA settings | post_init_hook failed | Manual group assignment |

## Installation Issues

### Issue: Python Dependency Installation Failed

**Symptoms**:
- Module installation fails with pip error
- Error message about `websockets` package
- `--break-system-packages` flag error

**Note**: The addon automatically installs `websockets` via `pre_init_hook`. This may fail in some environments.

**Solutions**:

1. **Manual Installation** (Recommended for Docker):
   ```bash
   docker compose exec web pip install --break-system-packages websockets>=10.0
   ```

2. **Without `--break-system-packages`** (Older systems):
   ```bash
   docker compose exec web pip install websockets>=10.0
   ```

3. **Add to requirements.txt** (Persistent fix):
   ```
   # In your Odoo requirements.txt
   websockets>=10.0
   ```

### Issue: Admin Cannot Access HA Settings After Install

**Symptoms**:
- Fresh install completed but admin can't see HA menu
- "Access Denied" when trying to configure instances
- HA Manager permission missing

**Note**: The addon automatically grants HA Manager permissions to admin via `post_init_hook`. This may fail if the user/group references are modified.

**Solutions**:

1. **Manual Group Assignment**:
   - Go to: Settings > Users & Companies > Users
   - Select admin user
   - In **Administration** tab, enable "Home Assistant Manager"

2. **Via Odoo Shell**:
   ```python
   admin = env.ref('base.user_admin')
   ha_manager = env.ref('odoo_ha_addon.group_ha_manager')
   admin.write({'groups_id': [(4, ha_manager.id)]})
   ```

3. **Check Installation Logs**:
   ```bash
   docker compose logs web | grep post_init_hook
   ```

## WebSocket Issues

### Issue: WebSocket Connection Failed

**Symptoms**:
- Dashboard displays "WebSocket: Disconnected" or "WebSocket: Error"
- Entities are not syncing
- Real-time updates not working

**Diagnosis**:
```bash
# Check WebSocket status
docker compose logs web | grep WebSocket

# Check in Odoo shell
env['ha.entity'].check_websocket_status()
```

**Solutions**:

1. **Verify Home Assistant Configuration**:
   - Go to: Settings > Technical > Parameters > System Parameters
   - Check `odoo_ha_addon.ha_api_url` (e.g., `http://192.168.1.100:8123`)
   - Check `odoo_ha_addon.ha_api_token` (Long-Lived Access Token)
   - Ensure URL is accessible from Docker container

2. **Restart WebSocket Service**:
   ```python
   # In Odoo shell
   env['ha.entity'].restart_websocket_service()
   ```

3. **Check Network Connectivity**:
   ```bash
   # Test from within Odoo container
   docker compose exec web bash
   curl http://YOUR_HA_URL:8123/api/
   ```

4. **Review Logs**:
   ```bash
   docker compose logs -f web | grep -i websocket
   ```

### Issue: WebSocket Keeps Disconnecting

**Symptoms**:
- Connection status alternates between "Connected" and "Disconnected"
- Frequent reconnection attempts in logs

**Solutions**:

1. **Check Home Assistant Stability**:
   - Verify Home Assistant is not restarting frequently
   - Check Home Assistant system resources (CPU, Memory)
   - Review Home Assistant logs for errors

2. **Increase Timeout Settings**:
   - WebSocket timeout is configurable in `models/common/hass_websocket_service.py`
   - Default ping interval: 30 seconds
   - Default timeout: 60 seconds

3. **Network Issues**:
   - Check firewall rules between Odoo and Home Assistant
   - Verify no proxy/load balancer interfering with WebSocket
   - Test with direct IP connection instead of DNS

## Entity Sync Issues

### Issue: Entities Not Appearing

**Symptoms**:
- Entity list is empty
- Recently added HA entities don't show up

**Solutions**:

1. **Force Entity Sync**:
   ```python
   # In Odoo shell
   env['ha.entity'].fetch_states(force=True)
   ```

2. **Check Permissions**:
   - Verify user has `group_ha_user` or `group_ha_manager`
   - Go to: Settings > Users & Companies > Users
   - Check user's groups include "Home Assistant User"

3. **Verify Entity Groups**:
   - Go to: Settings > Home Assistant > Entity Groups
   - Ensure entities are assigned to groups
   - Verify user has access to entity groups

4. **Check Instance Selection**:
   - Ensure correct instance is selected in Systray
   - Try switching to another instance and back

### Issue: Entity Data Outdated

**Symptoms**:
- Entity states don't update in real-time
- Historical data missing

**Solutions**:

1. **Check WebSocket Status**: Must be "Connected" for real-time updates

2. **Clear Cache**:
   ```python
   env['ir.cache'].clear_all()
   ```

3. **Force Reload**:
   - Refresh browser (Ctrl+F5 / Cmd+Shift+R)
   - Logout and login again
   - Clear browser cookies

## Session and Instance Issues

### Issue: Dashboard Shows Wrong Instance Data

**Symptoms**:
- Selected instance in Systray doesn't match displayed data
- Data from previous instance still showing
- Switching instances has no effect

**Diagnosis**:
```python
# Check session
request.session.get('current_ha_instance_id')

# Check user preference
env.user.current_ha_instance_id
```

**Solutions**:

1. **Clear Session**:
   ```python
   # In Odoo shell
   request.session.pop('current_ha_instance_id', None)
   ```

2. **Clear Browser Storage**:
   - Open browser DevTools (F12)
   - Application > Storage > Clear site data
   - Refresh page

3. **Force Instance Switch**:
   - Switch to a different instance
   - Wait for data to load
   - Switch back to desired instance

4. **Check Fallback Logic**:
   - Review logs for "Session instance invalid" warnings
   - Verify instance still exists and is active
   - Check user has permission to access instance

### Issue: Multi-Tab Instance Mismatch

**Symptoms**:
- Different tabs show different instance data
- Switching instance in one tab doesn't update others

**Diagnosis**:
```javascript
// In browser console
// Check if Bus WebSocket is connected
// Look for: /bus/websocket_worker_bundle in Network tab
```

**Solutions**:

1. **Verify Nginx Proxy Configuration**:
   ```nginx
   # Check data/nginx/odoo.conf
   location /bus/websocket_worker_bundle {
       proxy_pass http://localhost:8072;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```

2. **Restart Nginx**:
   ```bash
   docker compose restart nginx
   ```

3. **Check Bus Service**:
   - Open DevTools > Network
   - Look for `/bus/websocket_worker_bundle` request
   - Status should be `101 Switching Protocols`

4. **Review Bus Notifications**:
   ```javascript
   // Add debug logging in HaBusBridge
   console.log('[DEBUG] Bus notification received:', notification);
   ```

## Permission Issues

### Issue: Access Denied Errors

**Symptoms**:
- "Access Denied" when viewing entities
- Cannot see certain instances
- Missing menu items

**Solutions**:

1. **Check User Groups**:
   - Go to: Settings > Users & Companies > Users
   - Select user
   - Ensure has `group_ha_user` or `group_ha_manager`

2. **Verify Entity Group Access**:
   - Go to: Settings > Home Assistant > Entity Groups
   - Check which groups user is assigned to
   - Public groups (no users assigned) are visible to all HA users

3. **Check Instance Permissions**:
   ```python
   # In Odoo shell
   user = env['res.users'].browse(USER_ID)
   accessible = env['ha.instance'].get_accessible_instances()
   print(f"User can access: {accessible.mapped('name')}")
   ```

4. **Review Record Rules**:
   - Go to: Settings > Technical > Security > Record Rules
   - Filter by model: `ha.entity`, `ha.instance`, etc.
   - Verify rules are correctly configured

## Frontend Issues

### Issue: Dashboard Not Loading

**Symptoms**:
- Blank dashboard
- JavaScript errors in console
- Infinite loading spinner

**Diagnosis**:
```javascript
// Open browser DevTools > Console
// Look for errors related to:
// - ha_data_service
// - chart_service
// - Component rendering
```

**Solutions**:

1. **Clear Browser Cache**:
   - Hard refresh: Ctrl+F5 (Windows) / Cmd+Shift+R (Mac)
   - Or clear site data in DevTools

2. **Check Asset Loading**:
   - DevTools > Network tab
   - Filter by JS/CSS
   - Verify all `web.assets_backend` files loaded successfully

3. **Review Console Errors**:
   - Common errors and solutions:
     - `ha_data is undefined`: Service not registered, check asset loading
     - `Cannot read property 'useState'`: OWL version mismatch
     - `rpc is not defined`: Missing OWL import

4. **Verify Service Registration**:
   ```javascript
   // In browser console
   const services = odoo.__DEBUG__.services;
   console.log('ha_data service:', services.ha_data);
   ```

### Issue: Charts Not Displaying

**Symptoms**:
- Chart area is blank
- Console errors about Chart.js
- Historical data charts missing

**Solutions**:

1. **Check Chart.js Library**:
   ```javascript
   // In browser console
   console.log('Chart.js:', window.Chart);
   ```

2. **Verify Chart Service**:
   ```javascript
   const chartService = useService("chart");
   console.log('Chart service:', chartService);
   ```

3. **Destroy Old Charts**:
   ```javascript
   // In component
   onWillUnmount(() => {
       if (this.chartRef) {
           this.chartService.destroyChart(this.chartRef);
       }
   });
   ```

4. **Check Chart Data Format**:
   - Verify data structure matches Chart.js expectations
   - Use `UnifiedChart` component for consistent behavior
   - Review console for data validation errors

## Performance Issues

### Issue: Slow Dashboard Loading

**Symptoms**:
- Dashboard takes >5 seconds to load
- UI feels sluggish
- High CPU usage

**Solutions**:

1. **Enable Caching**:
   - HaDataService caches API responses for 30 seconds
   - Verify cache is working:
     ```javascript
     console.log('Cache size:', haDataService.cache.size);
     ```

2. **Optimize Chart Rendering**:
   - Use `UnifiedChart` instead of legacy chart components
   - Limit historical data range
   - Reduce chart update frequency

3. **Batch API Calls**:
   ```javascript
   // Good: Parallel loading
   await Promise.all([
       this.loadHardwareInfo(),
       this.loadNetworkInfo(),
       this.loadWebSocketStatus()
   ]);

   // Bad: Sequential loading
   await this.loadHardwareInfo();
   await this.loadNetworkInfo();
   await this.loadWebSocketStatus();
   ```

4. **Check Database Query Performance**:
   ```python
   # Enable query logging
   # In odoo.conf
   log_level = debug_sql
   ```

### Issue: Memory Leaks

**Symptoms**:
- Browser memory usage keeps increasing
- Tab becomes unresponsive over time
- Need to refresh frequently

**Solutions**:

1. **Clean Up Subscriptions**:
   ```javascript
   setup() {
       const haDataService = useService("ha_data");

       this.handler = (data) => { /* ... */ };
       haDataService.onGlobalState('instance_switched', this.handler);

       onWillUnmount(() => {
           // IMPORTANT: Always clean up!
           haDataService.offGlobalState('instance_switched', this.handler);
       });
   }
   ```

2. **Destroy Chart Instances**:
   ```javascript
   onWillUnmount(() => {
       if (this.chartInstance) {
           this.chartService.destroyChart(this.chartInstance);
       }
   });
   ```

3. **Monitor Memory Usage**:
   - Chrome DevTools > Memory > Take Heap Snapshot
   - Look for detached DOM nodes
   - Check for event listener leaks

## Database Issues

### Issue: PostgreSQL Serialization Conflict

**Symptoms**:
- Error: "could not serialize access due to concurrent update"
- Occasional WebSocket request failures

**Solution**:
- This is a known issue with concurrent WebSocket updates
- See: [archive/issues/postgresql-serialization-conflict.md](../archive/issues/postgresql-serialization-conflict.md)
- Retry logic is already implemented in WebSocket service

### Issue: Database Deadlock

**Symptoms**:
- Transactions timing out
- "deadlock detected" errors in logs

**Solutions**:

1. **Check Transaction Isolation**:
   - Review transaction scopes in code
   - Avoid long-running transactions

2. **Restart Database**:
   ```bash
   docker compose restart db
   ```

3. **Analyze Locks**:
   ```sql
   -- In PostgreSQL
   SELECT * FROM pg_locks WHERE NOT granted;
   ```

## Diagnostic Commands

### Check System Status

```python
# In Odoo shell
# WebSocket status
env['ha.entity'].check_websocket_status()

# Instance count
instances = env['ha.instance'].search([])
print(f"Total instances: {len(instances)}")

# Entity count
entities = env['ha.entity'].search([])
print(f"Total entities: {len(entities)}")

# Current user permissions
user = env.user
print(f"User: {user.name}")
print(f"Groups: {user.groups_id.mapped('name')}")
print(f"Accessible instances: {env['ha.instance'].get_accessible_instances().mapped('name')}")
```

### Enable Debug Logging

```python
# In Odoo shell
import logging

# Enable WebSocket debug logs
logging.getLogger('odoo.addons.odoo_ha_addon.models.common.hass_websocket_service').setLevel(logging.DEBUG)

# Enable controller debug logs
logging.getLogger('odoo.addons.odoo_ha_addon.controllers').setLevel(logging.DEBUG)
```

### Clear All Caches

```python
# In Odoo shell
# Clear Odoo cache
env['ir.cache'].clear_all()

# Clear frontend cache (requires browser refresh)
# Or use Ctrl+Shift+R
```

## Getting More Help

If your issue isn't covered here:

1. **Check Architecture Docs**:
   - [Session Instance](../architecture/session-instance.md) - Session issues
   - [Instance Helper](../architecture/instance-helper.md) - Instance selection
   - [Bus Mechanisms](bus-mechanisms.md) - Real-time notification issues
   - [WebSocket Subscription](../architecture/websocket-subscription.md) - WebSocket issues

2. **Review Implementation Docs**:
   - [Multi-Instance Implementation](../implementation/multi-instance/overview.md)
   - [Phase 6 Test Report](../implementation/multi-instance/phase6-report.md)

3. **Check Archived Issues**:
   - [Issues Archive](../archive/issues/)
   - Similar problems might have been resolved

4. **Enable Verbose Logging**:
   - Backend: Set `log_level = debug` in odoo.conf
   - Frontend: Add console.log statements
   - Network: Monitor in browser DevTools

---

**Still having issues?** Make sure you're running the latest version of the addon and Odoo 18. Check the [changelog](../changelog/) for recent fixes.
