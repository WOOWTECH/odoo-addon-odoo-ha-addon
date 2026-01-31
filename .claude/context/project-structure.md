---
created: 2026-01-01T15:23:16Z
last_updated: 2026-01-18T13:25:58Z
version: 1.4
author: Claude Code PM System
---

# Project Structure

## Root Directory

```
odoo_ha_addon/
├── __init__.py              # Package initialization
├── __manifest__.py          # Odoo addon manifest (version 18.0.5.0)
├── hooks.py                 # Installation/uninstallation hooks
├── requirements.txt         # Python dependencies
├── CLAUDE.md               # AI assistant guidelines
├── CHANGELOG.md            # Version changelog (English)
├── CHANGELOG-tw.md         # Version changelog (Traditional Chinese)
├── AGENTS.md               # Agent 使用說明 (NEW)
├── COMMANDS.md             # 命令參考 (NEW)
├── CONTEXT_ACCURACY.md     # Context 準確度說明 (NEW)
├── LOCAL_MODE.md           # 本地開發模式 (NEW)
├── README_CCPM.md          # CCPM 系統文件 (NEW)
│
├── models/                  # Backend models (18 files)
├── controllers/             # HTTP controllers (2 files)
│   ├── controllers.py       # API endpoints
│   └── portal.py            # Portal user-based access + entity control
├── views/                   # XML view definitions (16 files)
│   ├── portal_templates.xml # Portal QWeb templates (zh_TW)
│   └── ha_entity_share_wizard_views.xml # Share wizard views (NEW)
├── static/                  # Frontend assets
├── docs/                    # Technical documentation
├── data/                    # Initial data files
│   └── cron.xml            # Cron jobs (NEW)
├── security/                # Access rights & rules
├── i18n/                    # Internationalization
├── wizard/                  # Wizard models
│   └── ha_entity_share_wizard.py  # Entity share wizard (NEW)
├── tests/                   # Test suite (7 files)
│   ├── test_controllers.py        # API tests
│   ├── test_portal_controller.py  # Portal route + control tests
│   ├── test_share_permissions.py  # Permission tests
│   ├── test_entity_share.py       # Entity share tests
│   ├── test_share_wizard.py       # Share wizard tests
│   ├── test_portal_my_ha.py       # Portal my/ha tests
│   └── test_security.py           # ir.rule 權限測試 (NEW)
└── .claude/                 # Claude Code configuration
```

## Models Directory

```
models/
├── __init__.py
├── common/                  # Shared utilities
│   ├── __init__.py
│   ├── hass_rest_api.py    # Home Assistant REST API client
│   ├── hass_websocket_service.py  # WebSocket service
│   ├── instance_helper.py  # HAInstanceHelper (Single Source of Truth)
│   ├── mixins.py           # Reusable model mixins
│   ├── utils.py            # Utility functions
│   ├── websocket_client.py # WebSocket client implementation
│   └── websocket_thread_manager.py  # Thread management
│
├── ha_instance.py          # Home Assistant instance model
├── ha_entity.py            # Entity base model (portal.mixin removed)
├── ha_entity_history.py    # Entity history data
├── ha_entity_group.py      # Entity grouping (portal.mixin removed)
├── ha_entity_group_tag.py  # Group tagging
├── ha_entity_tag.py        # Entity tagging
├── ha_entity_share.py      # Entity sharing records (NEW)
├── ha_area.py              # Area (room) model
├── ha_device.py            # Device model
├── ha_label.py             # Label model
├── ha_realtime_update.py   # Real-time update handling
├── ha_ws_request_queue.py  # WebSocket request queue
├── ir_action.py            # Action extensions
└── ir_ui_view.py           # View type extensions
```

## Frontend Structure

