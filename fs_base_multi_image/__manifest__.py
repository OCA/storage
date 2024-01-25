# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Base Multi Image",
    "summary": """
        Mulitple Images from External File System""",
    "version": "16.0.1.1.0",
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
    "assets": {
        "web.assets_backend": [
            "fs_base_multi_image/static/src/fields/"
            "fs_image_relation_dnd_upload/fs_image_relation_dnd_upload.esm.js",
            "fs_base_multi_image/static/src/fields/"
            "fs_image_relation_dnd_upload/fs_image_relation_dnd_upload.scss",
            "fs_base_multi_image/static/src/fields/"
            "fs_image_relation_dnd_upload/fs_image_relation_dnd_upload.xml",
        ],
    },
    "demo": [],
    "maintainers": ["lmignon"],
    "development_status": "Alpha",
}
