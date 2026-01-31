# Quick Start Guide

Get up and running with the Odoo HA Addon in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Basic understanding of Odoo and Home Assistant
- Home Assistant instance with API access

## Installation

### Step 1: Start Odoo Server

```bash
cd /Users/eugene/Documents/woow/AREA-odoo/odoo-server
docker compose -f docker-compose-18.yml up
```

### Step 2: Access Odoo

Open your browser and navigate to:
- **Web Interface**: http://localhost:8069
- **Database Admin**: http://localhost:8080 (Adminer)

### Step 3: Install the Addon

1. Log in to Odoo as administrator
2. Go to **Apps** menu
3. Search for "Home Assistant" or "odoo_ha_addon"
4. Click **Install**

> **Note**: During installation:
> - Python dependencies (`websockets`) are automatically installed via `pre_init_hook`
> - Admin user is automatically granted **HA Manager** permissions via `post_init_hook`

## Configuration

### Step 1: Configure Home Assistant Instance

1. Go to **Settings > Technical > Parameters > System Parameters**
2. Add/Edit these parameters:
   - `odoo_ha_addon.ha_api_url`: Your Home Assistant URL (e.g., `http://192.168.1.100:8123`)
   - `odoo_ha_addon.ha_api_token`: Your Home Assistant Long-Lived Access Token

### Step 2: Test Connection

1. Go to **Home Assistant > Configuration > Instances**
2. Click **Test Connection** on your instance
3. Verify the connection status shows "Connected"

### Step 3: Sync Entities

1. The addon automatically syncs entities via WebSocket
2. Go to **Home Assistant > Entities** to see synced devices
3. First sync may take a few minutes

## Basic Usage

### View Dashboard

1. Go to **Home Assistant > Dashboard**
2. See real-time sensor data, hardware info, and network status
3. Charts display historical data automatically

### Switch Instances

1. Click the **HA Instance** dropdown in the top navigation bar (Systray)
2. Select a different instance
3. Dashboard automatically reloads with new instance data

### Control Devices

1. Go to **Home Assistant > Entities**
2. Click on an entity (e.g., a light switch)
3. Use the form view to control the device state

## Development Setup

### Enable Development Mode

```bash
docker compose -f docker-compose-18.yml exec web odoo -d odoo --dev xml --log-handler odoo.tools.convert:DEBUG
```

### Update Addon After Changes

```bash
# For Python changes
docker compose -f docker-compose-18.yml restart web

# For XML/JS changes (hot reload enabled in dev mode)
# Just refresh your browser

# Force update addon
docker compose -f docker-compose-18.yml exec web odoo -d odoo -u odoo_ha_addon --dev xml
```

### Monitor Logs

```bash
docker compose -f docker-compose-18.yml logs -f web
```

## Common Commands

### WebSocket Status Check

```python
# In Odoo shell
env['ha.entity'].check_websocket_status()
```

### Restart WebSocket Service

```python
# In Odoo shell
env['ha.entity'].restart_websocket_service()
```

### Clear Cache

```python
# In Odoo shell
env['ir.cache'].clear_all()
```

## Troubleshooting

### WebSocket Not Connecting

**Symptoms**: Dashboard shows "WebSocket: Disconnected"

**Solution**:
1. Verify Home Assistant API URL and token in System Parameters
2. Check Home Assistant is accessible from Odoo container
3. Review logs: `docker compose logs -f web`
4. Restart WebSocket service from Odoo shell

### Entities Not Syncing

**Symptoms**: Entity list is empty or outdated

**Solution**:
1. Check WebSocket connection status
2. Verify user has `group_ha_user` or `group_ha_manager` permission
3. Check entity groups permissions (Settings > Home Assistant > Entity Groups)
4. Force sync by restarting WebSocket service

### Dashboard Shows Wrong Instance Data

**Symptoms**: Data doesn't match selected instance in Systray

**Solution**:
1. Clear browser cache and cookies
2. Check session in Odoo: Settings > Technical > Sessions
3. Switch to another instance and back
4. Check browser console for errors

### Permission Denied Errors

**Symptoms**: "Access Denied" errors when viewing entities

**Solution**:
1. Ensure user has `group_ha_user` permission (Settings > Users & Companies > Users)
2. Check entity group assignments (Settings > Home Assistant > Entity Groups)
3. Verify instance access permissions
4. Contact administrator for permission grants

## Next Steps

Now that you have the addon running:

1. **Understand the Architecture**: Read [Architecture Overview](../architecture/overview.md)
2. **Learn Development Patterns**: Review [Development Guide](../guides/development.md)
3. **Explore Security Model**: Check [Security Architecture](../architecture/security.md)
4. **Configure Multi-Instance**: See [Session Instance](../architecture/session-instance.md)

## Additional Resources

- **Full Documentation**: [docs/README.md](../README.md)
- **Development Guide**: [guides/development.md](../guides/development.md)
- **Troubleshooting**: [guides/troubleshooting.md](../guides/troubleshooting.md)
- **API Reference**: [reference/](../reference/)

## Getting Help

If you encounter issues not covered here:
1. Check the [Troubleshooting Guide](../guides/troubleshooting.md)
2. Review [Architecture Documentation](../architecture/)
3. Search through [Implementation Docs](../implementation/)
4. Check [Archived Issues](../archive/issues/) for similar problems

---

**Welcome to Odoo HA Addon!** We hope this quick start guide helps you get productive quickly. For deeper understanding, explore the rest of the documentation.
