/** @odoo-module */

/**
 * <hahistory domain="input_number" limit="5000"/> 的 props parser
 *
 * limit: 預設 5000 筆，確保能載入多個實體的歷史記錄
 *        （每個實體每天約 100-500 筆記錄，5000 筆可涵蓋約 10-50 個實體）
 */
export class HaHistoryArchParser {
  parse(xmlDoc) {
    const domains = (xmlDoc.getAttribute("domain") || "").split(",");
    const limit = parseInt(xmlDoc.getAttribute("limit"), 10) || 5000;
    return {
      domains,
      limit,
    };
  }
}
