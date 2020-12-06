# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage Image Product Brand",
    "summary": """Link images to product brands""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://www.github.com/OCA/storage",
    "depends": ["storage_image", "product_brand"],
    "data": [
        "security/product_brand_image_relation.xml",
        "views/product_brand.xml",
        "views/product_brand_image_relation.xml",
    ],
    "installable": False,
}
