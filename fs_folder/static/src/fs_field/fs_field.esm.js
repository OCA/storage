import {Component, onWillStart, useRef, useState} from "@odoo/owl";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {FsFieldDirectory} from "./fs_field_directory/fs_field_directory.esm";
import {FsFieldFile} from "./fs_field_file/fs_field_file.esm";
import {SimpleDialog} from "../simple_dialog/simple_dialog.esm";
import {_t} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useDropzone} from "@web/core/dropzone/dropzone_hook";

import {usePreviewIframeViewer} from "../preview_iframe/preview_iframe_hook.esm";
import {useService} from "@web/core/utils/hooks";

export class FsField extends Component {
    setup() {
        super.setup();
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
        this.state.data = await rpc(
            `/fs_field/get_children/${this.props.record.resModel}/${this.props.record.resId}/${this.props.name}`,
            {
                path: this.state.path.join("/"),
            }
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
                        rpc(
                            `/fs_field/upload/${self.props.record.resModel}/${self.props.record.resId}/${self.props.name}`,
                            {
                                path: self.state.path.join("/"),
                                name: file.name,
                                data: ev.target.result.split(",")[1],
                            }
                        ).then(() => resolve());
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
        await rpc(
            `/fs_field/${this.state.copy.move ? "move" : "copy"}/${this.props.record.resModel}/${this.props.record.resId}/${this.props.name}`,
            {
                path: this.state.path.join("/"),
                origin_path: this.state.copy.path,
                record: this.state.copy.record.name,
            }
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
        var url = new URL(
            `/fs_field/get_file/${this.props.record.resModel}/${this.props.record.resId}/${this.props.name}`,
            window.location.origin
        );
        var path = [...this.state.path, record.name];
        url.searchParams.append("path", path.join("/"));
        url.searchParams.append("download", 1);
        await downloadFile(url.toString());
    }
    async onClickPreview(record) {
        var url = new URL(
            `/fs_field/get_file/${this.props.record.resModel}/${this.props.record.resId}/${this.props.name}`,
            window.location.origin
        );
        var path = [...this.state.path, record.name];
        url.searchParams.append("path", path.join("/"));
        this.fileViewer.open(url.toString());
    }
    async onClickDelete(record) {
        this.dialog.add(ConfirmationDialog, {
            body: _t("Are you sure that you want to remove this item?"),
            confirm: () => {
                rpc(
                    `/fs_field/delete/${this.props.record.resModel}/${this.props.record.resId}/${this.props.name}`,
                    {
                        path: this.state.path.join("/"),
                        name: record.name,
                    }
                ).then(() => {
                    this.setData();
                });
            },
        });
    }
    onClickAddChildFolder() {
        this.dialog.add(SimpleDialog, {
            confirm: (value) => {
                rpc(
                    `/fs_field/add_folder/${this.props.record.resModel}/${this.props.record.resId}/${this.props.name}`,
                    {
                        path: this.state.path.join("/") || "",
                        name: value,
                    }
                ).then(this.setData());
            },
        });
    }
}
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
