# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage File",
    "summary": "Storage file in storage backend",
    "version": "18.0.1.0.0",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Production/Stable",
    "application": False,
    "installable": False,
    "external_dependencies": {"python": ["python_slugify"]},
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
