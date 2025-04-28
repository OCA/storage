import {Component, onWillStart, useRef, useState} from "@odoo/owl";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {FsFieldDirectory} from "./fs_field_directory/fs_field_directory.esm";
import {FsFieldFile} from "./fs_field_file/fs_field_file.esm";
import {SimpleDialog} from "../simple_dialog/simple_dialog.esm";
import {_t} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useDropzone} from "@web/core/dropzone/dropzone_hook";
import {usePreviewIframeViewer} from "../preview_iframe/preview_iframe_hook.esm";
import {useService} from "@web/core/utils/hooks";

export class FsField extends Component {
    setup() {
        super.setup();
        this.service = useService(this.constructor.serviceName);
        this.dropzone = useRef("dropzone");
        this.dialog = useService("dialog");
        this.fileViewer = usePreviewIframeViewer();
        this.state = useState({path: [], data: [], copy: false});
        onWillStart(() => {
            this.setData();
        });
        useDropzone(this.dropzone, this.onDropFile.bind(this), "");
    }
    async setData() {
        this.state.data = await this.service.getData(
            this.props.record,
            this.props.name,
            this.state.path
        );
    }
    async onDropFile(event) {
        const {files} = event.dataTransfer;
        const promises = [];
        const self = this;
        for (const file of files) {
            promises.push(
                new Promise((resolve) => {
                    var reader = new window.FileReader();
                    reader.readAsDataURL(file);
                    reader.onload = function (ev) {
                        self.service
                            .uploadFile(
                                this.props.record,
                                this.props.name,
                                this.state.path,
                                file,
                                ev.target.result.split(",")[1]
                            )
                            .then(() => resolve());
                    };
                })
            );
        }
        Promise.all(promises).then(() => {
            this.setData();
        });
    }
    async onCopy(record, move = false) {
        this.state.copy = {
            path: this.state.path.join("/"),
            record,
            move,
        };
    }
    async onPaste() {
        await this.service.pasteFile(
            this.props.record,
            this.props.name,
            this.state.path,
            this.state.copy.path,
            this.state.copy.record,
            this.state.copy.move
        );
        this.state.copy = null;
        this.setData();
    }
    async returnParent(path) {
        if (path) {
            this.state.path = [];
            this.setData();
            return;
        }
        this.state.path = this.state.path.slice(0, this.state.path.indexOf(path) + 1);
        this.setData();
    }
    getComponent(record) {
        if (record.type === "directory") {
            return FsField.components.FsFieldDirectory;
        }
        return FsField.components.FsFieldFile;
    }
    getProps(record) {
        const props = {
            record,
            onClickDelete: () => this.onClickDelete(record),
            onCopy: () => this.onCopy(record, false),
            onCut: () => this.onCopy(record, true),
        };
        if (record.type === "directory") {
            props.onClick = () => this.onClickDirectory(record);
        } else {
            props.onClickDownload = () => this.onClickDownload(record);
            props.onClickPreview = () => this.onClickPreview(record);
        }
        return props;
    }
    async onClickDirectory(record) {
        this.state.path = [...this.state.path, record.name];
        this.setData();
    }
    async onClickDownload(record) {
        await downloadFile(
            this.service.getFileUrl(
                this.props.record,
                this.props.name,
                this.state.path,
                record.name,
                1
            )
        );
    }
    async onClickPreview(record) {
        this.fileViewer.open(
            this.service.getFileUrl(
                this.props.record,
                this.props.name,
                this.state.path,
                record.name,
                0
            )
        );
    }
    async onClickDelete(record) {
        this.dialog.add(ConfirmationDialog, {
            body: _t("Are you sure that you want to remove this item?"),
            confirm: () => {
                this.service
                    .delete(this.props.record, this.props.name, this.state.path, record)
                    .then(() => {
                        this.setData();
                    });
            },
        });
    }
    onClickAddChildFolder() {
        this.dialog.add(SimpleDialog, {
            confirm: (value) => {
                this.service
                    .addFolder(
                        this.props.record,
                        this.props.name,
                        this.state.path,
                        value
                    )
                    .then(() => {
                        this.setData();
                    });
            },
        });
    }
}
FsField.serviceName = "fs.field";
FsField.components = {
    FsFieldDirectory,
    FsFieldFile,
};
FsField.template = "fs_field.FsField";
FsField.props = {
    ...standardFieldProps,
};
export const FsFieldField = {
    component: FsField,
};

registry.category("fields").add("fs_field", FsFieldField);
