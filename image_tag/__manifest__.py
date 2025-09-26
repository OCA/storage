# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Image Tag",
    "summary": """
        Image tag model""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["server_environment"],
    "data": [
        "security/res_groups.xml",
        "security/image_tag.xml",
        "views/image_tag.xml",
    ],
    'installable': False,
}
