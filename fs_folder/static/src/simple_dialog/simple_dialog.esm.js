import {Component, useRef} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {useChildRef} from "@web/core/utils/hooks";

export class SimpleDialog extends Component {
    static template = "fs_folder.SimpleDialog";
    static components = {Dialog};
    static props = {
        close: Function,
        title: {
            validate: (m) => {
                return (
                    typeof m === "string" ||
                    (typeof m === "object" && typeof m.toString === "function")
                );
            },
            optional: true,
        },
        body: {type: String, optional: true},
        value: {type: String, optional: true},
        confirm: {type: Function, optional: true},
        confirmLabel: {type: String, optional: true},
        confirmClass: {type: String, optional: true},
        cancel: {type: Function, optional: true},
        cancelLabel: {type: String, optional: true},
        dismiss: {type: Function, optional: true},
    };
    static defaultProps = {
        confirmLabel: _t("Ok"),
        cancelLabel: _t("Cancel"),
        confirmClass: "btn-primary",
        title: _t("Confirmation"),
    };

    setup() {
        this.env.dialogData.dismiss = () => this._dismiss();
        this.modalRef = useChildRef();
        this.isProcess = false;
        this.inputRef = useRef("input");
    }

    async _cancel() {
        return this.execButton(this.props.cancel);
    }

    async _confirm() {
        return this.execButton(this.props.confirm);
    }

    async _dismiss() {
        return this.execButton(this.props.dismiss || this.props.cancel);
    }

    setButtonsDisabled(disabled) {
        this.isProcess = disabled;
        if (!this.modalRef.el) {
            // Safety belt for stable versions
            return;
        }
        for (const button of [
            ...this.modalRef.el.querySelectorAll(".modal-footer button"),
        ]) {
            button.disabled = disabled;
        }
    }
    async execButton(callback) {
        if (this.isProcess) {
            return;
        }
        this.setButtonsDisabled(true);
        if (callback) {
            let shouldClose = true;
            try {
                /* eslint-disable-next-line callback-return */
                shouldClose = await callback(this.inputRef.el.value);
            } catch (e) {
                this.props.close();
                throw e;
            }
            if (shouldClose === false) {
                this.setButtonsDisabled(false);
                return;
            }
        }
        this.props.close();
    }
}
