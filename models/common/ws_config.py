# -*- coding: utf-8 -*-
"""
WebSocket Configuration Module

Centralized configuration for WebSocket timeouts and retry parameters.
This module provides a single source of truth for all timeout values
used across the Home Assistant WebSocket integration.
"""

# ============================================================================
# Connection Timeouts
# ============================================================================

# WebSocket connection close timeout (seconds)
WS_CLOSE_TIMEOUT = 5

# Authentication handshake timeout (seconds)
WS_AUTH_TIMEOUT = 5

# Initial connection timeout for service startup (seconds)
WS_CONNECT_TIMEOUT = 5


# ============================================================================
# API Request Timeouts
# ============================================================================

# Default timeout for general WebSocket API calls (seconds)
WS_DEFAULT_TIMEOUT = 10

# Timeout for controller API calls (seconds)
WS_CONTROLLER_TIMEOUT = 15

# Timeout for portal/public API calls (seconds)
WS_PORTAL_TIMEOUT = 10


# ============================================================================
# Registry Operations Timeouts
# ============================================================================

# Area registry list timeout (seconds)
WS_AREA_LIST_TIMEOUT = 15

# Area create/update timeout (seconds)
WS_AREA_CREATE_TIMEOUT = 10

# Device registry list timeout (seconds)
WS_DEVICE_LIST_TIMEOUT = 15

# Device update timeout (seconds)
WS_DEVICE_UPDATE_TIMEOUT = 15

# Label registry list timeout (seconds)
WS_LABEL_LIST_TIMEOUT = 10

# Entity registry timeout (seconds)
WS_ENTITY_REGISTRY_TIMEOUT = 10


# ============================================================================
# Service Call Timeouts
# ============================================================================

# Service call timeout for actions (seconds)
WS_SERVICE_CALL_TIMEOUT = 10

# Scene/Script execution timeout (seconds)
WS_SCENE_TIMEOUT = 15


# ============================================================================
# History Operations
# ============================================================================

# History stream subscription timeout (seconds)
WS_HISTORY_STREAM_TIMEOUT = 60

# Single entity history fetch timeout (seconds)
WS_HISTORY_FETCH_TIMEOUT = 60

# Batch history futures timeout (seconds)
WS_HISTORY_BATCH_TIMEOUT = 90


# ============================================================================
# Thread/Process Management
# ============================================================================

# Thread join timeout when stopping services (seconds)
WS_THREAD_JOIN_TIMEOUT = 10

# Sleep interval for retry loops (seconds)
WS_RETRY_SLEEP = 1

# Brief delay for HA to process operations (seconds)
WS_PROCESS_DELAY = 0.5

# Short polling delay (seconds)
WS_POLL_DELAY_SHORT = 0.3

# Standard polling delay (seconds)
WS_POLL_DELAY_STANDARD = 0.5


# ============================================================================
# REST API Timeouts (for sync operations via HTTP)
# ============================================================================

# REST API response timeout (seconds)
REST_API_TIMEOUT = 10

# REST API with scene/service execution (seconds)
REST_API_SERVICE_TIMEOUT = 30

# REST API future result timeout (seconds)
REST_API_FUTURE_TIMEOUT = 15

# REST API extended future timeout (seconds)
REST_API_FUTURE_EXTENDED_TIMEOUT = 35


# ============================================================================
# Odoo Cron Worker Limits (Reference Documentation)
# ============================================================================
# Odoo WorkerCron has a 120s hard limit per cron job execution.
# Heavy sync operations (full entity + device + history) may approach this.
# After timeout, HTTP sessions may reset, causing [Errno 104] errors.
#
# Known behavior:
# - WebSocket retry handles reconnection automatically (5 attempts, backoff)
# - HTTP session needs re-authentication after cron worker restart
# - This is infrastructure-level, not a code bug
#
# Mitigation:
# 1. Registry sync operations have individual timeouts (15s each)
# 2. History sync is capped at WS_HISTORY_BATCH_TIMEOUT (within limit)
# 3. Breaking syncs into smaller batches prevents worker timeout
ODOO_CRON_WORKER_TIMEOUT = 120  # Reference only, cannot change via code
