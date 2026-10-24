# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Attachment PDF/A",
    "summary": """Convert PDF attachments to PDF/A""",
    "version": "18.0.1.0.0",
    "category": "Storage",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": [
        "base_setup",
    ],
    "data": [
        "data/ir_cron.xml",
        "data/config_parameter.xml",
        "data/pdfa3_metadata.xml",
        "views/res_config_settings.xml",
    ],
    "external_dependencies": {
        "bin": [
            "gs",
        ],
    },
    "installable": True,
}
