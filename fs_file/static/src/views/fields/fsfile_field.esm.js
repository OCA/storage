/** @odoo-module */

/**
 * Copyright 2023 ACSONE SA/NV
 */
import {Component, onWillUpdateProps, useState} from "@odoo/owl";

import {FileUploader} from "@web/views/fields/file_handler";
import {getDataURLFromFile} from "@web/core/utils/urls";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";

export class FSFileField extends Component {
    setup() {
        this.notification = useService("notification");
        this.state = useState({
            ...this.props.value,
            isValid: true,
        });
        onWillUpdateProps((nextProps) => {
            this.state.isUploading = false;
            const {filename, mimetype, url} = nextProps.value || {};
            this.state.filename = filename;
            this.state.mimetype = mimetype;
            this.state.url = url;
        });
    }

    async uploadFile(file) {
        this.state.isUploading = true;
        const data = await getDataURLFromFile(file);
        this.props.record.update({
            [this.props.name]: {
                filename: file.name,
                content: data.split(",")[1],
            },
        });
        this.state.isUploading = false;
    }

    clear() {
        this.props.record.update({[this.props.name]: false});
    }

    onFileRemove() {
        this.state.isValid = true;
        this.props.update(false);
    }
    onFileUploaded(info) {
        this.state.isValid = true;
        this.props.update({
            filename: info.name,
            content: info.data,
        });
    }
    onLoadFailed() {
        this.state.isValid = false;
        this.notification.add(this.env._t("Could not display the selected image"), {
            type: "danger",
        });
    }
}

FSFileField.template = "fs_file.FSFileField";
FSFileField.components = {
    FileUploader,
};
FSFileField.props = {
    ...standardFieldProps,
    acceptedFileExtensions: {type: String, optional: true},
};
FSFileField.defaultProps = {
    acceptedFileExtensions: "*",
};
registry.category("fields").add("fs_file", FSFileField);
