# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Product Multi Media",
    "summary": """
        Link media to products and categories""",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_base_multi_media", "product", "sales_team"],
    "data": [
        "security/fs_product_category_media.xml",
        "security/fs_product_media.xml",
        "views/fs_product_category_media.xml",
        "views/fs_product_media.xml",
        "views/product_category.xml",
        "views/product_product.xml",
        "views/product_template.xml",
    ],
    "demo": [],
    "maintainers": ["lmignon"],
    "development_status": "Alpha",
}
