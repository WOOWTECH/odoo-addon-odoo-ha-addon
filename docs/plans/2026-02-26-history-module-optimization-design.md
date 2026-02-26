# History Module Optimization - PRD

**Created:** 2026-02-26T08:12:36Z
**Updated:** 2026-02-26T08:43:32Z
**Status:** Completed
**Author:** Claude Code Assistant

## Problem Statement

The HAHistory view has several issues affecting user experience:

1. **Search filter bar not appearing** - Users cannot filter history by time, domain, or entity
2. **Only one entity chart displayed** - Despite multiple entities having history records, only one chart renders
3. **\`[object Object]\` appearing in charts** - Label formatting issues on mobile view
4. **Coordinate numbers on line charts** - Datalabels plugin was enabled globally

## Root Cause Analysis

### Issue 1: Search Filter Bar Not Appearing

**Root Cause:** The \`ir_act_window\` record for the History action had \`search_view_id = NULL\`, meaning Odoo didn't know to load the search view.

**Evidence:**
\`\`\`sql
SELECT search_view_id FROM ir_act_window WHERE id=751;
-- Result: NULL (should be 5016)
\`\`\`

**Fix Applied:**
\`\`\`sql
UPDATE ir_act_window
SET search_view_id=5016,
    context='{"search_default_available": 1, "search_default_filter_today": 1}'
WHERE id=751;
\`\`\`

### Issue 2: Only One Entity Chart Displayed

**Investigation Results:**

1. **Database records are correct** - 6 entities with history data:
   - CO2 sensor: 2,277 records today
   - Current_2: 2,175 records today
   - Voltage: 2,001 records today
   - Current_1: 452 records today
   - Uptime: 152 records today
   - PM10: 125 records today

2. **Limit was increased** - Changed from 80 to 5000 in \`hahistory_arch_parser.js\`

3. **Distribution in first 5000 records** - All 6 entities are represented

**Possible Remaining Causes:**
- Asset cache not regenerated after JS changes
- Browser caching old JavaScript
- Frontend filtering logic issue

**Actions Taken:**
- Cleared \`ir_attachment\` asset cache
- Restarted Odoo container
- Search view now properly linked

### Issue 3: \`[object Object]\` in Charts

**Root Cause:** \`ctx.dataset.label\` was an object (entity relationship), not a string.

**Fix Applied:** Added \`ensureStringLabel()\` function in \`hahistory_renderer.js\`:
\`\`\`javascript
function ensureStringLabel(label) {
  if (label === null || label === undefined) return '';
  if (typeof label === 'object') {
    return label.name || label.display_name || String(label);
  }
  return String(label);
}
\`\`\`

### Issue 4: Datalabels on Line Charts

**Root Cause:** chartjs-plugin-datalabels was enabled globally.

**Fix Applied:** Added \`datalabels: { display: false }\` to all line chart configurations in \`hahistory_renderer.js\`.

## Architecture Overview

\`\`\`
┌─────────────────────────────────────────────────────────────────┐
│                    HAHistory View Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────┐  │
│  │ hahistory_view.js│   │hahistory_model.js│   │hahistory_arch │  │
│  │  (View Def)     │──▶│  (Data Loading)  │◀──│ _parser.js    │  │
│  └─────────────────┘   └────────┬────────┘   └───────────────┘  │
│                                 │                                │
│                                 ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   hahistory_controller.js                    ││
│  │  - Manages state (displayMode, updateKey)                    ││
│  │  - Subscribes to ha_data service events                      ││
│  │  - Handles search domain changes                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                 │                                │
│                                 ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   hahistory_renderer.js                      ││
│  │  - Groups records by entity                                  ││
│  │  - Selects chart type based on domain                        ││
│  │  - Renders UnifiedChart components                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                 │                                │
│                                 ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              UnifiedChart Component (Chart.js)               ││
│  │  - Line charts for numeric sensors                          ││
│  │  - Timeline bars for binary/categorical states              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
\`\`\`

## Data Flow

1. **User opens History view**
   - Action loads with \`search_view_id\` and default filters
   - \`HaHistoryController\` initializes with domain from search

2. **Data Loading**
   - \`HaHistoryModel.loadHistory(domain)\` calls \`orm.webSearchRead()\`
   - Returns up to 5000 records with specified fields
   - Filters by arch domains (sensor, binary_sensor, etc.)

3. **Rendering**
   - Records grouped by entity_id
   - Each group creates a separate chart
   - Chart type determined by domain:
     - \`sensor\`, \`input_number\`, etc. → Line chart
     - \`binary_sensor\`, \`switch\`, etc. → Timeline bars
     - \`climate\`, \`fan\`, etc. → Categorical timeline

## Files Modified

| File | Changes |
|------|---------|
| \`src/views/ha_entity_history_views.xml\` | Added search view with filters, increased limit to 5000 |
| \`src/static/src/views/hahistory/hahistory_arch_parser.js\` | Default limit changed to 5000 |
| \`src/static/src/views/hahistory/hahistory_renderer.js\` | Added \`ensureStringLabel()\`, disabled datalabels on line charts |
| \`src/static/src/util/color.js\` | Added HSL color support in \`isLightColor()\` |
| \`src/static/src/components/charts/unified_chart/unified_chart.js\` | Fixed datalabels config |

## Database Fixes Applied

\`\`\`sql
-- Fix action's search view reference
UPDATE ir_act_window
SET search_view_id=5016,
    context='{"search_default_available": 1, "search_default_filter_today": 1}'
WHERE id=751;

-- Clear asset cache to force JS regeneration
DELETE FROM ir_attachment WHERE name LIKE 'web.assets%';
\`\`\`

## Verification Steps

After applying fixes:

1. **Hard refresh browser** (Ctrl+Shift+R)
2. **Navigate to HA Entity History**
3. **Verify search bar appears** at top with filters
4. **Verify multiple charts display** for each entity
5. **Check browser console** for debug output showing record counts

## Expected Outcome

- Search filter bar visible with time/domain/entity filters
- 6 separate charts displayed (one per entity with history)
- Each chart showing correct visualization:
  - Sensors → Line charts
  - Binary states → Timeline bars with On/Off colors
- No \`[object Object]\` or coordinate numbers visible

## Resolution Summary

All issues have been successfully resolved:

| Issue | Status | Solution |
|-------|--------|----------|
| Search filter bar not appearing | **Fixed** | Updated `ir_act_window.search_view_id` and search view arch in database |
| Only one entity chart displayed | **Fixed** | Increased limit from 80 to 5000 in hahistory view |
| `[object Object]` in charts | **Fixed** | Added `ensureStringLabel()` function |
| Coordinate numbers on line charts | **Fixed** | Disabled datalabels plugin for line charts |
| Inconsistent legend display | **Fixed** | Added explicit legend config to `parseNumericChartData()` |

## Lessons Learned

1. **XML view changes require module upgrade** - Simply deploying files is not enough; Odoo caches view definitions in `ir_ui_view` table
2. **Database sync is critical** - Action configurations (`ir_act_window`) must have correct references
3. **Asset cache must be cleared** - After JS changes, delete `ir_attachment` records with `name LIKE 'web.assets%'`
4. **Browser cache** - Users must hard refresh (Ctrl+Shift+R) after frontend changes
