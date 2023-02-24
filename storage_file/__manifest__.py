# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage File",
    "summary": "Storage file in storage backend",
    "version": "12.0.2.0.2",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Stable/Production",
    "application": False,
    "installable": True,
    "external_dependencies": {"python": ["slugify"]},
    "depends": ["storage_backend"],
    "data": [
        "views/storage_file_view.xml",
        "views/storage_backend_view.xml",
        "security/ir.model.access.csv",
        "security/storage_file.xml",
        "data/ir_cron.xml",
        "data/storage_backend.xml",
    ],
}
