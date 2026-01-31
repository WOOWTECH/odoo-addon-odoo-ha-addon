# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [18.0.6.2] - 2026-01-21

### Added

#### Portal Enhancements

- Add Portal Breadcrumbs navigation for better user orientation
- Add PortalLiveStatus component for real-time sidebar state display
- Add Entity Control panel to Entity Form View

#### Entity Form View

- Add responsive layout support for better mobile experience
- Fix attributes parsing in Entity Form View

### Fixed

#### Portal

- Prevent portal entity grid overflow with unified card minimum width (150px)
- Add group share fallback for entity access check (fix permission issues when accessing via group share)
- Correct attributes path in portal entity control response handler

### Changed

#### UI Refactoring

- Simplify entity controller UI to match portal style
- Simplify portal entity controller UI structure
- Remove unused LiveStatusCard sub-template from PortalEntityInfo
- Simplify group header UI by removing redundant elements

### Documentation

- Add user guide for sharing feature with screenshots

## [18.0.6.1] - 2026-01-18

### Changed

#### Sharing Mechanism Migration (Token-Based to User-Based)

- Replaced token-based portal access with user-based authentication (`auth='user'`)
- Portal routes now require Odoo login, unauthenticated users are redirected to login page
- Added `/my/ha` page for users to view all entities and groups shared with them
- Instance-based navigation: `/my/ha/<instance_id>` shows entities/groups per HA instance

### Added

#### ha.entity.share Model

- New model `ha.entity.share` for tracking share relationships between entities/groups and users
- SQL constraints for entity/group mutual exclusivity and unique user combinations
- Computed fields: `ha_instance_id`, `is_expired`, `display_name`
- Search support for `is_expired` field with proper domain filtering
- Helper methods: `get_shares_for_user()`, `get_shared_entities_for_user()`, `get_shared_groups_for_user()`

#### Share Wizard (ha.entity.share.wizard)

- New wizard for multi-user sharing with batch create/update support
- Context-aware default population (from entity/group form views)
- Permission level selection: View Only or Can Control
- Optional expiry date setting
- Duplicate handling: updates existing shares instead of creating duplicates
- Display of existing shares count and user list

#### Permission-Based Access Control

- Two permission levels: `view` (read-only) and `control` (can operate devices)
- View permission shows entity state but hides control UI
- Control permission enables device operation via `/portal/call-service` endpoint
- Domain and service whitelist validation for control actions

#### Expiry Management

- Optional expiry date for shares
- Cron job: `_cron_check_expiring_shares()` - notifies share creators 7 days before expiry
- Cron job: `_cron_cleanup_expired_shares()` - removes shares expired for 30+ days
- Expired shares are automatically excluded from access checks

#### Portal /my/ha Integration

- `/my/ha` route displays all HA instances with shares for current user
- `/my/ha/<instance_id>` route shows entities/groups in tabs
- Entity count and group count per instance
- Permission badge display (View/Control)
- Empty state message when no shares exist

#### UI Enhancements

- Slider progress indicator styling for brightness, fan speed, and cover position controls

### Fixed

#### Share Wizard UI

- Remove group wrapper from share wizard alert to fix UI layout issue

#### Permission System

- Clear ir.rule cache when entity group `user_ids` changes to ensure immediate permission updates
- Use `registry.clear_cache()` instead of deprecated `model.clear_caches()` for Odoo 18 compatibility

#### Portal

- Prevent portal entity controller overflow in two-column layout
- Add zh_TW translations for portal templates
- Align portal HA card with standard Odoo portal category structure

#### Cron Jobs

- Remove deprecated `numbercall` field from cron.xml for Odoo 18 compatibility

### Removed

#### Portal Token Mechanism (Deprecated)

- Remove `portal.mixin` inheritance from `ha.entity` and `ha.entity.group` models
- Remove `action_share_portal` method and "Share via Link" buttons from views
- Delete obsolete `test_portal_mixin.py` test file
- Token-based access completely replaced by user-based authentication

### Security

- All portal routes use `auth='user'` requiring Odoo login
- Access controlled via `ha.entity.share` records (no URL manipulation bypass)
- Field whitelists (`PORTAL_ENTITY_FIELDS`, `PORTAL_GROUP_FIELDS`) prevent sensitive data exposure
- `sudo()` used only for read operations, never for write
- Service whitelist (`PORTAL_CONTROL_SERVICES`) restricts allowed control actions
- Expired shares denied access automatically
- Added security tests for ir.rule permission changes

## [18.0.6.0] - 2025-01-10

### Added

#### Portal Sharing (Token-Based Access)

- Portal mixin support for `ha.entity` and `ha.entity.group` models
- Share button in entity and group form views with token generation
- Portal controller with HMAC-based token validation (timing attack prevention)
- Portal QWeb templates for entity and group sharing pages
- Polling optimization with visibility control and visual feedback
- Portal entity control for switch/light/fan/cover/climate/automation/scene/script domains
- Unified portal call-service API via JSON-RPC (`/portal/entity/<id>/call-service`)
- PortalEntityInfo and PortalGroupInfo OWL components
- Portal group entities displayed as responsive card grid layout
- Header-based token authentication (`X-Portal-Token`)

