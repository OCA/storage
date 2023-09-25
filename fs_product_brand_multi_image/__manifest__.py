# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Product Brand Multi Image",
    "summary": """
        Link images to product brands""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_base_multi_image", "product_brand", "sales_team", "image_tag"],
    "data": [
        "security/fs_product_brand_image.xml",
        "views/fs_product_brand_image.xml",
        "views/product_brand.xml",
    ],
    "demo": [],
    "maintainers": ["lmignon"],
    "development_status": "Alpha",
}
