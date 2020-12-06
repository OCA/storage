odoo.define("storage_image.image_url", function (require) {
    "use strict";
    var core = require("web.core");
    var _t = core._t;
    var qweb = core.qweb;
    var registry = require("web.field_registry");
    var basic_fields = require("web.basic_fields");

    var FieldImageUrl = basic_fields.FieldBinaryImage.extend({
        _render: function () {
            // This code is an override that only change the way the rule is build
            // In Odoo core if the value is not a binary, Odoo always query the
            // server on /web/image....
            var self = this;
            var url = this.value;
            if (!url) {
                url = this.placeholder;
            } else if (!url.startsWith("http")) {
                url = "data:image/png;base64," + url;
            }

            /*
             From here it's the same code as in FieldBinaryImage
             */
            var $img = $(qweb.render("FieldBinaryImage-img", {widget: this, url: url}));
            // Override css size attributes (could have been defined in css files)
            // if specified on the widget
            var width = this.nodeOptions.size
                ? this.nodeOptions.size[0]
                : this.attrs.width;
            var height = this.nodeOptions.size
                ? this.nodeOptions.size[1]
                : this.attrs.height;
            if (width) {
                $img.attr("width", width);
                $img.css("max-width", width + "px");
            }
            if (height) {
                $img.attr("height", height);
                $img.css("max-height", height + "px");
            }
            this.$("> img").remove();
            this.$el.prepend($img);
            $img.on("error", function () {
                $img.attr("src", self.placeholder);
                self.do_warn(_t("Image"), _t("Could not display the selected image."));
            });
        },
    });
    registry.add("image_url", FieldImageUrl);
    return FieldImageUrl;
});
