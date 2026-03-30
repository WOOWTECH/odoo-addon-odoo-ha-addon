/** @odoo-module */

import { KeepLast } from "@web/core/utils/concurrency";
import { debug } from "../../util/debug";

export class HaHistoryModel {
  constructor(orm, resModel, archInfo, haDataService) {
    this.orm = orm;
    this.resModel = resModel;
    this.haDataService = haDataService;

    const { domains, limit } = archInfo;
    this.domains = domains;
    this.limit = limit;

    this.keepLast = new KeepLast();

    this.records = [];
  }

  /**
   *
   * @param {array} domain 這裡的 domain 是指 search domain，https://learnopenerp.blogspot.com/2021/08/list-of-search-domain-operators-odoo.html
   */
  async loadHistory(domain) {
    const taskFun = async () => {
      // 不再強制過濾實例，讓用戶透過 Search View 的 "Current Instance" filter 自己選擇
      debug("webSearchRead HaHistory", {
        domain: domain
      });

      const result = await this.orm.webSearchRead(this.resModel, domain, {
        limit: this.limit,
        specification: {
          entity_name: {},
          entity_id_string: {},
          entity_state: {}, // 使用 entity_state 而非保留欄位 state
          num_state: {},
          domain: {},
          last_updated: {},
          last_changed: {},
        },
      });
      const { records, ...others } = result;
      const filteredRecords = records.filter((record) =>
        this.domains.some((elt) => elt === record["domain"])
      );

      this.records = filteredRecords;
    };
    return this.keepLast.add(taskFun());
  }
}
