import {markup, onWillStart, useState, useSubEnv} from "@odoo/owl";
import {FsFolder} from "@fs_folder/fs_folder/fs_folder.esm";
import {PreviewIframe} from "../components/preview_iframe.esm";
import {_t} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {formatDateTime} from "@web/core/l10n/dates";
import {patch} from "@web/core/utils/patch";
import {rpc} from "@web/core/network/rpc";
const {DateTime} = luxon;

patch(FsFolder.prototype, {
    setup() {
        super.setup();
        useSubEnv({
            onOpenInMsDrive: (record) => {
                this.onOpenInMsDrive(record);
            },
            onCloseUrlPreview: () => {
                this.onCloseUrlPreview();
            },
            isMSGD: () => {
                return this.isMSGD;
            },
        });
        this.urlPreview = useState({
            url: null,
            show: false,
        });
        onWillStart(this.onWillStart);
    },

    async onWillStart() {
        if (this.isMSGD) {
            this.ensureMsDriveAccountConnected();
        }
    },

    async ensureMsDriveAccountConnected() {
        const result = await rpc("/ms_drive_account/status", {
            from_url: window.location.href,
        });
        if (result.status === "not_connected") {
            window.location.assign(result.url);
        }
    },

    get isMSGD() {
        const value = this.props.record.data[this.props.name];
        if (value) {
            const protocol = value.protocol;
            if (Array.isArray(protocol)) {
                return protocol.includes("msgd");
            }
            return protocol === "msgd";
        }
        return false;
    },

    async onClickPreview(row) {
        if (!this.isMSGD) {
            return super.onClickPreview(row);
        }

        if (this.props.record.data[this.props.name]) {
            const path = [...this.state.path];
            if (row) {
                path.push(row.name);
            }
            const record = this.props.record;
            rpc(
                `/fs_folder_ms_drive/get_ms_drive_preview_url/${record.resModel}/${record.resId}/${this.props.name}`,
                {
                    path: path.join("/"),
                }
            ).then((url) => {
                this.urlPreview.url = url;
                this.urlPreview.show = true;
            });
        }
    },
    async onClickDownload(row) {
        if (!this.isMSGD) {
            return super.onClickDownload(row);
        }

        if (this.props.record.data[this.props.name]) {
            const path = [...this.state.path];
            if (row) {
                path.push(row.name);
            }
            const record = this.props.record;
            rpc(
                `/fs_folder_ms_drive/get_ms_drive_download_url/${record.resModel}/${record.resId}/${this.props.name}`,
                {
                    path: path.join("/"),
                }
            ).then(async (url) => {
                await downloadFile(url);
            });
        }
    },

    async onOpenInMsDrive(row) {
        if (!this.isMSGD) {
            return;
        }
        if (this.props.record.data[this.props.name]) {
            const path = [...this.state.path];
            if (row) {
                path.push(row.name);
            }
            const record = this.props.record;
            rpc(
                `/fs_folder_ms_drive/get_ms_drive_url/${record.resModel}/${record.resId}/${this.props.name}`,
                {
                    path: path.join("/"),
                }
            ).then((url) => {
                if (url) {
                    window.open(url, "_blank");
                }
            });
        }
    },

    async onClickInitialize() {
        const record = this.props.record;
        const result = await rpc(
            `/fs_folder_ms_drive/is_ms_drive/${record.resModel}/${record.resId}/${this.props.name}`
        );
        if (result.is_ms_drive) {
            this.ensureMsDriveAccountConnected();
        }
        return super.onClickInitialize();
    },

    onCloseUrlPreview() {
        this.urlPreview.show = false;
        this.urlPreview.url = null;
    },

    get fieldDefinition() {
        let definition = super.fieldDefinition;
        // Update the field definition to reflect the format used by the MS Graph Data connector
        // tht definition is a list of object and we will modify only some properties of
        // specific objects
        if (this.isMSGD && definition && Array.isArray(definition)) {
            // First we remove the 'uid' field if it exists
            definition = definition.filter((item) => item.name !== "uid");
            // Then we add the description, the createdBy field and modifiedBy field
            definition.push({
                sequence: 15,
                name: "description",
                type: "char",
                optional: true,
                string: _t("Description"),
                value: (record) => {
                    return markup(record?.item_info?.description || "");
                },
            });
            definition.push({
                sequence: 35,
                name: "createdBy",
                type: "char",
                optional: true,
                string: _t("Created By"),
                value: (record) => {
                    const user = record?.item_info?.createdBy?.user;
                    if (user) {
                        return user.displayName;
                    }
                    return "";
                },
            });
            definition.push({
                sequence: 45,
                name: "modifiedBy",
                type: "char",
                optional: true,
                string: _t("Modified By"),
                value: (record) => {
                    const user = record?.item_info?.lastModifiedBy?.user;
                    if (user) {
                        return user.displayName;
                    }
                    return "";
                },
            });

            // We finally format the modified time and create time line
            definition.forEach((item) => {
                if (item.name === "created") {
                    item.type = "datetime";
                    item.value = (record) => {
                        const createdDateTime =
                            record.item_info?.fileSystemInfo?.createdDateTime;
                        if (createdDateTime) {
                            return formatDateTime(DateTime.fromISO(createdDateTime));
                        }
                        return "";
                    };
                    item.cmp = (recordA, recordB) => {
                        const createdA =
                            recordA.item_info?.fileSystemInfo?.createdDateTime;
                        const createdB =
                            recordB.item_info?.fileSystemInfo?.createdDateTime;
                        return DateTime.fromISO(createdA) - DateTime.fromISO(createdB);
                    };
                } else if (item.name === "mtime") {
                    item.type = "datetime";
                    item.value = (record) => {
                        const lastModifiedDateTime =
                            record.item_info?.fileSystemInfo?.lastModifiedDateTime;
                        if (lastModifiedDateTime) {
                            return formatDateTime(
                                DateTime.fromISO(lastModifiedDateTime)
                            );
                        }
                        return "";
                    };
                }
            });
        }

        return definition;
    },
});

FsFolder.components = {
    ...FsFolder.components,
    PreviewIframe,
};
