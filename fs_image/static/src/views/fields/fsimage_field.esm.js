/** @odoo-module */

/**
 * Copyright 2023 ACSONE SA/NV
 */
import {
    ImageField,
    fileTypeMagicWordMap,
    imageCacheKey,
} from "@web/views/fields/image/image_field";
import {onWillUpdateProps, useState} from "@odoo/owl";

import {AltTextDialog} from "../dialogs/alttext_dialog.esm";
import {registry} from "@web/core/registry";
import {url} from "@web/core/utils/urls";
import {useService} from "@web/core/utils/hooks";

const placeholder = "/web/static/img/placeholder.png";

export class FSImageField extends ImageField {
    setup() {
        // Call super.setup() to initialize the state
        super.setup();
        this.state = useState({
            ...this.props.value,
            ...this.state,
        });
        onWillUpdateProps((nextProps) => {
            this.state.isUploading = false;
            const {filename, mimetype, alt_text, url} = nextProps.value || {};
            this.state.filename = filename;
            this.state.mimetype = mimetype;
            this.state.url = url;
            this.state.alt_text = alt_text;
        });
        this.dialogService = useService("dialog");
    }

    getUrl(previewFieldName) {
        if (
            this.state.isValid &&
            this.props.value &&
            typeof this.props.value === "object"
        ) {
            // Check if value is a dict
            if (this.props.value.content) {
                // We use the binary content of the value
                // Use magic-word technique for detecting image type
                const magic =
                    fileTypeMagicWordMap[this.props.value.content[0]] || "png";
                return `data:image/${magic};base64,${this.props.value.content}`;
            }
            if (!this.rawCacheKey) {
                this.rawCacheKey = this.props.record.data.__last_update;
            }
            const model = this.props.record.resModel;
            const id = this.props.record.resId;
            let base_url = this.props.value.url;
            if (id !== undefined && id !== null && id !== false) {
                const field = previewFieldName;
                const filename = this.props.value.filename;
                base_url = `/web/image/${model}/${id}/${field}/${filename}`;
            }
            return url(base_url, {unique: imageCacheKey(this.rawCacheKey)});
        }
        return placeholder;
    }

    get hasTooltip() {
        return this.props.enableZoom && !this.props.isDebugMode && this.props.value;
    }

    onFileUploaded(info) {
        this.state.isValid = true;
        // Invalidate the `rawCacheKey`.
        this.rawCacheKey = null;
        this.props.update({
            filename: info.name,
            content: info.data,
        });
    }
    onAltTextEdit() {
        const self = this;
        const altText = this.props.value.alt_text || "";
        const dialogProps = {
            title: this.env._t("Alt Text"),
            altText: altText,
            confirm: (value) => {
                self.props.update({
                    ...self.props.value,
                    alt_text: value,
                });
            },
        };
        this.dialogService.add(AltTextDialog, dialogProps);
    }
}

FSImageField.template = "fs_image.FSImageField";
registry.category("fields").add("fs_image", FSImageField);