```
static/src/
├── constants.js             # Global constants
│
├── services/                # Service layer
│   ├── chart_service.js    # Chart.js integration
│   ├── ha_data_service.js  # Data fetching service
│   ├── ha_bus_bridge.js    # Bus notification bridge
│   └── ha_bus_bridge.xml   # Bus bridge template
│
├── util/                    # Shared utilities
│   ├── debug.js            # Debug logging utilities
│   └── color.js            # Color manipulation
│
├── components/              # Reusable components
│   ├── charts/             # Chart components
│   │   ├── unified_chart/  # Universal chart wrapper
│   │   ├── chart/          # Base chart component
│   │   └── line_chart/     # Line chart variant
│   ├── entity_controller/  # Entity control components
│   │   ├── hooks/          # React-like hooks
│   │   └── controllers/    # Domain-specific controllers
│   ├── dashboard_item/     # Dashboard card component
│   ├── instance_selector/  # Instance picker dropdown
│   ├── device_card/        # Device display card
│   ├── standalone_entity_card/  # Entity card
│   ├── glances_block/      # Glances integration
│   ├── related_entity_dialog/  # Entity info dialog
│   └── entity_demo/        # Demo wrapper
│
├── views/                   # Custom view types
│   ├── hahistory/          # History timeline view
│   │   ├── hahistory_model.js
│   │   ├── hahistory_renderer.js
│   │   ├── hahistory_arch_parser.js
│   │   ├── hahistory_controller.js
│   │   └── hahistory_view.js
│   └── entity_kanban/      # Entity Kanban view
│
├── actions/                 # Client actions (pages)
│   ├── ha_instance_dashboard/  # Instance entry page
│   ├── dashboard/          # Main dashboard
│   ├── area_dashboard/     # Area-based view
│   └── glances_device_dashboard/  # Glances devices
│
└── scss/                    # Stylesheets
    └── dashboard.scss
```

## Views Directory

```
views/
├── dashboard_menu.xml              # Main menu structure
├── dashboard_views.xml             # Dashboard views
├── ha_instance_views.xml           # Instance management
├── ha_instance_dashboard_action.xml # Instance entry action
├── ha_entity_views.xml             # Entity list/form views
├── ha_entity_history_views.xml     # History views
├── ha_entity_group_views.xml       # Group views
├── ha_entity_group_tag_views.xml   # Group tag views
├── ha_entity_tag_views.xml         # Entity tag views
├── ha_area_views.xml               # Area views
├── ha_device_views.xml             # Device views
├── ha_label_views.xml              # Label views
├── ha_config_action.xml            # Settings action
├── res_config_settings.xml         # System settings
└── area_dashboard_views.xml        # Area dashboard action
```

## Documentation Structure

```
docs/
├── README.md                # Documentation index
├── architecture/            # Architecture docs
│   ├── overview.md
│   ├── security.md
│   ├── session-instance.md
│   ├── user-based-sharing.md  # User-based sharing (NEW)
│   └── ...
├── guides/                  # Development guides
│   ├── development.md
│   ├── troubleshooting.md
│   ├── i18n-development.md   # i18n 開發指南 (NEW)
│   └── ...
├── implementation/          # Implementation details
│   ├── multi-instance/
│   ├── i18n/
│   └── features/
├── backlog-prd/             # Backlog PRDs (NEW)
│   ├── ha-user-permission-fix.md
│   └── user-permission-ui-improvements.md
├── reference/               # API references
├── changelog/               # Change logs
└── archive/                 # Historical docs
```

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Model | `ha_{entity}.py` | `ha_entity.py` |
| View | `ha_{entity}_views.xml` | `ha_entity_views.xml` |
| Component | `{name}/{name}.js` | `device_card/device_card.js` |
| Service | `{name}_service.js` | `ha_data_service.js` |
| Action | `{name}/{name}.js` | `dashboard/dashboard.js` |
| Test | `test_{module}.py` | `test_controllers.py` |

## Key Files

| File | Purpose |
|------|---------|
| `__manifest__.py` | Addon metadata, dependencies, assets |
| `hooks.py` | Installation lifecycle hooks |
| `models/common/instance_helper.py` | Single Source of Truth for instance |
| `models/ha_entity_share.py` | Entity sharing records (NEW) |
| `wizard/ha_entity_share_wizard.py` | Share wizard (NEW) |
| `static/src/services/ha_data_service.js` | Frontend data layer |
| `static/src/services/chart_service.js` | Chart.js wrapper |

## Update History
- 2026-01-18: Added test_security.py for ir.rule permission tests
- 2026-01-18: Added ha_entity_share model, share wizard, new docs and tests
