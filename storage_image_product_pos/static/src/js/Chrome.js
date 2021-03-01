/* Copyright (C) 2020-Today Akretion (https://www.akretion.com)
    @author Raphaël Reverdy <raphael.reverdy@akretion.com>
    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/

odoo.define("storage_image_product_pos.Chrome", function (require) {
    "use strict";

    var Chrome = require("point_of_sale.Chrome");
    var Registries = require("point_of_sale.Registries");

    var SIPPChrome = (Chrome) =>
        class SIPPChrome extends Chrome {
            _preloadImages() {
                this.env.pos.db.get_product_by_category(0).forEach(function (product) {
                    if (!product.image_medium_url) return;
                    var image = new Image();
                    image.src = product.image_medium_url;
                });
                Object.values(this.env.pos.db.category_by_id).forEach(function (
                    category
                ) {
                    if (!category.image_medium_url) return;
                    var image = new Image();
                    image.src = category.image_medium_url;
                });
                ["backspace.png", "bc-arrow-big.png"].forEach(function (imageName) {
                    var image = new Image();
                    image.src = `/point_of_sale/static/src/img/${imageName}`;
                });
            }
        };

    Registries.Component.extend(Chrome, SIPPChrome);
    return SIPPChrome;
});
