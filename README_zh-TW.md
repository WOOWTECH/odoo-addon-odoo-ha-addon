<p align="center">
  <img src="https://img.shields.io/badge/Odoo-18.0-875A7B?style=for-the-badge&logo=odoo&logoColor=white" alt="Odoo 18"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/License-LGPL--3-blue?style=for-the-badge" alt="LGPL-3"/>
  <img src="https://img.shields.io/badge/Home_Assistant-2024.1+-41BDF5?style=for-the-badge&logo=homeassistant&logoColor=white" alt="Home Assistant"/>
  <img src="https://img.shields.io/badge/WebSocket-即時通訊-010101?style=for-the-badge&logo=socketdotio&logoColor=white" alt="WebSocket"/>
  <img src="https://img.shields.io/badge/OWL-前端框架-714B67?style=for-the-badge" alt="OWL"/>
</p>

<h1 align="center">WOOW Dashboard</h1>

<p align="center">
  <strong>Odoo 18 ERP 的 Home Assistant 整合模組</strong><br/>
  在 Odoo 後台與 Portal 中即時監控、操作與分享 IoT 裝置。
</p>

<p align="center">
  <code>v18.0.6.2</code> &nbsp;·&nbsp;
  <a href="#畫面截圖">畫面截圖</a> &nbsp;·&nbsp;
  <a href="#安裝方式">安裝方式</a> &nbsp;·&nbsp;
  <a href="#設定說明">設定說明</a> &nbsp;·&nbsp;
  <a href="README.md">English</a>
</p>

---

## 為什麼選擇 WOOW Dashboard？

| 挑戰 | 解決方案 |
|---|---|
| IoT 資料被鎖在 Home Assistant 中 | 在 ERP 內建立統一儀表板 |
| 缺乏企業級的裝置分享機制 | 基於使用者的 Portal 分享，支援細粒度權限控制 |
| 分散的監控工具 | 即時 WebSocket 橋接 — 無需輪詢 |
| 多站點 HA 部署 | 多實例管理，支援 Session 切換 |
| 裝置狀態缺乏稽核記錄 | 實體歷史記錄與圖表視覺化 |

---

## 概述

WOOW Dashboard 將 **Home Assistant** 與 **Odoo ERP** 無縫整合，讓您在企業管理平台中即時監控、操作與分享 IoT 裝置。模組透過 WebSocket 與 REST API 連接一個或多個 Home Assistant 實例，同步實體、區域與裝置資料，並透過 Odoo 後台介面與入口網站（Portal）呈現給使用者。

無論您管理的是智慧辦公室、工業感測器群組，還是樓宇自動化系統，WOOW Dashboard 都能讓您的團隊在 Odoo 內直接監控和操作 IoT 裝置，並透過安全的 Portal 機制將裝置存取權限分享給外部使用者。

---

## 功能特色

### 核心整合

- **Home Assistant 整合** — 透過 WebSocket 與 REST API 進行即時雙向通訊，支援自動重連與狀態同步。
- **多實例管理** — 在單一 Odoo 安裝中連接並管理多個 Home Assistant 實例。支援基於 Session 的實例切換與使用者偏好記憶。
- **即時更新** — Home Assistant 的狀態變化透過 Odoo Bus Bridge 串流至瀏覽器，無需輪詢即可即時更新介面。

### 實體管理

- **實體管理與控制** — 完整支援 10 種裝置類型：開關、燈光、感測器、空調、窗簾、風扇、自動化、場景、腳本，以及通用類型。
- **實體看板視圖** — 自訂 Odoo 看板視圖，即時顯示狀態、依類型呈現控制元件，支援行內互動。
- **實體歷史記錄** — 記錄並視覺化實體狀態變化，提供專屬的圖表時間軸視圖。

### 裝置與區域管理

- **區域與裝置管理** — 與 Home Assistant 雙向同步區域和裝置資料。視覺化區域儀表板以裝置卡片呈現，並嵌入實體控制器。
- **裝置區域繼承** — 實體自動繼承其父裝置的區域，可透過「跟隨裝置」開關進行細粒度控制。
- **Glances 系統監控** — 在 Odoo 內直接查看 Home Assistant 主機的系統指標（CPU、記憶體、磁碟、網路），透過 Glances 整合實現。

### Portal 分享

- **Portal 分享機制** — 將實體與實體群組分享給 Portal 使用者。支援使用者層級的權限管理，可設定唯讀或完整控制，並支援到期日設定。
- **Portal 實體控制** — 在 Portal 上提供與後台相同的裝置控制元件，適配公開存取需求。

### 進階功能

