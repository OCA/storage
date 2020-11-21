odoo.define('storage_image.image_handle', function (require) {
    "use strict";
    var core = require('web.core');
    var data = require('web.data');
    var Model = require("web.DataModel");
    var session = require('web.session');
    var pyeval = require('web.pyeval');
    var kanban = require("web_kanban.KanbanView");
    var m2m_kanban = require("web_kanban.Many2ManyKanbanView");

    data.DataSet.include({
        /* Inherit the DataSet to include a resequence on the parent record */
        init : function() {
            this._super.apply(this, arguments);
        },

        resequence_child: function (id, child_field, children_ids, options) {
            options = options || {};
            return session.rpc('/web/dataset/resequence_child', {
                model: this.model,
                target_id: id,
                child_field: child_field,
                children_ids: children_ids,
                context: pyeval.eval('context', this.get_context(options.context)),
            }).then(function (results) {
                return results;
            });
        },
    });

    core.view_registry.get("one2many_kanban").include({
        render: function () {
            var res = this._super.apply(this, arguments);
            var self = this;
            if (!self.options["read_only_mode"]) {
                if (self.options["creatable"]) {
                    this.$el.css('min-height', '50px')
                    this.$el.on('dragenter dragover', function (e) {
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
                this.$el.sortable({
                    tolerance: 'pointer',
                    cursor: 'move',
                    update: function () {
                        // Only if we have info related to the parent
                        if (self.dataset && self.dataset.parent_view.model && self.dataset.parent_view.datarecord && self.dataset.child_name) {
                            new data.DataSet(self, self.dataset.parent_view.model).resequence_child(self.dataset.parent_view.datarecord.id, self.dataset.child_name, self._getIDs());
                        }
                        else {
                            // If not, call the resequence on the relation record
                            new data.DataSet(self, self.record_options.model).resequence(self._getIDs());
                        }
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
                _.each(args, function (arg) {
                    new Model("storage.image").call("create", [arg]).done(function (image) {
                        self.x2m.node.attrs.context = {};
                        self.x2m.node.attrs.context["default_image_id"] = image;
                        self.add_record();
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
                var id = $(r).data('record').id;
                if (Number.isInteger(id)) {
                    ids.push(id);
                }
            });
            return ids;
        },
    });
});
