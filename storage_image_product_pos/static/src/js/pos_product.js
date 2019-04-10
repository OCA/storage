/* Copyright (C) 2018-Today Akretion (https://www.akretion.com)
    @author Pierrick Brun
    @author Sebastien Beau
    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/

odoo.define("storage_image_product.pos_product", function (require) {
    "use strict";

    var screens = require("point_of_sale.screens");
    var models = require('point_of_sale.models');

    /* ********************************************************
    Overload: point_of_sale.ProductListWidget

    - The overload will:
    - display product custom storage image;
    *********************************************************** */
    screens.ProductListWidget.include({
        get_product_image_url: function (product) {

            /* ************************************************
            Overload: 'get_product_image_url'
            */
            return product.image_medium_url;
        },
    });

    /* ********************************************************
    Overload: point_of_sale.PosModel
    - Overload module.PosModel.initialize function to load extra-data
         - Load 'image_medium_url' field of model product.product;
    *********************************************************** */
    models.PosModel.prototype.models.some(function (model) {
        if (model.model === 'product.product') {
            if (model.fields.indexOf('image_medium_url') === -1) {
                model.fields.push('image_medium_url');
            }
        }
        return false;
    });
});
