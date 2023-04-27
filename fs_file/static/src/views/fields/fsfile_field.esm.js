/** @odoo-module */

/**
 * Copyright 2023 ACSONE SA/NV
 */

import {registry} from "@web/core/registry";
import {session} from "@web/session";
import {formatFloat} from "@web/views/fields/formatters";
import {useService} from "@web/core/utils/hooks";
import {sprintf} from "@web/core/utils/strings";
import {getDataURLFromFile} from "@web/core/utils/urls";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {Component, onWillUpdateProps, useState} from "@odoo/owl";

const DEFAULT_MAX_FILE_SIZE = 128 * 1024 * 1024; // 128MB

export class FSFileField extends Component {
    setup() {
        this.notification = useService("notification");
        this.state = useState({
            ...this.props.value,
            isUploading: false,
        });
        onWillUpdateProps((nextProps) => {
            this.state.isUploading = false;
            const {filename, mimetype, url} = nextProps.value || {};
            this.state.filename = filename;
            this.state.mimetype = mimetype;
            this.state.url = url;
        });
    }
    get maxUploadSize() {
        return session.max_file_upload_size || DEFAULT_MAX_FILE_SIZE;
    }

    edit() {
        var input = document.createElement("input");
        input.type = "file";
        input.accept = this.props.acceptedFileExtensions;
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                if (file.size > this.maxUploadSize) {
                    this.notification.add(
                        sprintf(
                            this.env._t(
                                "The file size exceeds the maximum allowed size of %s MB."
                            ),
                            formatFloat(this.maxUploadSize / 1024 / 1024)
                        ),
                        {type: "danger"}
                    );
                    return;
                }
                this.uploadFile(file);
            }
        };
        input.click();
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
}

FSFileField.template = "fs_file.FSFileField";
FSFileField.props = {
    ...standardFieldProps,
    acceptedFileExtensions: {type: String, optional: true},
};
FSFileField.defaultProps = {
    acceptedFileExtensions: "*",
};
registry.category("fields").add("fs_file", FSFileField);
