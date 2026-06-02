/** @odoo-module */

/**
 * <hahistory domain="sensor,switch,..." limit="5000" max_points_per_entity="500"/> 的 props parser
 *
 * limit: fallback 上限（用於非降採樣模式）
 * max_points_per_entity: 每個 entity 伺服器端降採樣最大點數（預設 500）
 */
export class HaHistoryArchParser {
  parse(xmlDoc) {
    const domains = (xmlDoc.getAttribute("domain") || "").split(",");
    const limit = parseInt(xmlDoc.getAttribute("limit"), 10) || 5000;
    const maxPointsPerEntity =
      parseInt(xmlDoc.getAttribute("max_points_per_entity"), 10) || 500;
    return {
      domains,
      limit,
      maxPointsPerEntity,
    };
  }
}
