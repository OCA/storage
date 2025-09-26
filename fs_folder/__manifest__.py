# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Fs Folder",
    "summary": """A module to link to Odoo records and manage from record forms forlders
            from external file systems """,
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": [
        "fs_storage",
    ],
    "data": [
        "views/fs_storage.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "fs_folder/static/src/**/*",
        ],
    },
    "demo": [],
    "installable": False,
    "maintainers": ["lmignon"],
}
