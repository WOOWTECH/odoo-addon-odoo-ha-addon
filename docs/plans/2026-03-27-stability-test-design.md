# Stability Test Plan — WOOW Dashboard (odoo_ha_addon)

Created: 2026-03-27T00:14:24Z

## Goal

Comprehensive stability testing of the odoo_ha_addon module covering backend ORM, API endpoints, frontend UI, portal sharing, and bidirectional sync with Home Assistant. Priority on data integrity (CRUD + Odoo↔HA sync).

## Environment

- Odoo 18 at http://localhost:9077 (admin/admin, DB: odoohaiot)
- HA at https://woowtech-ha.woowtech.io (HA 2026.1.2, WebSocket connected)
- 720 entities, 9 areas, 175 devices, 3 labels synced
- Playwright headless + curl API testing

## Test Rounds

### R1: Data Integrity (~100 cases) — HIGHEST PRIORITY

Bidirectional CRUD sync between Odoo and Home Assistant.

- **R1-A: Area CRUD sync** (15 cases) — Create/rename/delete area in Odoo→verify HA, HA→sync→verify Odoo, boundary values
- **R1-B: Entity sync** (25 cases) — State sync, name/area/label updates Odoo→HA, per-domain state comparison, boundary values
- **R1-C: Scene/Script/Automation sync** (25 cases) — Scene CRUD→HA, activate scene, automation toggle/trigger, script run, blueprint wizard
- **R1-D: Device/Label/Tag CRUD** (15 cases) — Registry sync idempotency, device-area/entity relations, label/tag CRUD
- **R1-E: Cross-entity consistency** (20 cases) — Entity-area-device chain verification, batch operations, concurrent modifications

### R2: API Stress (~60 cases)

- **R2-A: Parameter boundary injection** (25 cases) — null/type errors/huge IDs/SQL injection/XSS/malformed JSON
- **R2-B: Load & concurrency** (15 cases) — Rapid-fire requests, concurrent call_service, bulk queries
- **R2-C: Portal API boundary** (20 cases) — Unauthorized access, expired shares, parameter injection, cross-entity attack

### R3: Security & Permission (~40 cases)

- **R3-A: ACL boundary** (15 cases) — No-group user, HA User vs Manager, ir.rule isolation, api_token hiding
- **R3-B: Portal security** (15 cases) — HMAC token, permission escalation, field/service whitelists
- **R3-C: Session & instance isolation** (10 cases) — Instance filter mixin, session expiry fallback

### R4: Frontend Playwright (~50 cases)

- **R4-A: Dashboard loading** (10 cases) — Instance/Area/Glances/Main dashboards, menu navigation
- **R4-B: Entity controllers per domain** (25 cases) — All 9+ domains with real data
- **R4-C: Abnormal state UI** (10 cases) — unavailable/unknown/null attributes/long names
- **R4-D: Portal frontend** (5 cases) — Portal page load, polling, control, permissions

### R5: Integration & Recovery (~30 cases)

- **R5-A: WebSocket reconnect** (10 cases) — restart, consecutive restart, post-reconnect sync
- **R5-B: Full operation sequences** (10 cases) — End-to-end workflows (area lifecycle, scene management, portal sharing)
- **R5-C: Data recovery & consistency** (10 cases) — Sync idempotency, clear+resync, final Odoo↔HA count comparison

## Verification Method

Each CRUD operation verified via triple-check:
1. Odoo ORM (JSON-RPC)
2. HA REST API (direct curl)
3. Controller endpoint

## Output

- `tests/stability/` directory with executable Python scripts
- JSON/text reports in `tests/stability/reports/`
