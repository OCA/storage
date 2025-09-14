/**
 * Copyright (c) 2025 ACSONE SA/NV
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 */

import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";
import {user} from "@web/core/user";

export class MSDriveConnectField extends Component {
    setup() {
        this.state = useState({
            value: this.props.record.data[this.props.name],
        });
        this.orm = useService("orm");
        this.action = useService("action");
    }
    get isConnected() {
        // If the current user has no write access on the record
        // then the field is readonly
        return this.state.value === "connected";
    }

    get isReadonly() {
        return (
            !this.props.record.isInEdition || user.userId !== this.props.record.resId
        );
    }

    async onButtonClick() {
        if (this.isReadonly) {
            return;
        }
        if (this.isConnected) {
            await this.onDisconnect();
        } else {
            await this.onConnect();
        }
    }

    async onDisconnect() {
        const action = await this.orm.call(
            "res.users",
            "action_drive_disconnect",
            [this.props.record.resId],
            {}
        );
        this.action.doAction(action, {
            clearBreadcrumbs: true,
            tag: "reload",
            onClose: async () => {
                window.location.reload(); // Reload the page to reflect the changes
            },
        });
    }

    async onConnect() {
        if (this.isReadonly || this.isConnected) {
            return;
        }
        const from_url = window.location.href;
        // Call the method get_drive_authentication_url
        // on the current model with from_url as argument
        // this method will return the authentication url
        // to connect to drive
        const auth_url = await this.orm.call(
            this.props.record.resModel,
            "get_drive_authentication_url",
            [[this.props.record.resId], from_url]
        );
        window.location.assign(auth_url);
    }
}

MSDriveConnectField.template = "microsoft_drive_account.MSDriveConnectField";
MSDriveConnectField.props = standardFieldProps;
MSDriveConnectField.supportedTypes = ["selection"];

registry.category("fields").add("ms_drive_connect", {
    component: MSDriveConnectField,
});
