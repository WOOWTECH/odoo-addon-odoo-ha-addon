---
created: 2026-01-01T15:23:16Z
last_updated: 2026-01-18T08:00:05Z
version: 1.1
author: Claude Code PM System
---

# Technical Context

## Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Odoo** | 18.0 | ERP framework |
| **Python** | 3.10+ | Backend language |
| **PostgreSQL** | 15 | Database |
| **websockets** | >=12.0 | WebSocket client library |
| **asyncio** | stdlib | Async I/O |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Odoo Web (OWL)** | 2.x | Component framework |
| **Chart.js** | (bundled) | Data visualization |
| **Font Awesome** | 4.x | Icon library |
| **SCSS** | - | Styling |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Nginx** | Reverse proxy |
| **Git Worktree** | Parallel development |

## Dependencies

### Python Dependencies (requirements.txt)
```
websockets>=12.0
asyncio
```

### Odoo Dependencies (__manifest__.py)
```python
'depends': ['base', 'web', 'mail']
```

## Development Environment

### Docker Configuration
- **Docker Compose File:** `docker-compose-18.yml`
- **Web Port:** 8069
- **Database Admin:** 8080 (Adminer)
- **Entry URL:** http://localhost (via Nginx)

### Key Paths
| Path | Description |
|------|-------------|
| `/mnt/extra-addons` | Addon mount point (from `./data/18/addons`) |
| `data/18/addons/odoo_ha_addon` | Addon source directory |

### Development Commands
```bash
# Start environment
docker compose -f docker-compose-18.yml up

# Restart web container
docker compose -f docker-compose-18.yml restart web

# Update addon
docker compose -f docker-compose-18.yml exec web odoo -d odoo -u odoo_ha_addon --dev xml

# Access shell
docker compose -f docker-compose-18.yml exec web bash

# View logs
docker compose -f docker-compose-18.yml logs -f web
```

## External Integrations

### Home Assistant Integration

| API Type | Purpose |
|----------|---------|
| **REST API** | Entity data, area info, device info |
| **WebSocket API** | Real-time state updates, subscriptions |

#### WebSocket Commands Used
- `subscribe_events` - State change notifications
- `get_states` - All entity states
- `call_service` - Control devices

### Odoo Bus System
- **Channels:** `ha_entity_update`, instance-specific channels
- **Protocol:** Long-polling / WebSocket (when available)

## Runtime Patterns

### Thread Management
- **WebSocket Threads:** Managed per-instance
- **Thread Pool:** Controlled by `websocket_thread_manager.py`
- **Cleanup:** Handled via `uninstall_hook`

### Cron Jobs
- **WebSocket Cron:** Defined in `data/websocket_cron.xml`
  - Purpose: Maintain WebSocket connections
- **Entity Share Cron:** Defined in `data/cron.xml` (NEW)
  - Purpose: Handle share expiry notifications

## Testing Infrastructure

### Test Framework
- Odoo's test runner (based on Python unittest)
- Test files in `tests/` directory

### Test Commands
```bash
# Run tests in container
docker compose -f docker-compose-18.yml exec web odoo -d odoo -u odoo_ha_addon --test-enable

# Run specific test
docker compose -f docker-compose-18.yml exec web odoo -d odoo --test-tags=/odoo_ha_addon
```

## Build & Deploy

### Asset Compilation
- Odoo handles asset bundling
- Assets defined in `__manifest__.py` under `'assets'`
- Development mode: `--dev xml` for auto-reload

### Addon Installation Hooks
| Hook | Purpose |
|------|---------|
| `pre_init_hook` | Install Python dependencies |
| `post_init_hook` | Post-installation setup |
| `uninstall_hook` | Cleanup on removal |
| `post_load_hook` | Runtime initialization |

## Version Information

### Addon Version
- **Current:** 18.0.5.0
- **License:** LGPL-3
- **Category:** WOOW/Extra Tools

### Compatibility
- **Odoo:** 18.0
- **Python:** 3.10+
- **PostgreSQL:** 15+

## Update History
- 2026-01-18: Added entity share cron job
