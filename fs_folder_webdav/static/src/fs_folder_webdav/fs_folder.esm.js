import {FsFolder} from "@fs_folder/fs_folder/fs_folder.esm";
import {formatDateTime} from "@web/core/l10n/dates";
import {patch} from "@web/core/utils/patch";
const {DateTime} = luxon;

patch(FsFolder.prototype, {
    get isWebDAV() {
        const value = this.props.record.data[this.props.name];
        if (value) {
            const protocol = value.protocol;
            if (Array.isArray(protocol)) {
                return protocol.includes("webdav");
            }
            return protocol === "webdav";
        }
        return false;
    },

    get fieldDefinition() {
        let definition = super.fieldDefinition;
        if (this.isWebDAV && definition && Array.isArray(definition)) {
            // Remove 'created' and 'uid' as it is not implemented by webdav
            definition = definition.filter((item) => item.name !== "uid");
            definition = definition.filter((item) => item.name !== "created");

            definition.forEach((item) => {
                if (item.name === "mtime") {
                    item.type = "datetime";
                    item.value = (record) => {
                        // Record.modified format is "2025-09-20 15:25:39" which does not respect
                        // http://www.webdav.org/specs/rfc4918.html#PROPERTY_getlastmodified (why?)
                        const lastModifiedDateTime = record.modified;
                        if (lastModifiedDateTime) {
                            return formatDateTime(
                                DateTime.fromISO(
                                    lastModifiedDateTime.replace(" ", "T"),
                                    {zone: "utc"}
                                )
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
