# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Base Multi Image",
    "summary": """
        Mulitple Images from External File System""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": [
        "fs_image",
    ],
    "data": [
        "security/res_groups.xml",
        "security/fs_image.xml",
        "views/fs_image.xml",
        "views/fs_image_relation_mixin.xml",
    ],
    "demo": [],
    "maintainers": ["lmignon"],
    "development_status": "Alpha",
}
