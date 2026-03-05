/** @odoo-module **/

/**
 * BlueprintSelector - Custom field widget for selecting Blueprint templates
 *
 * This widget displays a list of available Blueprints from Home Assistant
 * and allows the user to select one for creating Automation/Script.
 */

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";

const { Component, useState, onWillUpdateProps } = owl;

export class BlueprintSelector extends Component {
    static template = "odoo_ha_addon.BlueprintSelector";
    static props = {
        ...standardFieldProps,
        list_field: { type: String, optional: true },
    };

    setup() {
        this.state = useState({
            blueprintList: [],
            selectedPath: this.props.record.data[this.props.name] || "",
            searchText: "",
        });

        this._parseBlueprints();

        onWillUpdateProps((nextProps) => {
            this.state.selectedPath = nextProps.record.data[nextProps.name] || "";
            this._parseBlueprints(nextProps);
        });
    }

    _parseBlueprints(props = this.props) {
        const listField = props.list_field || "blueprint_list_json";
        const listJson = props.record.data[listField];

        if (!listJson) {
            this.state.blueprintList = [];
            return;
        }

        try {
            const blueprintData = JSON.parse(listJson);
            const blueprints = [];

            for (const [path, info] of Object.entries(blueprintData)) {
                const metadata = info.metadata || {};
                blueprints.push({
                    path: path,
                    name: metadata.name || path,
                    description: metadata.description || "",
                    domain: metadata.domain || "",
                    source_url: metadata.source_url || "",
                });
            }

            // Sort by name
            blueprints.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
            this.state.blueprintList = blueprints;

        } catch (e) {
            console.error("Failed to parse blueprint list:", e);
            this.state.blueprintList = [];
        }
    }

    get filteredBlueprints() {
        const search = this.state.searchText.toLowerCase();
        if (!search) {
            return this.state.blueprintList;
        }
        return this.state.blueprintList.filter(bp =>
            bp.name.toLowerCase().includes(search) ||
            bp.description.toLowerCase().includes(search) ||
            bp.path.toLowerCase().includes(search)
        );
    }

    get selectedBlueprint() {
        return this.state.blueprintList.find(bp => bp.path === this.state.selectedPath);
    }

    onSearchInput(ev) {
        this.state.searchText = ev.target.value;
    }

    onSelectBlueprint(blueprint) {
        this.state.selectedPath = blueprint.path;
        this.props.record.update({ [this.props.name]: blueprint.path });
    }

    onClearSelection() {
        this.state.selectedPath = "";
        this.props.record.update({ [this.props.name]: false });
    }
}

BlueprintSelector.extractProps = ({ attrs }) => {
    return {
        list_field: attrs.options?.list_field || "blueprint_list_json",
    };
};

registry.category("fields").add("blueprint_selector", {
    component: BlueprintSelector,
    extractProps: BlueprintSelector.extractProps,
    supportedTypes: ["char"],
});
