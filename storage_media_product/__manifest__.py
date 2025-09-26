# Copyright 2018 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage Media Product",
    "summary": "Link media to products and categories",
    "version": "18.0.1.0.0",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": False,
    "depends": ["storage_media", "product"],
    "data": [
        "security/ir.model.access.csv",
        "views/product.xml",
        "views/product_category.xml",
    ],
}