- **Blueprint 精靈** — 透過引導式表單，在 Odoo 中直接從 Blueprint 建立 Home Assistant 自動化。
- **多語系支援** — 完整的繁體中文（zh_TW）翻譯覆蓋率。後台與 Portal 介面皆支援多語系顯示。
- **自訂視圖** — 專為 IoT 設計的 Odoo 視圖，包含實體歷史時間軸、即時狀態看板，以及以裝置為中心的區域儀表板。

---

## 支援的實體類型

| 類型 | 功能 |
|---|---|
| **switch**（開關） | 開啟/關閉切換 |
| **light**（燈光） | 開關切換、亮度調整、色溫控制 |
| **sensor**（感測器） | 唯讀數值顯示與屬性 |
| **climate**（空調） | 目標溫度、空調模式、風扇模式 |
| **cover**（窗簾） | 開啟、關閉、停止、位置滑桿 |
| **fan**（風扇） | 開關切換、風速控制、擺動 |
| **automation**（自動化） | 啟用/停用切換、手動觸發 |
| **scene**（場景） | 啟動場景 |
| **script**（腳本） | 執行、開關切換 |
| **generic**（通用） | 基本狀態顯示，適用於未支援的類型 |

---

## 畫面截圖

### 實例儀表板

入口頁面，顯示已連線的 Home Assistant 實例、連線狀態、實體/區域數量與快速導覽按鈕。

<p align="center">
  <img src="docs/screenshots/instance_dashboard.png" alt="實例儀表板" width="720"/>
</p>

### HA 資訊儀表板

系統資訊面板，顯示 WebSocket 連線狀態、硬體資訊、儲存空間與網路監控。

<p align="center">
  <img src="docs/screenshots/ha_info_dashboard.png" alt="HA 資訊儀表板" width="720"/>
</p>

### 區域儀表板

依 Home Assistant 區域分類的裝置卡片，提供區域分頁。每張卡片內嵌實體控制器，可直接互動 — 切換燈光、啟動場景、調整設定。

<p align="center">
  <img src="docs/screenshots/area_dashboard.png" alt="區域儀表板" width="720"/>
</p>

<p align="center">
  <img src="docs/screenshots/area_dashboard_controls.png" alt="區域儀表板控制元件" width="720"/>
</p>

### 實體列表與看板

所有已同步的實體，即時顯示狀態，支援依類型篩選、區域指派與群組/標籤管理。可切換列表與看板視圖。

<p align="center">
  <img src="docs/screenshots/entity_list.png" alt="實體列表" width="720"/>
</p>

<p align="center">
  <img src="docs/screenshots/entity_kanban.png" alt="實體看板" width="720"/>
</p>

### 實體表單

詳細的實體頁面，顯示狀態、類型、區域指派（含「跟隨裝置」開關）、群組、標籤與自訂屬性。包含「分享給使用者」操作按鈕。

<p align="center">
  <img src="docs/screenshots/entity_form.png" alt="實體表單" width="720"/>
</p>

### 裝置管理

所有 Home Assistant 裝置，顯示製造商、型號、區域指派與關聯實體。

<p align="center">
  <img src="docs/screenshots/device_list.png" alt="裝置列表" width="720"/>
</p>

### 實例設定

HA 實例表單，包含連線設定、同步控制（測試連線、同步 Registry、同步實體、重啟 WebSocket）與實例識別資訊。

<p align="center">
  <img src="docs/screenshots/ha_instance_form.png" alt="HA 實例設定" width="720"/>
</p>

### 系統設定

WebSocket 設定頁面，包含連線狀態、實例管理、API URL 與存取權杖設定。

<p align="center">
  <img src="docs/screenshots/settings.png" alt="系統設定" width="720"/>
</p>

### Portal 使用者介面

Portal 使用者可透過安全的響應式介面查看和控制已分享的實體。

| 截圖 | 說明 |
|:---:|---|
| ![Portal 首頁](docs/screenshots/portal/01-portal-home.png) | **Portal 首頁** — 使用者的 Portal 登入頁，包含已分享實例摘要。 |
| ![實例列表](docs/screenshots/portal/02-instance-list.png) | **實例列表** — 已分享的 HA 實例，顯示實體與群組數量。 |
| ![實例詳情](docs/screenshots/portal/03-instance-detail.png) | **實例詳情** — 已分享的實體與權限等級標示。 |
| ![實體控制](docs/screenshots/portal/04-entity-control.png) | **實體控制** — 燈光實體，含亮度滑桿與開關切換。 |
| ![實體群組](docs/screenshots/portal/05-entity-group.png) | **實體群組** — 響應式卡片網格，每張卡片附有獨立控制器。 |
| ![感測器檢視](docs/screenshots/portal/06-entity-sensor.png) | **感測器檢視** — 唯讀感測器，顯示數值、量測單位與屬性。 |

