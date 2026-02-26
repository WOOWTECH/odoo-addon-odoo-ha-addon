---
name: entity-follows-device-area
description: 實體分區跟隨裝置分區功能
status: in-progress
created: 2026-02-26T02:11:09Z
updated: 2026-02-26T02:15:29Z
---

# Entity Follows Device Area

## 概述

讓 Odoo HA 整合中的實體分區行為與 Home Assistant 一致：當 HA 實體設定為「跟隨裝置分區」時，Odoo 中也能正確顯示並處理此設定。

## 問題背景

### 現況
- Home Assistant 允許實體設定「跟隨裝置分區」
- 當實體設定為跟隨裝置分區時，HA 的 entity registry API 回傳 `area_id = null`
- 目前 Odoo HA 整合直接儲存此 null 值，導致實體顯示為「無分區」

### 影響
- 使用者無法在 Odoo 中看到實體的實際分區
- 分區相關的篩選和分類功能失效
- 與 Home Assistant 的行為不一致，造成使用者困惑

## 功能需求

### 核心功能

1. **新增欄位**
   - `follows_device_area`: 布林欄位，標記實體是否跟隨裝置分區
   - `display_area_id`: 計算欄位，顯示實際分區（自己的或繼承裝置的）

2. **UI 變更**
   - 在分區欄位旁加入「跟隨裝置分區」勾選框
   - 勾選時，分區欄位變為唯讀
   - 勾選框只在實體有關聯裝置時顯示

3. **同步邏輯**
   - HA → Odoo: 當 `area_id = null` 且 `device_id != null` 時，設定 `follows_device_area = True`
   - Odoo → HA: 勾選時同步 `area_id = null`，取消勾選時同步選擇的分區

### 行為規格

| follows_device_area | device_id | 顯示的分區 | 分區欄位狀態 |
|---------------------|-----------|------------|--------------|
| True | 裝置A (廚房) | 廚房 | 唯讀 |
| True | null | 無 | 唯讀 |
| False | 任意 | area_id 的值 | 可編輯 |

## 技術設計

### 檔案變更

**後端 (Python)**
- `models/ha_entity.py`: 新增欄位和計算邏輯
- `views/ha_entity_views.xml`: 新增 UI 元素

**國際化**
- 新增繁體中文翻譯：「跟隨裝置分區」

### 詳細設計
參見: `docs/plans/2026-02-26-entity-follows-device-area-design.md`

## 驗收標準

1. [ ] 同步有 `area_id = null` 且有 `device_id` 的實體時，`follows_device_area = True`
2. [ ] 同步有 `area_id` 的實體時，`follows_device_area = False`
3. [ ] 勾選「跟隨裝置分區」後，同步 `area_id = null` 至 HA
4. [ ] 取消勾選並選擇分區後，同步選擇的分區至 HA
5. [ ] 裝置分區變更時，跟隨的實體 `display_area_id` 自動更新
6. [ ] 當 `follows_device_area = True` 時，分區欄位為唯讀
7. [ ] 當實體無關聯裝置時，勾選框隱藏
8. [ ] 繁體中文翻譯正確顯示

## 優先順序

**高** - 此功能影響基本的分區顯示正確性

## 相關連結

- 設計文件: `docs/plans/2026-02-26-entity-follows-device-area-design.md`
