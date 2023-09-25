# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Base Multi Media",
    "summary": """
        Give the possibility to store media data in external filesystem from odoo""",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": [
        "fs_file",
    ],
    "data": [
        "security/res_groups.xml",
        "security/fs_media_type.xml",
        "security/fs_media.xml",
        "views/fs_media.xml",
        "views/fs_media_relation_mixin.xml",
        "views/fs_media_type.xml",
    ],
    "demo": [],
    "maintainers": ["lmignon"],
    "development_status": "Alpha",
}
