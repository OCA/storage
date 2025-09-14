import {Component, markup, useEffect, useRef, useState, useSubEnv} from "@odoo/owl";
import {useBus, useService} from "@web/core/utils/hooks";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {FileUploader} from "@web/views/fields/file_handler";
import {FsFolderItem} from "./fs_folder_item/fs_folder_item.esm";
import {SimpleDialog} from "../simple_dialog/simple_dialog.esm";
import {_t} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {formatDateTime} from "@web/core/l10n/dates";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useDropzone} from "@web/core/dropzone/dropzone_hook";
import {usePreviewIframeViewer} from "../preview_iframe/preview_iframe_hook.esm";
const {DateTime} = luxon;

export class FsFolder extends Component {
    setup() {
        super.setup();
        this.service = useService(this.constructor.serviceName);
        this.dropzone = useRef("dropzone");
        this.dialog = useService("dialog");
        this.fileViewer = usePreviewIframeViewer();
        this.state = useState({path: [], data: [], copy: false, sort: [], hide: []});
        this.notificationService = useService("fs_folder_notification");
        useBus(this.notificationService.bus, "folder_modified", this.onFolderModified);
        useEffect(
            () => {
                // Initialize the fields as we are changing the record
                this.state.path = [];
                this.state.copy = false;
                this.setData();
            },
            () => [this.props.record.resId]
        );
        useDropzone(this.dropzone, this.onDropFile.bind(this), "");
        useSubEnv({
            onClickDirectory: (record) => {
                this.onClickDirectory(record);
            },
            onClickPreview: (record) => {
                this.onClickPreview(record);
            },
            onClickDownload: (record) => {
                this.onClickDownload(record);
            },
        });
    }
    onFolderModified(event) {
        const {resId, resModel, fieldName} = event.detail;
        if (
            resId === this.props.record.resId &&
            resModel === this.props.record.resModel &&
            fieldName === this.props.name
        ) {
            this.setData();
        }
    }
    async onClickInitialize() {
        await this.service.initialize(this.props.record, this.props.name);
        this.props.record.load();
    }
    async setData() {
        if (this.props.record.data[this.props.name]) {
            this.state.data = this.sortData(
                await this.service.getData(
                    this.props.record,
                    this.props.name,
                    this.state.path
                )
            );
        }
    }
    onSort(field) {
        if (this.state.sort.length && this.state.sort[0].field.name === field.name) {
            this.state.sort[0].order =
                this.state.sort[0].order === "asc" ? "desc" : "asc";
        } else {
            const newSort = this.state.sort.filter((s) => s.field.name !== field.name);
            newSort.unshift({
                field: field,
                order: "asc",
            });
            this.state.sort = newSort;
        }
        this.state.data = this.sortData(this.state.data);
    }
    sortData(data) {
        if (!this.state.sort) {
            return data;
        }
        return data.sort((a, b) => {
            for (const sort of this.state.sort) {
                const field = sort.field;
                const order = sort.order;
                if (field.name === "name") {
                    // Special case for name field, we want to sort by type first
                    const aType = a?.type || "directory";
                    const bType = b?.type || "directory";
                    const typeOrder = aType.localeCompare(bType);
                    if (typeOrder !== 0) {
                        return typeOrder;
                    }
                }
                let cmp = (itemA, itemB) => {
                    const aValue = itemA[field.name] || field.value(itemA) || "";
                    const bValue = itemB[field.name] || field.value(itemB) || "";
                    const type = field.type || "char";
                    if (
                        (type === "char" || type === "text") &&
                        typeof aValue === "string"
                    ) {
                        // For string fields, we want to do a case-insensitive and accented
                        // character insensitive comparison based on the locale
                        return aValue.localeCompare(bValue, undefined, {
                            sensitivity: "base",
                        });
                    }
                    return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
                };
                if (typeof field?.cmp === "function") {
                    cmp = field.cmp;
                }
                const cmpResult = cmp(a, b);
                if (cmpResult !== 0) {
                    return order === "asc" ? cmpResult : -cmpResult;
                }
            }
            return 0;
        });
    }
    async onAddFile(file) {
        this.service.uploadFile(
            this.props.record,
            this.props.name,
            this.state.path,
            file,
            file.data
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
                                self.props.record,
                                self.props.name,
                                self.state.path,
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
    async returnParent(path_index) {
        if (path_index < 0) {
            this.state.path = [];
            this.setData();
            return;
        }
        this.state.path = this.state.path.slice(0, path_index + 1);
        this.setData();
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
    get moreActionDef() {
        /**
         * This should return an array of objects with the following properties:
         * - sequence: The sequence of the action
         * - string: The name of the action
         * - icon: The icon of the action
         * - callback: The function to call when the action is clicked
         * - directory: true if the action is for a directory
         * - file: true if the action is for a file
         *
         */
        return [
            {
                sequence: 10,
                name: _t("Rename"),
                icon: "fa-pencil",
                callback: (record) => {
                    this.dialog.add(SimpleDialog, {
                        title: _t("Rename"),
                        value: record.name,
                        confirm: (value) => {
                            this.service
                                .rename(
                                    this.props.record,
                                    this.props.name,
                                    this.state.path,
                                    record.name,
                                    value
                                )
                                .then(() => {
                                    this.setData();
                                });
                        },
                    });
                },
                directory: true,
                file: true,
            },
            {
                sequence: 30,
                name: _t("Copy"),
                icon: "fa-copy",
                callback: (record) => this.onCopy(record),
                directory: true,
                file: true,
            },
            {
                sequence: 50,
                name: _t("Cut"),
                icon: "fa-scissors",
                callback: (record) => this.onCopy(record, true),
                directory: true,
                file: true,
            },
            {
                sequence: 99,
                name: _t("Delete"),
                icon: "fa-trash",
                callback: (record) => this.onClickDelete(record),
                directory: true,
                file: true,
            },
        ];
    }
    get fieldDef() {
        return this.fieldDefinition.sort((a, b) => a.sequence - b.sequence);
    }
    get fieldDefinition() {
        /**
         * This should return an array of objects with the following properties:
         *
         * - string: The name of the field
         * - type: The type of the field
         * - name: Technical name of the field
         * */
        return [
            {
                sequence: 10,
                string: _t("Name"),
                type: "char",
                name: "name",
                value: (record) => {
                    return markup(
                        `<span><i class="p-1 fa ${this.getIcon(record)}"></i>${record.name}</span>`
                    );
                },
            },
            {
                sequence: 20,
                string: _t("Created on"),
                type: "datetime",
                optional: true,
                name: "created",
                value: (record) => {
                    if (!record.created) {
                        return "";
                    }

                    if (typeof record.created === "number") {
                        return formatDateTime(DateTime.fromSeconds(record.created));
                    }
                    return record.created;
                },
            },
            {
                sequence: 30,
                string: _t("User"),
                optional: true,
                type: "char",
                name: "uid",
            },
            {
                sequence: 40,
                string: _t("Modified on"),
                optional: true,
                type: "datetime",
                name: "mtime",
                value: (record) => {
                    if (!record.mtime) {
                        return "";
                    }

                    if (typeof record.mtime === "number") {
                        return formatDateTime(DateTime.fromSeconds(record.mtime));
                    }
                    return record.mtime;
                },
            },
        ];
    }
    onClickAddChildFolder() {
        this.dialog.add(SimpleDialog, {
            title: _t("Add Folder"),
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
    getIcon(record) {
        if (record.type === "directory") {
            return "fa-folder";
        }
        const filename = record.name;
        const extensionStartPosition = filename.lastIndexOf(".");
        if (extensionStartPosition === -1) {
            return "fa-file-o";
        }
        const extension = filename.slice(extensionStartPosition + 1);
        switch (extension.toLowerCase()) {
            case "aac":
            case "ogg":
            case "mp3":
                return "fa-file-audio-o";
            case "avi":
            case "flv":
            case "mkv":
            case "mp4":
                return "fa-file-video-o";
            case "css":
            case "html":
            case "js":
                return "fa-file-code-o";
            case "csv":
                return "fa-file-csv-o";
            case "doc":
            case "docx":
                return "fa-file-word-o";
            case "gif":
            case "jpeg":
            case "jpg":
            case "png":
                return "fa-file-image-o";
            case "gz":
            case "zip":
            case "archive":
                return "fa-file-archive-o";
            case "pdf":
                return "fa-file-pdf-o";
            case "ppt":
            case "pptx":
                return "fa-file-powerpoint-o";
            case "txt":
            case "text":
                return "fa-file-alt-o";
            case "xls":
            case "xlsx":
                return "fa-file-excel-o";
            case "audio":
                return "fa-file-audio-o";
            case "code":
                return "fa-file-code-o";
            case "image":
                return "fa-file-image-o";
            case "excel":
                return "fa-file-excel-o";
            case "powerpoint":
                return "fa-file-powerpoint-o";
            case "video":
                return "fa-file-video-o";
            case "word":
                return "fa-file-word-o";
            default:
                return "fa-file-o";
        }
    }
    showField(fieldName) {
        return (
            Object.values(this.state.hide).filter((item) => item === fieldName)
                .length === 0
        );
    }
    hideField(fieldName) {
        if (this.showField(fieldName)) {
            this.state.hide.push(fieldName);
        } else {
            this.state.hide.pop(fieldName);
        }
    }
}
FsFolder.serviceName = "fs.folder";
FsFolder.components = {
    Dropdown,
    DropdownItem,
    FileUploader,
    FsFolderItem,
};
FsFolder.template = "fs_folder.FsFolder";
FsFolder.props = {
    ...standardFieldProps,
};
export const FsFolderField = {
    component: FsFolder,
};

registry.category("fields").add("fs_folder", FsFolderField);
