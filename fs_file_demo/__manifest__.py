# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs File Demo",
    "summary": """Demo addon for fs_file and fs_image""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": [
        "fs_file",
        "fs_image",
    ],
    "data": [
        "security/fs_file.xml",
        "views/fs_file.xml",
    ],
    "demo": [],
    "development_status": "Alpha",
}
