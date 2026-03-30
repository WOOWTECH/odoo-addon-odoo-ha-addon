/** @odoo-module **/

/**
 * 應用程式常數定義
 *
 * 統一管理時間間隔、快取設定等魔術數字，
 * 便於維護和調整。
 */

// ============================================
// 快取設定
// ============================================

/** 資料快取過期時間 (毫秒) */
export const CACHE_TIMEOUT_MS = 30000; // 30 秒

// ============================================
// 定時刷新間隔
// ============================================

/** WebSocket 狀態刷新間隔 (毫秒) */
export const WEBSOCKET_STATUS_REFRESH_MS = 10000; // 10 秒

/** Glances 設備列表刷新間隔 (毫秒) */
export const GLANCES_REFRESH_MS = 30000; // 30 秒

/** Glances 設備詳情刷新間隔 (毫秒) */
export const GLANCES_DEVICE_REFRESH_MS = 10000; // 10 秒

/** 硬體資訊刷新間隔 (毫秒) */
export const HARDWARE_INFO_REFRESH_MS = 300000; // 5 分鐘

/** 網路資訊刷新間隔 (毫秒) */
export const NETWORK_INFO_REFRESH_MS = 300000; // 5 分鐘

/** HA URLs 刷新間隔 (毫秒) */
export const HA_URLS_REFRESH_MS = 300000; // 5 分鐘

// ============================================
// Chart.js 圖表設定
// ============================================

/** Timeline 圖表：顯示標籤的最小區塊寬度 (像素) */
export const MIN_BAR_WIDTH_FOR_LABEL = 30;

/** Timeline 圖表：Bar 佔 category 的比例 */
export const TIMELINE_BAR_PERCENTAGE = 0.9;

/** Timeline 圖表：Category 佔可用空間的比例 */
export const TIMELINE_CATEGORY_PERCENTAGE = 0.9;

/** Timeline 圖表：Bar 最大厚度 (像素) */
export const TIMELINE_MAX_BAR_THICKNESS = 60;

/** Timeline 圖表：標籤字體大小 */
export const TIMELINE_LABEL_FONT_SIZE = 10;

/** 無效狀態的虛線樣式 [dash, gap] */
export const UNAVAILABLE_DASH_PATTERN = [5, 5];
