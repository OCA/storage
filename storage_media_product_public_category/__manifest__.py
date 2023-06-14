# Copyright 2023 ForgeFlow (http://www.forgeflow.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage Media Product",
    "summary": "Link media to public categories",
    "version": "14.0.1.0.0",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " ForgeFlow, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["storage_media", "product", "website_sale"],
    "data": [
        "views/product_public_category.xml",
    ],
}
