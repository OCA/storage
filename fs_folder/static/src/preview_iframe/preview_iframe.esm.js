import {Component} from "@odoo/owl";

export class PreviewIframe extends Component {
    static template = "fs_folder.PreviewIframe";
    static props = {
        url: {type: String, optional: false},
        onClose: {type: Function, optional: true},
    };

    onCloseClick() {
        if (this.props.onClose) {
            this.props.onClose();
        }
    }
}
