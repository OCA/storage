# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Microsoft account for Drive",
    "summary": """
        Link user with Microsoft """,
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": [
        "microsoft_account",
    ],
    "data": [
        "wizards/microsoft_drive_account_reset.xml",
        "views/res_users.xml",
        "security/microsoft_drive_account_reset.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "microsoft_drive_account/static/src/js/fields/**/*",
        ],
    'installable': False,
},
    "maintainers": ["lmignon"],
    'installable': False,
}
