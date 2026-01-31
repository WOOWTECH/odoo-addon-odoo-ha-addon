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
- Create/modify entity groups and tags
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
- WebSocket service management

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
| **Public Groups** | Entity groups with `user_ids = False` are accessible to all HA users |
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
