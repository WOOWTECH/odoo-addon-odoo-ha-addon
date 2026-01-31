# Portal 測試 URLs

ha_user 目前可存取的 Portal 頁面。

## 測試帳號

| 帳號 | 密碼 |
|------|------|
| yujiechen0514@gmail.com | 12341234 |

## 可存取的 Portal 頁面

| Entity | Domain | URL | Permission |
|--------|--------|-----|------------|
| Test Switch3 | switch | http://localhost/portal/entity/51 | Can Control |
| Test Lights | light | http://localhost/portal/entity/50 | Can Control |
| Test Fan 測試風扇 | fan | http://localhost/portal/entity/49 | Can Control |
| Test Cover cover | cover | http://localhost/portal/entity/48 | Can Control |
| 多切開關控制燈具 | automation | http://localhost/portal/entity/44 | Can Control |
| test2 | scene | http://localhost/portal/entity/32 | Can Control |
| notify | script | http://localhost/portal/entity/29 | Can Control |
| Backup 備份管理器狀態 | sensor | http://localhost/portal/entity/24 | Can Control |

## 快速測試

1. 用 ha_user 登入後直接訪問上述 URL
2. 或從 http://localhost/my/home 進入 Portal 首頁

## 新增測試 Entity

如需測試其他 domain（如 fan、cover、sensor 等），需用 admin 帳號：
1. 登入 admin/admin
2. 導航到對應 entity 的 form view
3. 點擊 "Share with Users" 按鈕
4. 選擇 ha user，設定權限為 "Can Control"
5. 點擊 Share
