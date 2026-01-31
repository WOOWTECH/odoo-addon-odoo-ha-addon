# WebSocket 並發控制優化任務

## 任務背景

當前 WebSocket 實作已達到 95% 的無序回應處理能力，核心機制使用 `_pending_requests` 字典以 message ID 為鍵值配對請求和回應，不依賴回應順序。但缺少並發控制機制，這是剩餘的 5%。

## 目前實作狀態

### 已完成（95%）

1. **ID 配對機制**
   - 使用 `self._pending_requests = {}` 儲存 `{message_id: asyncio.Future}` 配對
   - 發送請求時建立 Future 並存入字典
   - 收到回應時透過 ID 查找對應的 Future 並完成等待

2. **無序處理**
   - 完全基於 ID 匹配，不依賴回應順序
   - 可同時處理多個未完成的請求
   - 支援陣列回應處理

3. **協定符合度**
   - ✅ ID 管理：100%
   - ✅ 認證流程：100%
   - ✅ 請求-回應配對：100%
   - ✅ 陣列回應處理：100%
   - ⚠️ 無序回應處理：95%

### 缺少的功能（5%）

目前可以無限制地連發請求，可能導致：

1. **Home Assistant Server 過載**
   - 無並發數量限制
   - 可能短時間內發送大量請求

2. **記憶體占用問題**
   - `_pending_requests` 字典可能無限增長
   - 沒有超時清理機制
   - 過期的請求不會被自動移除

3. **錯誤處理不完整**
   - 請求超時沒有處理
   - 未完成的請求可能永久占用記憶體

## 改進方案

### 方案：加入 Semaphore 並發控制

在 `HassWebSocketService` 類別中加入以下改進：

```python
class HassWebSocketService:
    def __init__(self, env=None, db_name=None, ha_url=None, ha_token=None):
        # 現有初始化...
        self._pending_requests = {}

        # 新增：並發控制
        self._request_semaphore = asyncio.Semaphore(10)  # 最多 10 個並發請求
        self._request_timeout = 30  # 請求超時時間（秒）

    async def send_request(self, request_type, **kwargs):
        """
        發送 WebSocket 請求並等待回應（加入並發控制）
        """
        async with self._request_semaphore:  # 取得許可，超過限制時會等待
            message_id = self._message_id
            self._message_id += 1

            # 建立 Future 等待回應
            future = asyncio.Future()
            self._pending_requests[message_id] = future

            # 發送請求
            await self._websocket.send(json.dumps({
                "id": message_id,
                "type": request_type,
                **kwargs
            }))

            self._logger.debug(f"Sent request {message_id}: {request_type}")

            try:
                # 等待回應，加入超時控制
                result = await asyncio.wait_for(future, timeout=self._request_timeout)
                return result
            except asyncio.TimeoutError:
                # 超時時清理 pending request
                self._pending_requests.pop(message_id, None)
                self._logger.error(f"Request {message_id} timed out after {self._request_timeout}s")
                raise Exception(f"Request {message_id} timed out")
            except Exception as e:
                # 其他錯誤也要清理
                self._pending_requests.pop(message_id, None)
                raise
```

### 改進效益

1. **防止過載**
   - Semaphore 限制並發請求數量（預設 10 個）
   - 超過限制時自動排隊等待

2. **記憶體控制**
   - 超時後自動清理 `_pending_requests`
   - 防止記憶體洩漏

3. **錯誤處理**
   - 請求超時有明確處理
   - 所有錯誤路徑都會清理資源

4. **可調整參數**
   - `_request_semaphore` 並發數可調整
   - `_request_timeout` 超時時間可調整

## 測試場景

實作後應測試以下場景：

1. **並發限制測試**
   - 同時發送 20 個請求，驗證只有 10 個並發執行
   - 其餘 10 個請求應該排隊等待

2. **超時清理測試**
   - 發送請求但 Home Assistant 不回應
   - 驗證 30 秒後請求被清理，不會占用記憶體

3. **錯誤恢復測試**
   - 在請求進行中斷開 WebSocket
   - 驗證所有 pending requests 被正確清理

## 優先級

**優先級：中**

- 目前系統運作正常，無序處理已達 95%
- 此優化主要防止極端情況（大量並發請求）
- 建議在遇到以下情況時實作：
  - 發現記憶體持續增長
  - Home Assistant 回報請求過載
  - 需要支援高頻率請求場景

## 相關文件

- `models/common/hass_websocket_service.py` - WebSocket 服務實作
- `docs/homeasistant-websocket.md` - Home Assistant WebSocket 協定規範

## 實作檢查清單

- [ ] 在 `__init__()` 中加入 `_request_semaphore` 和 `_request_timeout`
- [ ] 修改 `send_request()` 方法加入 Semaphore 控制
- [ ] 加入 `asyncio.wait_for()` 超時處理
- [ ] 確保所有錯誤路徑都會清理 `_pending_requests`
- [ ] 編寫並發限制測試
- [ ] 編寫超時清理測試
- [ ] 更新日誌記錄並發狀態
