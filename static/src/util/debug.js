/** @odoo-module */

/**
 * Debug utilities for conditional logging
 * Set ENABLE_DEBUG to false in production to disable all debug logs
 */
const ENABLE_DEBUG = true;

/**
 * Debug log (replaces console.log)
 * @param {...any} args - Arguments to log
 */
export function debug(...args) {
  ENABLE_DEBUG && console.log(...args);
}

/**
 * Debug warning (replaces console.warn)
 * @param {...any} args - Arguments to log
 */
export function debugWarn(...args) {
  ENABLE_DEBUG && console.warn(...args);
}

/**
 * Debug info (replaces console.info)
 * @param {...any} args - Arguments to log
 */
export function debugInfo(...args) {
  ENABLE_DEBUG && console.info(...args);
}
