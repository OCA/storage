/* Copyright (C) 2020-Today Akretion (https://www.akretion.com)
    @author Raphaël Reverdy <raphael.reverdy@akretion.com>
    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/

odoo.define("storage_image_product_pos.ProductItem", function (require) {
    "use strict";

    var ProductItem = require("point_of_sale.ProductItem");
    var Registries = require("point_of_sale.Registries");

    var SIPPProductItem = (ProductItem) =>
        class SIPPProductItem extends ProductItem {
            get imageUrl() {
                return this.props.product.image_medium_url;
            }
        };
    Registries.Component.extend(ProductItem, SIPPProductItem);
    return SIPPProductItem;
});
