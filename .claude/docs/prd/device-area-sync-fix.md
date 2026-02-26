---
name: device-area-sync-fix
description: 修復裝置分區同步問題 - 確保裝置正確繼承 HA 分區
status: complete
created: 2026-02-26T03:02:15Z
updated: 2026-02-26T03:05:32Z
---

# Device Area Sync Fix

## 概述

修復裝置同步時分區資訊遺失的問題。當 HA 中的 Area 在 Odoo 不存在時，Device 同步會遺失分區資訊。

## 問題分析

### 現況
- Odoo 中共有 162 個裝置
- 33 個裝置有分區 (20%)
- 129 個裝置沒有分區 (80%)

### 調查結果

經過直接查詢 HA WebSocket API 確認：

1. **HA 中的裝置確實有 129 個沒有分區**
   - 這不是同步問題，而是 HA 中的實際狀態
   - 例如：`Athom Energy Monitor 029d10` 在 HA 中 `area_id: None`

2. **需要修復的問題**
   - 當 HA 的 area_id 在 Odoo 不存在時，原本會記錄警告並跳過
   - 這會導致某些裝置的分區丟失

### 影響

- 實體設定為「跟隨裝置分區」時，如果裝置沒有分區，`display_area_id` 正確顯示為空
- 這是預期行為，不是 bug

## 解決方案

### 已實作：Area 自動建立

修改 `sync_device_from_ha_data` 和 `_do_sync_entity_registry_relations` 方法：
- 當 Device/Entity 引用的 area_id 在 Odoo 不存在時，自動建立 Area 記錄
- 使用 area_id 作為臨時名稱
- 下次 Area 同步時會更新正確名稱

### 修改的檔案

1. **`models/ha_device.py`** - `sync_device_from_ha_data` 方法
2. **`models/ha_entity.py`** - `_do_sync_entity_registry_relations` 方法

## 測試結果

### 2026-02-26 測試

**HA 原始資料確認：**
```
=== HA Device Area Summary ===
  With area: 33
  Without area: 129

=== Athom Devices in HA ===
  Name: Athom Energy Monitor 029d10
    area_id: None  <-- HA 中確實沒有設定分區
```

**結論：**
- Odoo 的資料與 HA 一致
- 129 個裝置沒有分區是因為 HA 中就沒有設定
- 實體的 `display_area_id` 顯示為空是正確行為

## 驗收標準

1. [x] Device 同步後，所有在 HA 有分區的裝置，在 Odoo 也有對應分區
2. [x] 當 Device 引用不存在的 area 時，自動建立 Area 記錄
3. [x] 實體的 `display_area_id` 能正確顯示裝置的分區（如果裝置有分區）
4. [x] 同步資料與 HA 一致

## 用戶操作建議

如果希望實體顯示分區，需要在 Home Assistant 中：
1. 進入 Settings > Devices & Services
2. 找到裝置（如 Athom Energy Monitor）
3. 設定裝置的 Area
4. Odoo 會在下次同步時取得新的分區資訊

## 優先順序

**已完成** - 同步功能正常，資料與 HA 一致

## 相關功能

- [Entity Follows Device Area](entity-follows-device-area.md) - 實體跟隨裝置分區功能
