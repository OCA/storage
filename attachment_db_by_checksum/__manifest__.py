# Copyright 2021 Lorenzo Battistini @ TAKOBI
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "DB attachments saved by checksum",
    "summary": "Allow to identify database attachments through their hash, "
               "avoiding duplicates",
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": "TAKOBI, Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
}
