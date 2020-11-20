odoo.define('storage_image.image_handle', function (require) {
    "use strict";
    var registry = require('web.field_registry');
    var relational_fields = require('web.relational_fields');

    var FieldImageHandle = relational_fields.FieldOne2Many.extend({
        _render: function () {
            var self = this;
            if (!this.isReadonly && this.activeActions.create) {
                this.$el.on('dragover dragenter', function (e) {
                    self.$el.addClass('is-dragover');
                    e.preventDefault();
                    e.stopPropagation();
                });
                this.$el.on('dragleave dragend drop', function (e) {
                    self.$el.removeClass('is-dragover');
                    e.preventDefault();
                    e.stopPropagation();
                });
                this.$el.on('drop', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.upload_images(e.originalEvent.dataTransfer.files);
                });
            }
            var res = this._super();
            if (this.mode == "edit") {
                this.$el.find(".o_kanban_view").sortable({
                    tolerance: 'pointer',
                    cursor: 'move',
                    update: function () {
                        self.trigger_up('resequence', {
                            "rowIDs": self._getIDs(),
                            "handleField": "sequence",
                            "offset": 0,
                        });
                    },
                });
            }
            return res
        },

        upload_images: function (files) {
            var self = this;
            var promises = [];
            _.each(files, function (file) {
                if (!file.type.includes("image")) {
                    return
                }
                var filePromise = new Promise(function (resolve) {
                    var reader = new FileReader();
                    reader.readAsDataURL(file);
                    reader.onload = function (upload) {
                        var data = upload.target.result;
                        data = data.split(',')[1];
                        resolve([file.name, data]);
                    };
                });
                promises.push(filePromise);
            });
            Promise.all(promises).then(function (fileContents) {
                var args = []
                _.each(fileContents, function (content) {
                    args.push({ 'name': content[0], 'image_medium_url': content[1] })
                });
                self._rpc({
                    model: 'storage.image',
                    method: 'create',
                    args: [args],
                }).then(function (images) {
                    var context = []
                    _.each(images, function (image) {
                        var context_val  = {}
                        context_val['default_image_id'] = image
                        context.push(context_val)
                    });
                    self.trigger_up("add_record", {
                        forceEditable: "bottom",
                        allowWarning: true,
                        context: context,
                    });
                });
            });
        },

        /**
         * @returns {integer[]} the virtual_ids of the records in the kanban view
         */
        _getIDs: function () {
            var ids = [];
            this.$el.find('.oe_kanban_vignette').each(function (index, r) {
                ids.push($(r).data('record').db_id);
            });
            return ids;
        },
    });
    registry.add('image_handle', FieldImageHandle);
    return FieldImageHandle;
});
