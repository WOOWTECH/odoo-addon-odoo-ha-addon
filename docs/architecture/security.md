# Security Architecture

This document describes the security architecture of the Odoo HA Addon.

## Two-Tier Permission Design

Following Point of Sale module pattern, the addon implements a dedicated group-based permission system instead of binding directly to Odoo's base groups. This follows the **Principle of Least Privilege** - users must be explicitly granted HA access.

## Permission Groups

### 1. `group_ha_user` (Home Assistant User)

**Purpose**: Basic access to authorized HA data

**Location**: Settings > Users & Companies > Groups > Administration / Home Assistant User

**Access Rights**:
- Read authorized instances (via entity groups)
- Read authorized entities (via entity groups)
- Read entity history for authorized entities
- Read areas from authorized instances
- Read authorized entity groups and group tags (read-only; only HA Managers can create/modify/delete them, because group membership is the authorization source)
- Call Home Assistant services only on entities visible through their entity groups, within the domain/service whitelist (no `homeassistant`, `hassio`, `shell_command`, `script`, `automation`, `update`, ...); target selectors (`area_id`, `device_id`, `floor_id`, `label_id`, `target`) are dropped
- Receive realtime bus notifications only for entities/instances they are authorized for (entity-group members must still be in `group_ha_user`); users who only hold an `ha.entity.share`, and HA Users who reach an entity only through a public group (no `user_ids`), get the portal attribute policy on the bus too (no `access_token`, `token`, GPS coordinates, ... and no token in `entity_picture`)
- HA registry sync helpers (`_sync_device_from_ha_data`, `_sync_area_from_ha_data`, `_sync_label_from_ha_data`, `_sync_area_from_ha_event`, `_get_or_create_labels`) are private and cannot be called through RPC
- Cannot modify instances, entities, or areas (read-only)

**Assignment**: Must be explicitly granted to users who need HA access

### 2. `group_ha_manager` (Home Assistant Manager)

**Purpose**: Full HA management capabilities

**Location**: Settings > Users & Companies > Groups > Administration / Home Assistant Manager

**Access Rights**:
- All permissions from `group_ha_user` (via `implied_ids`)
- Create/modify/delete HA instances
- Manage instance configurations and credentials
- Full access to all instances, entities, and areas
- WebSocket service management (restart, start/stop) and full HA synchronisation
- Create/modify/delete entity groups and group tags (authorize HA Users)

**Inheritance**: Automatically includes `base.group_user` + `group_ha_user`

## Permission Architecture Comparison

```
Old Design (Too Permissive):
base.group_user (ALL internal users) -> Automatic HA access
base.group_portal (ALL portal users) -> Automatic HA access

New Design (Explicit Authorization):
base.group_user -> No HA access by default
    | (must be explicitly granted)
group_ha_user -> Basic HA access to authorized data
    | (automatically included via implied_ids)
group_ha_manager -> Full HA management
```

## Access Control Implementation

### Model-Level

`security/ir.model.access.csv` - Controls CRUD operations on models

### Record-Level

`security/security.xml` - 12 `ir.rule` records control which records users can access:
- **User rules**: Filter data based on `user.ha_entity_group_ids` (group-based access)
- **Manager rules**: Full access to all records (`domain_force: [(1, '=', 1)]`)

## Key Security Features

| Feature | Description |
|---------|-------------|
| **Group-Based Authorization** | Users access instances/entities through authorized entity groups |
| **Cascade Permissions** | Entity groups -> Entities -> History -> Areas |
| **Public Groups** | Entity groups with `user_ids = False` are treated as public for realtime bus notifications: every HA User receives the sanitized (portal-policy) state of their entities. The ORM record rules only follow explicit membership (`user.ha_entity_group_ids`), so public-group entities are not readable through the ORM by non-members |
| **Portal Control** | `/my/ha/<instance>/entity/<id>/service` needs a non-expired `control` share, the URL instance must be the entity's instance and `domain == entity.domain`; the CONTROL_SERVICES whitelist applies (script, automation and update entities can be controlled when explicitly shared), target selectors and unknown parameters are dropped and numbers must be finite |
| **Share Revocation** | Deleting or expiring an `ha.entity.share` resets the `access_token` of the shared entity / group / device. Other share holders of the same record keep access; their embedded chatter token is regenerated on their next page view |
| **HA Host Details** | `/odoo_ha_addon/ha_urls` (internal / external / cloud URLs), `hardware_info` and `network_info` are HA Manager only. `/odoo_ha_addon/websocket_status` returns the connection state to every user who can read the instance, but `current_url` / `has_token` only to managers (others get `url_hidden: true`). Note: `ha.instance.api_url` itself is still a plain field readable by HA Users through the ORM and `/odoo_ha_addon/instances` |
| **Sharing** | `action_share` (entity / group / device) and `ha.entity.share.wizard` are HA Manager only; the wizard requires exactly one target. Legacy `/portal/entity/<id>` and `/portal/entity_group/<id>` URLs redirect to the canonical page only with a valid share, otherwise to the user's own `/my/ha` hub (unknown ids behave the same) |
| **Read-Only Entities** | Entity data synced from HA, only admin can modify (via WebSocket service) |
| **Session-Based Instance** | Current instance stored in user session, validated on each request |

## Best Practices

1. **For Regular Users**: Grant only `group_ha_user`, then authorize specific entity groups
2. **For Administrators**: Grant `group_ha_manager` for full control
3. **For Portal Users**: Grant `group_ha_user` for limited read-only dashboard access
4. **Security Principle**: Always assign minimum required permissions

## Reference Files

- `security/security.xml` - Group definitions and 12 record rules
- `security/ir.model.access.csv` - Model-level access control (12 entries)
