/* Copyright (C) 2018-Today Akretion (https://www.akretion.com)
    @author Pierrick Brun
    @author Sebastien Beau
    @author Raphaël Reverdy <raphael.reverdy@akretion.com>
    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/

odoo.define("storage_image_product_pos.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    models.PosModel.prototype.models.some(function (model) {
        if (model.model === "product.product") {
            if (model.fields.indexOf("image_medium_url") === -1) {
                model.fields.push("image_medium_url");
            }
            // Exit early
            return true;
        }
        return false;
    });
});
