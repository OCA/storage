# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Image Thumbnail",
    "summary": """
        Generate and store thumbnail for images""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_image", "base_partition"],
    "data": [
        "views/ir_attachment.xml",
        "security/fs_thumbnail.xml",
        "views/fs_image_thumbnail_mixin.xml",
        "views/fs_thumbnail.xml",
    ],
    "demo": [],
    "maintainers": ["lmignon"],
    "development_status": "Alpha",
    "external_dependencies": {"python": ["python_slugify"]},
}
