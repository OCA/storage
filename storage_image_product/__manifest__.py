# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage Image Product",
    "summary": "Link images to products and categories",
    "version": "13.0.1.2.0",
    "category": "Storage",
    "website": "https://www.github.com/OCA/storage",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Production/Stable",
    "installable": False,
    "depends": ["storage_image", "product", "sale"],  # only for the menu
    "data": [
        "security/ir.model.access.csv",
        "views/product_template.xml",
        "views/product_image_relation.xml",
        "views/product_product.xml",
        "views/product_category.xml",
        "views/image_tag.xml",
        "views/storage_image.xml",
    ],
}
