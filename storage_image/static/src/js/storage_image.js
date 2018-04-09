odoo.define('storage_image.image_url', function (require) {
"use strict";
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;

var FieldBinaryImage = core.form_widget_registry.map.image;
var FieldImageUrl = FieldBinaryImage.extend({
    render_value: function() {
        var self = this;
        var url = this.get('value');
        if (!url) {
            url = this.placeholder;
        } else if (!url.startsWith('http')) {
            url = 'data:image/png;base64,' + url;
        }
        var $img = $(QWeb.render("FieldBinaryImage-img", { widget: this, url: url }));
        $img.click(function(e) {
            if(self.view.get("actual_mode") === "view") {
                var $button = $(".o_form_button_edit");
                $button.openerpBounce();
                e.stopPropagation();
            }
        });
        this.$('> img').remove();
        if (self.options.size) {
            $img.css("width", "" + String(self.options.size[0]) + "px");
            $img.css("height", "" + String(self.options.size[1]) + "px");
        }
        this.$el.prepend($img);
        $img.on('error', function() {
            self.on_clear();
            $img.attr('src', self.placeholder);
            self.do_warn(_t("Image"), _t("Could not display the selected image."));
        });
    },
});
core.form_widget_registry.add('image_url', FieldImageUrl);
return FieldImageUrl;
});
