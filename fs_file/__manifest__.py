# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs File",
    "summary": """
        Field to store files into filesystem storages""",
    "version": "16.0.1.0.4",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_attachment"],
    "data": [],
    "demo": [],
    "maintainers": ["lmignon"],
    "development_status": "Alpha",
    "assets": {
        "web.assets_backend": [
            "fs_file/static/src/**/*",
        ],
    },
}
