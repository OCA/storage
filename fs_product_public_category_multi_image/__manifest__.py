# Copyright 2024 ForgeFlow (http://www.forgeflow.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Product Public Category Multi Image",
    "summary": """
        Manage multi images from extenal file system on eCommerce public categories""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_base_multi_image", "website_sale", "image_tag"],
    "data": [
        "security/fs_product_public_category_image.xml",
        "views/fs_product_public_category_image.xml",
        "views/product_public_category.xml",
    ],
    "demo": [],
    "development_status": "Alpha",
}
