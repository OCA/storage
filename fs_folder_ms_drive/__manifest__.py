# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Fs Folder Msgraph",
    "summary": """Display and manage your files from Microsoft drives from within
            Odoo""",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_folder", "fs_storage_ms_drive"],
    "data": [],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "fs_folder_ms_drive/static/src/**/*",
        ],
    'installable': False,
},
    "maintainers": ["lmignon"],
    'installable': False,
}