---

## 系統架構

```
┌───────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  瀏覽器 (OWL)     │  <───>  │   Odoo 伺服器    │  <───>  │  Home Assistant   │
├───────────────────┤         ├──────────────────┤         ├──────────────────┤
│ OWL 元件          │         │ Models           │         │ WebSocket API    │
│ ha_data_service   │  RPC    │ ha_entity        │  WS/    │ REST API         │
│ ha_bus_bridge     │ <────>  │ ha_instance      │  REST   │ State Machine    │
│ Entity Controllers│         │ ha_area/device   │ <────>  │                  │
│ Chart Service     │         │ HA API Client    │         │                  │
└───────────────────┘         └──────────────────┘         └──────────────────┘
        ▲                             │
        │     Odoo Bus Bridge         │
        └─────────────────────────────┘
             (即時狀態傳播)
```

### 資料流向

- **後端**：Odoo 模型透過專屬的 API Client 與 Home Assistant 通訊，同時支援 WebSocket 訂閱與 REST 呼叫。
- **前端**：OWL 元件透過服務層（`ha_data_service`）消費資料，處理 RPC 呼叫、快取與響應式狀態管理。
- **即時更新**：WebSocket Bridge 訂閱 Home Assistant 的狀態變化，並透過 Odoo Bus 轉發至所有已連線的瀏覽器 Session。
- **Portal**：專屬控制器提供 Portal 頁面，透過使用者權限驗證存取，並經由相同的後端 API Client 取得實體狀態。

### 關鍵設計模式

| 模式 | 用途 |
|---|---|
| **服務優先** | 使用 `useService("ha_data")`，不直接呼叫 RPC |
| **Bus 通知** | 使用 `bus_service.subscribe()` 接收即時更新 |
| **響應式狀態** | `useState()` + 服務回調 |
| **實體控制** | 後台與 Portal 共用 `useEntityControl` Hook |

---

## 安裝方式

### 系統需求

| 元件 | 版本 |
|---|---|
| Odoo | 18.0+（Community 或 Enterprise） |
| Home Assistant | 2024.1+ |
| Python | 3.10+ |
| websockets | 透過 `pre_init_hook` 自動安裝 |

### Odoo 模組相依性

- `base`、`web`、`mail`、`portal`

### 從原始碼安裝

本儲存庫本身**即為** Odoo 模組。直接 Clone 或下載至您的 Odoo addons 目錄即可使用：

```bash
# Clone 到 Odoo addons 路徑，重新命名為 odoo_ha_addon
git clone https://github.com/WOOWTECH/odoo-addon-odoo-ha-addon.git \
  /path/to/odoo/addons/odoo_ha_addon

# 或從 GitHub Releases 下載 ZIP 並解壓縮
```

然後在 Odoo 中：

1. 前往 **應用程式**，點選 **更新應用程式列表**
2. 搜尋並安裝 **WOOW Dashboard**

> Python 相依套件 `websockets` 會透過 `pre_init_hook` 自動安裝，無需手動執行 pip install。

### 使用 Docker（開發環境）

```bash
# 複製儲存庫
git clone https://github.com/WOOWTECH/odoo-addon-odoo-ha-addon.git
cd odoo-addon-odoo-ha-addon

# 設定環境
cp .env.example .env

# 啟動服務
docker compose up -d

# 存取 Odoo：http://localhost:8069
```

---

## 設定說明

1. 前往 **設定** > **WOOW HA**
2. 點選 **+ 新增實例**，填入以下資訊：
   - **實例名稱**：Home Assistant 實例的描述性標籤
   - **API URL**：Home Assistant 的基礎網址（例如 `http://homeassistant.local:8123`）
   - **存取權杖**：在 Home Assistant 中產生的[長期存取權杖](https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token)
3. 點選 **測試連線** 以驗證連線狀態
4. 點選 **同步 Registry** 以匯入區域、裝置與標籤
5. 點選 **同步實體** 以匯入所有實體

WebSocket 連線將自動建立，提供即時狀態更新。

---

## 專案結構

