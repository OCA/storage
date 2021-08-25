odoo.define("storage_image.FieldStorageImageHandle", function (require) {
    "use strict";

    const registry = require("web.field_registry");
    const relational_fields = require("web.relational_fields");
    const utils = require("web.utils");

    const FieldStorageImageHandle = relational_fields.FieldOne2Many.extend({
        /**
         * @override
         */
        _render: function () {
            this.$el.addClass("o_field_storage_image_handle");
            if (!this.isReadonly && this.activeActions.create) {
                this.$el.on("dragover dragenter", (e) => {
                    this.$el.addClass("drop-zone");
                    e.preventDefault();
                    e.stopPropagation();
                });
                this.$el.on("dragleave dragend drop", (e) => {
                    this.$el.removeClass("drop-zone");
                    e.preventDefault();
                    e.stopPropagation();
                });
                this.$el.on("drop", (e) => {
                    // StopImmediatePropagation to avoid event bubbling
                    e.stopImmediatePropagation();
                    e.preventDefault();
                    this._uploadImages(e.originalEvent.dataTransfer.files);
                });
            }
            return this._super.apply(this, arguments);
        },

        _uploadImages: async function (files) {
            // Prepare storage.image values
            const storageImageValues = [];
            for (const file of files) {
                if (!file.type.includes("image")) {
                    continue;
                }
                const data = await utils.getDataURLFromFile(file);
                const content = data.split(",")[1];
                storageImageValues.push({
                    name: file.name,
                    data: content,
                });
            }
            // Create images
            await this._rpc({
                model: "storage.image",
                method: "create",
                args: [storageImageValues],
            }).then((record_ids) => {
                const context = record_ids.map(
                    (rec_id) =>
                        new Object({
                            default_image_id: rec_id,
                        })
                );
                this.trigger_up("add_record", {
                    forceEditable: context.length > 1 ? "bottom" : false,
                    allowWarning: true,
                    context: context,
                });
            });
        },
    });

    registry.add("storage_image_handle", FieldStorageImageHandle);
    return FieldStorageImageHandle;
});