#### Portal UI Redesign (IoT-Style Interface)

- CSS Custom Properties theme system with light/dark mode support
- IoT Toggle Switch styles for binary controls
- Value Slider styles for brightness/speed/position controls
- Sensor Display styles for value and binary sensors
- State change animations with reduced motion support (accessibility)
- Responsive breakpoints and touch target optimization
- WCAG AA compliant color contrast (5.48:1 for green buttons)

#### History Sync Performance

- Parallel history sync with configurable max workers
- Stale subscription cleanup mechanism
- Batch subscription validity check (single DB query optimization)

#### Instance Data Management

- Extended instance data clearing to include devices, labels, and entity tags
- Sync Registry button to sync Labels, Areas, and Devices in order

#### Testing

- Playwright E2E tests for entity controller components
- E2E test configuration (`tests/e2e_tests/e2e_config.yaml`)

### Changed

#### Portal Architecture

- Unified portal token handling and access verification
- Migrated fetchState to JSON-RPC (removed deprecated HTTP endpoint)
- Renamed `entity_id` to `record_id` for clarity in call-service endpoint
- Removed deprecated `portal_entity_control` endpoint

#### Entity Controller Refactoring

- Extracted shared entity control logic into reusable hooks (`useEntityControl`)
- Unified action building with `buildActionsFromConfig` helper
- Unified entity controller action naming conventions
- Declarative `owl-component` tag for portal entity controller

#### UI/UX

- Disabled auto dark mode, use light theme as default
- Translated portal templates to zh_TW

### Fixed

- Prevent HA data deletion during addon uninstall
- CSS `max()` with `env()` escaped for SASS compiler compatibility
- JSON-RPC response wrapper handling in portal service
- Odoo record ID usage for portal API calls (was using HA entity_id)
- KeyError in subscription cleanup during concurrent access
- Timeout handling for parallel history sync tasks

### Documentation

- Added portal sharing feature documentation to CLAUDE.md
- Updated E2E testing section to use Playwright MCP
- Added portal UI testing guide with sample test links
- Formatted share_entities PRD markdown tables
- Clarified clear instance data only affects Odoo, not HA

## [18.0.5.0] - 2025-12-03

### Added

#### Glances Dashboard Integration

- Backend APIs for Glances device discovery and entity retrieval
  - `/glances_devices`: fetch devices via config/device_registry/list
  - `/glances_device_entities`: fetch device entities with states
- GlancesBlock component to display device cards in HA Info page
- GlancesDeviceDashboard action for detailed entity view
  - Group entities by type (CPU, memory, disk, network, etc.)
  - Color-coded status indicators based on values
- ha_data_service extended with `getGlancesDevices`/`getGlancesDeviceEntities` methods

#### Real-time Updates

- Event-driven cache invalidation for Glances dashboard
- Subscribe to `device_registry_updated` WebSocket event from Home Assistant
- Automatically clear Glances cache when devices are added or removed

### Changed

#### Code Quality

- Extract timer intervals to `constants.js` for better maintainability
- Centralize magic numbers (30000ms, 300000ms, etc.) into a single constants file

#### Cleanup

- Remove dead code: unused notification methods (`_notify_entity_update`, `_notify_ha_websocket_status`, `notify_entity_update`)

### Documentation

- Update docs to reflect actual implementation
- Fix TransientModel → Model with bus.listener.mixin in documentation
- Replace `notify_entity_update` with `notify_entity_state_change` in examples
- Update method list and code examples across 5 doc files

## [18.0.4.2] - 2025-11-27

### Added

#### Multi-Instance Support

- POS-style Settings page for HA Instance configuration
- Group-based permission system with explicit authorization
- Instance data clearing wizard with i18n support
- Instance sync timestamps tracking
- Show `ha_instance_id` field in entity list view
- Modal form for creating new HA Instance directly from dashboard

#### Internationalization

- Complete i18n support with Traditional Chinese translations
- Multi-language support throughout the addon

#### Installation & Dependencies

- Auto-install for Python dependencies in `pre_init_hook`
- Support for `--break-system-packages` flag for Debian/Ubuntu pip install
- Lazy import for websockets to enable auto-installation

### Fixed

#### Accessibility

- Standardize ARIA alert roles for accessibility compliance

#### Permissions & Security

- Use correct Odoo API for permission check
- Add error handling and permission check for create instance modal
- Auto-grant HA Manager permission to admin on install
- Prevent API token exposure in debug logs

#### Installation

- Remove `external_dependencies` to allow `pre_init_hook` auto-install

#### Data Integrity

- Add `copy=False` to fields that should not be duplicated
- Remove incorrect `@api.depends` from `entity_count` and `area_count`
- Correct mock patch path for `get_websocket_client` in tests

#### UI/UX

- Make required fields conditional to allow New Instance button
- Remove custom footer from modal form to use default save behavior
- Resolve view validation warnings for fa icons and alerts
- Add simplified modal form for creating new HA instance

