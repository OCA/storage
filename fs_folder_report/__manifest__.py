# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Folder Report",
    "summary": """Save your pdf reports into the folder associated to your record.""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": [
        "fs_attachment",
        "fs_folder",
    ],
    "data": [
        "views/ir_actions_report.xml",
    ],
    "demo": [],
    "installable": True,
    "maintainers": ["lmignon"],
}