```
odoo_ha_addon/                   # ← 本儲存庫（Clone 後命名為 odoo_ha_addon）
├── __manifest__.py              # Odoo 模組描述檔（v18.0.6.2）
├── __init__.py                  # Python 套件初始化
├── hooks.py                     # 安裝/移除 Hook
├── models/                      # 後端模型與商業邏輯
│   ├── common/                  # 共用工具（API Client、Helper）
│   ├── ha_instance.py           # HA 實例管理
│   ├── ha_entity.py             # 實體模型與 WebSocket 同步
│   ├── ha_area.py               # 區域雙向同步
│   ├── ha_device.py             # 裝置管理
│   ├── ha_entity_share.py       # Portal 分享模型
│   └── ...                      # 其他模型
├── controllers/                 # HTTP 與 Portal 控制器
├── views/                       # XML 視圖定義與模板
├── static/src/                  # 前端（OWL 元件、JS、SCSS）
│   ├── services/                # 服務層（ha_data、chart、bus bridge）
│   ├── actions/                 # Client Action 頁面（儀表板）
│   ├── views/                   # 自訂視圖類型（hahistory、entity_kanban）
│   ├── components/              # 可重用 UI 元件
│   ├── portal/                  # Portal 專屬元件
│   └── hooks/                   # 共用 Hooks（實體控制）
├── security/                    # 存取權限與記錄規則
├── data/                        # 初始資料、選單、排程任務
├── i18n/                        # 翻譯檔案（zh_TW）
├── wizard/                      # 精靈視圖（Blueprint、清除實例）
├── tests/                       # 單元、整合與 E2E 測試
├── docs/                        # 技術文件與截圖
├── scripts/                     # 開發自動化腳本
├── config/                      # Docker 與 Nginx 設定
├── docker-compose.yml           # Docker 開發環境
├── CHANGELOG.md                 # 版本更新紀錄（英文）
└── CHANGELOG-tw.md              # 版本更新紀錄（繁體中文）
```

---

## 安全性

### 雙層權限架構

- **後台存取**：HA Admin 與 HA User 群組，搭配記錄層級的安全規則。管理員可管理實例與同步資料；使用者可查看和控制指派的實體。
- **Portal 存取**：基於使用者的分享機制，提供每個實體和群組的權限記錄。支援唯讀和完整控制的存取層級，並支援到期日設定。

### API 安全性

- 所有 Home Assistant API 呼叫使用長期存取權杖，儲存在 Odoo 的加密憑證庫中
- Portal 實體存取透過 `hmac.compare_digest()` 驗證分享記錄，防止計時攻擊
- WebSocket 連線使用認證 Session，支援自動 Token 輪換

---

## API 參考

所有後端 API 端點採用統一的回應格式：

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### 主要端點

| 端點 | 方法 | 說明 |
|---|---|---|
| `/ha/entity/state` | POST | 取得實體當前狀態 |
| `/ha/entity/control` | POST | 發送控制指令至實體 |
| `/ha/instance/sync` | POST | 觸發實體同步 |
| `/portal/entity/<id>/state` | GET | Portal 實體狀態（JSON 輪詢） |

完整 API 文件請參閱 [docs/architecture/overview.md](docs/architecture/overview.md)。

---

## 測試

```bash
# 執行單元測試
python -m pytest tests/ -v

# 使用 Odoo 測試執行器
./odoo-bin -d test_db -i odoo_ha_addon --test-enable --stop-after-init

# E2E 測試（Playwright）
# 請參閱 tests/e2e_tests/ 了解設定方式
```

---

## 更新紀錄

完整版本更新紀錄請參閱 [CHANGELOG-tw.md](CHANGELOG-tw.md)。

### 近期重點更新

- **v18.0.6.2** — Portal 麵包屑導覽、即時狀態側欄、實體表單控制面板
- **v18.0.6.1** — 使用者層級分享遷移（Token → 使用者權限）
- **v18.0.6.0** — Portal 分享系統、實體群組、Portal 控制器
- **v18.0.5.0** — Blueprint 精靈、Glances 整合、實體歷史

---

## 貢獻指南

歡迎提交貢獻。請遵循以下流程：

1. Fork 此儲存庫
2. 建立功能分支（`git checkout -b feature/your-feature`）
3. 以清晰的訊息提交變更
4. 確保所有測試通過
5. 提交 Pull Request

開發環境設定詳情，請參閱[開發指南](docs/guides/development.md)。

---

## 授權條款

本專案採用 **GNU 較寬鬆通用公共授權條款 v3.0（LGPL-3）** 授權。

詳情請參閱 [LICENSE](https://www.gnu.org/licenses/lgpl-3.0.html)。

---

## 支援

- **問題回報**：[GitHub Issues](https://github.com/WOOWTECH/odoo-addon-odoo-ha-addon/issues)
- **技術文件**：[docs/](docs/)
- **開發指南**：[docs/guides/development.md](docs/guides/development.md)
- **疑難排解**：[docs/guides/troubleshooting.md](docs/guides/troubleshooting.md)

---

<p align="center">
  由 <strong><a href="https://github.com/WOOWTECH">WOOWTECH</a></strong> 開發與維護
</p>
