/** @odoo-module */

import { KeepLast } from "@web/core/utils/concurrency";
import { debug } from "../../util/debug";

export class HaHistoryModel {
  constructor(orm, resModel, archInfo, haDataService) {
    this.orm = orm;
    this.resModel = resModel;
    this.haDataService = haDataService;

    const { domains, limit, maxPointsPerEntity } = archInfo;
    this.domains = domains;
    this.limit = limit;
    this.maxPointsPerEntity = maxPointsPerEntity || 500;

    this.keepLast = new KeepLast();

    this.records = [];
  }

  /**
   *
   * @param {array} domain 這裡的 domain 是指 search domain，https://learnopenerp.blogspot.com/2021/08/list-of-search-domain-operators-odoo.html
   */
  async loadHistory(domain) {
    const taskFun = async () => {
      debug("get_downsampled_history HaHistory", {
        domain: domain,
        supported_domains: this.domains,
        max_points: this.maxPointsPerEntity,
      });

      const records = await this.orm.call(
        this.resModel,
        "get_downsampled_history",
        [domain, this.domains, this.maxPointsPerEntity]
      );

      this.records = records;
    };
    return this.keepLast.add(taskFun());
  }
}
