# Issue #60 分析報告

## 問題根因

經過調查，問題的根因是 **ir.rule 快取未正確失效**。

### 技術細節

1. **domain_force 語法正確**
   - `security/security.xml` 中的 `ha_instance_user_rule` 使用：
     ```xml
     [('id', 'in', user.ha_entity_group_ids.mapped('ha_instance_id').ids)]
     ```
   - 這個語法在 Odoo ir.rule 評估中是正確的

2. **問題所在：快取機制**
   - Odoo 的 ir.rule 會快取 domain 評估結果以提高效能
   - 當 `ha.entity.group.user_ids` 被修改時：
     - 關聯表 `ha_entity_group_user_rel` 會更新
     - 但 ir.rule 快取**不會自動失效**
   - 導致用戶權限變更後，首次請求仍使用舊的快取結果

3. **相關程式碼**
   - `models/ha_entity_group.py`：缺少 `write` 方法的快取清除邏輯
   - `models/res_users.py`：定義了 `ha_entity_group_ids` 反向關聯

## 修復方案

在 `models/ha_entity_group.py` 中覆寫 `write` 和 `create` 方法：

```python
def write(self, vals):
    res = super().write(vals)
    if 'user_ids' in vals:
        # 清除所有相關用戶的 ir.rule 快取
        self.env['ir.rule'].clear_caches()
    return res

def create(self, vals_list):
    records = super().create(vals_list)
    # 如果建立時有設定 user_ids，清除快取
    if any(vals.get('user_ids') for vals in vals_list if isinstance(vals, dict)):
        self.env['ir.rule'].clear_caches()
    return records
```

## 風險評估

| 風險 | 評估 | 緩解措施 |
|------|------|---------|
| 效能影響 | 低 | `clear_caches()` 只在權限變更時呼叫，不頻繁 |
| ha_manager 影響 | 無 | Manager 使用 `[(1, '=', 1)]` 規則，不受影響 |

## 測試計畫

1. 手動測試：權限變更後立即生效
2. 後端單元測試：驗證各種權限場景
3. Playwright E2E 測試：完整用戶流程測試
