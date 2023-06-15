# Copyright 2023 ForgeFlow (http://www.forgeflow.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage Image Product Public Category",
    "summary": "Link images to products and categories",
    "version": "14.0.1.0.0",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " ForgeFlow, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Production/Stable",
    "installable": True,
    "depends": [
        "storage_image",
        "product",
        "sale",
        "website_sale",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/public_category_image_relation.xml",
        "views/storage_image.xml",
    ],
}
