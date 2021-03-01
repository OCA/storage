odoo.define("storage_image.image_handle", function (require) {
    "use strict";
    var registry = require("web.field_registry");
    var relational_fields = require("web.relational_fields");

    var FieldImageHandle = relational_fields.FieldOne2Many.extend({
        _render: function () {
            var self = this;
            if (!this.isReadonly && this.activeActions.create) {
                this.$el.on("dragover dragenter", function (e) {
                    self.$el.addClass("is-dragover");
                    e.preventDefault();
                    e.stopPropagation();
                });
                this.$el.on("dragleave dragend drop", function (e) {
                    self.$el.removeClass("is-dragover");
                    e.preventDefault();
                    e.stopPropagation();
                });
                this.$el.on("drop", function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.upload_images(e.originalEvent.dataTransfer.files);
                });
            }
            return this._super();
        },

        upload_images: function (files) {
            var self = this;
            var promises = [];
            _.each(files, function (file) {
                if (!file.type.includes("image")) {
                    return;
                }
                var filePromise = new Promise(function (resolve) {
                    var reader = new FileReader();
                    reader.readAsDataURL(file);
                    reader.onload = function (upload) {
                        var data = upload.target.result;
                        data = data.split(",")[1];
                        resolve([file.name, data]);
                    };
                });
                promises.push(filePromise);
            });
            Promise.all(promises).then(function (fileContents) {
                var args = [];
                _.each(fileContents, function (content) {
                    args.push({name: content[0], image_medium_url: content[1]});
                });
                self._rpc({
                    model: "storage.image",
                    method: "create",
                    args: [args],
                }).then(function (images) {
                    var context = [];
                    _.each(images, function (image) {
                        var context_val = {};
                        var default_image_field = "default_image_id";
                        context_val[default_image_field] = image;
                        context.push(context_val);
                    });
                    self.trigger_up("add_record", {
                        forceEditable: "bottom",
                        allowWarning: true,
                        context: context,
                    });
                });
            });
        },
    });
    registry.add("image_handle", FieldImageHandle);
    return FieldImageHandle;
});
