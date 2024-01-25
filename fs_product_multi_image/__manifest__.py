# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Product Multi Image",
    "summary": """
        Manage multi images from extenal file system on product""",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_base_multi_image", "product", "sales_team", "image_tag"],
    "data": [
        "security/fs_product_category_image.xml",
        "security/fs_product_image.xml",
        "views/fs_product_category_image.xml",
        "views/fs_product_image.xml",
        "views/image_tag.xml",
        "views/product_category.xml",
        "views/product_product.xml",
        "views/product_template.xml",
    ],
    "demo": [],
    "maintainers": ["lmignon"],
    "development_status": "Alpha",
}
