/** @odoo-module */

/**
 * <hahistory domain="input_number" limit="80"/> 的 props parser
 */
export class HaHistoryArchParser {
  parse(xmlDoc) {
    const domains = (xmlDoc.getAttribute("domain") || "").split(",");
    const limit = xmlDoc.getAttribute("limit") || 80;
    return {
      domains,
      limit,
    };
  }
}