### Changed

#### Architecture

- Remove `is_default` field and implement permission-based instance selection
- Replace systray switcher with instance dashboard entry page
- Extract `HACurrentInstanceFilterMixin` to reduce code duplication
- Consolidate menu definitions into `dashboard_menu.xml`
- Simplify HA instance field mapping using related fields

#### Performance

- Restore `cr.commit()` in `get_areas` for better concurrency
- Defer fingerprint update to save action instead of test connection

#### Code Quality

- Improve transaction management and internationalization
- Move loggers to module level
- Improve global settings visual separation

### Documentation

- Reorganize documentation structure
- Refactor CLAUDE.md and split into modular documentation
- Add comments explaining `sudo()` usage for security audit
- Update documentation to reflect `is_default` field removal
- Update architecture diagram to reflect actual implementation
- Update documentation for auto-install hooks and troubleshooting

### Tests

- Add unit tests for `get_areas` and area sync functionality

## [18.0.2.2] - 2025-10-28

### Fixed

- Layout component dependency removed from HA Info dashboard for improved ir.actions.client compatibility
- ACE editor JSON mode configuration removed from entity attributes view

## [18.0.2.1] - 2025-10-28

### Added

#### Entity Controllers

- Cover entity controller with real-time attribute sync (position, tilt)
- Fan entity controller with real-time attribute sync (speed, direction)
- Automation entity controller support
- Scene entity controller support
- Script entity controller support

#### Dashboard Features

- Network information dashboard with fullWidth layout support
- Home Assistant shared URLs display in network dashboard

### Fixed

- Event bubbling in entity controller buttons to prevent unwanted form view navigation
- Dashboard scrolling behavior with proper Odoo Layout integration
- PostgreSQL serialization conflicts in area dashboard with retry mechanism and savepoint isolation

### Performance

- Optimized dashboard initial loading with parallel data fetching

### Refactored

- Standardized all HTTP endpoint response formats with unified wrapper (`_standardize_response()`)
- All endpoints now return consistent `{success: bool, data: dict, error: str}` format

### Documentation

- API response format standardization documentation

## [18.0.2.0] - 2025-10-22

### Added

#### WebSocket Integration

- WebSocket real-time connection support with Home Assistant
- Cross-process WebSocket request queue system (`ws.request.queue` model)
- WebSocket status monitoring and real-time notifications
- Configurable WebSocket heartbeat interval with settings UI
- Intelligent retry mechanism and restart cooldown protection
- Multi-database support for WebSocket service
- WebSocket hardware info and control UI

#### History Data Management

- WebSocket subscription mechanism for history data streaming
- Comprehensive history API endpoints
- Search UI support with filters and grouping for history view
- Entity name and entity_id display fields in history list view
- Chart data structure enhancement with entity_name and entity_id_string fields

#### Real-time Notifications

- Centralized bus bridge pattern implementation (`HaBusBridge`)
- Unified real-time notification system via Odoo bus
- Real-time state change notifications with old/new state tracking
- Real-time WebSocket status updates to frontend

#### Entity Management

- Entity group tagging system with many2many relationships
- Color field support for entity groups with many2many_tags widget
- Sequence field for custom entity group tag ordering
- Friendly name field for HA entities
- Area-based dashboard with Home Assistant area management

#### Device Control

- Unified `EntityController` component with domain-specific controls
- Device control API implementation
- Complete control flow for Home Assistant devices

#### UI/UX Improvements

- Modernized settings UI with dedicated WOOW HA section
- Dashboard action renamed to `ha_info_dashboard` for clarity
- JSON to string conversion for ACE editor display

### Changed

- Renamed `state` field to `entity_state` to avoid Odoo reserved field conflict
- Renamed WebSocket request queue model with `ha` prefix for consistency (`ws.request.queue` → `ha.ws.request.queue`)
- Updated `view_mode` from `tree` to `list` for Odoo 18 compatibility
- Extracted `WebSocketClient` and unified API call logic
- Made WebSocket heartbeat interval dynamically configurable
- Updated menu configuration for better organization

### Fixed

- Error handling for unavailable `ha_data` service in entity demo
- Retry mechanism for database serialization failures
- Timezone handling in WebSocket API calls
- Preservation of HA settings after container restart

### Removed

- Test code and unused sensor model
- queue_job dependency

### Documentation

- Comprehensive WebSocket API documentation for history endpoints
- Bus mechanisms comparison guide (useBus vs bus_service.subscribe)
- Research on Home Assistant history record deduplication strategy
- Documentation structure reorganization
- WebSocket subscription implementation documentation (v1.2)
- Last_changed vs last_updated field explanation

### Infrastructure

- Nginx reverse proxy configuration for Odoo with WebSocket support
- Enhanced uninstall hook with comprehensive data cleanup

## [18.0.1.1] - Previous Release

Initial release with basic Home Assistant integration.

### Added

- Basic entity synchronization from Home Assistant
- Dashboard view for entity display
- REST API integration with Home Assistant
- Configuration management for HA connection settings
