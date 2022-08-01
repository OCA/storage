# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage Image Product Brand",
    "summary": "Link images to product brands",
    "version": "14.0.2.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["storage_image_product", "product_brand"],
    "data": [
        "security/product_brand_image_relation.xml",
        "views/product_brand.xml",
        "views/product_brand_image_relation.xml",
    ],
}
