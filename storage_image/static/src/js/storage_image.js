
console.log('loading')
openerp.storage_image = function(instance, local) {
"use strict";
var QWeb = instance.web.qweb;
var _t = instance.web._t;
instance.web.form.widgets.add('image_url', 'instance.web.form.FieldImageUrl');
console.log('loading');
instance.web.form.FieldImageUrl = instance.web.form.FieldBinaryImage.extend({
    render_value: function() {
        var self = this;
        var url = this.get('value');
        if (!url) {
            url = this.placeholder
        }

        var $img = $(QWeb.render("FieldBinaryImage-img", { widget: this, url: url }));
        $($img).click(function(e) {
            if(self.view.get("actual_mode") == "view") {
                var $button = $(".oe_form_button_edit");
                $button.openerpBounce();
                e.stopPropagation();
            }
        });
        this.$el.find('> img').remove();
        this.$el.prepend($img);
        $img.load(function() {
            if (! self.options.size)
                return;
            $img.css("max-width", "" + self.options.size[0] + "px");
            $img.css("max-height", "" + self.options.size[1] + "px");
        });
        $img.on('error', function() {
            self.on_clear();
            $img.attr('src', self.placeholder);
            instance.webclient.notification.warn(_t("Image"), _t("Could not display the selected image."));
        });
    },
});
};
