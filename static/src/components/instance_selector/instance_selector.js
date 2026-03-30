/** @odoo-module **/

import { Component, useState, useRef, onWillUnmount } from "@odoo/owl";

/**
 * Instance Selector Component
 *
 * A dropdown component for selecting Home Assistant instances.
 * Displays the current instance and allows switching between available instances.
 *
 * Props:
 * - instances: Array of instance objects {id, name, websocket_status, entity_count}
 * - currentInstanceId: ID of the currently selected instance
 * - onSelectInstance: Callback function when an instance is selected
 * - loading: Boolean indicating if instances are being loaded
 */
export class InstanceSelector extends Component {
    static template = "odoo_ha_addon.InstanceSelector";
    static props = {
        instances: { type: Array, optional: false },
        currentInstanceId: { type: Number, optional: true },
        onSelectInstance: { type: Function, optional: false },
        loading: { type: Boolean, optional: true },
    };

    setup() {
        this.state = useState({
            isOpen: false,
        });
        this.rootRef = useRef("rootRef");

        // Close dropdown when clicking outside
        this.onDocumentClick = this.onDocumentClick.bind(this);
        document.addEventListener("click", this.onDocumentClick);

        onWillUnmount(() => {
            document.removeEventListener("click", this.onDocumentClick);
        });
    }

    /**
     * Handle clicks outside the dropdown to close it
     */
    onDocumentClick(ev) {
        const dropdownEl = this.rootRef?.el;
        if (dropdownEl && !dropdownEl.contains(ev.target)) {
            this.state.isOpen = false;
        }
    }

    /**
     * Toggle dropdown open/close
     */
    toggleDropdown(ev) {
        ev.stopPropagation();
        this.state.isOpen = !this.state.isOpen;
    }

    /**
     * Handle instance selection
     */
    selectInstance(instanceId, ev) {
        ev.stopPropagation();
        this.state.isOpen = false;

        if (instanceId !== this.props.currentInstanceId) {
            this.props.onSelectInstance(instanceId);
        }
    }

    /**
     * Get the current instance object
     */
    get currentInstance() {
        if (!this.props.currentInstanceId || !this.props.instances.length) {
            return null;
        }
        return this.props.instances.find(inst => inst.id === this.props.currentInstanceId);
    }

    /**
     * Get status icon class based on websocket status
     */
    getStatusIcon(status) {
        const iconMap = {
            'connected': 'fa-circle text-success',
            'connecting': 'fa-circle text-warning',
            'disconnected': 'fa-circle text-muted',
            'error': 'fa-circle text-danger',
        };
        return iconMap[status] || 'fa-circle text-muted';
    }

    /**
     * Check if an instance is the current one
     */
    isCurrentInstance(instanceId) {
        return instanceId === this.props.currentInstanceId;
    }
}
