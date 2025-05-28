import {Component} from "@odoo/owl";

export class PreviewIframe extends Component {
    static template = "fs_folder_ms_drive.PreviewIframe";
    static props = {
        url: {type: String, optional: false},
    };
}
