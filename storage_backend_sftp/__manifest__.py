# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage Backend SFTP",
    "summary": "Implement SFTP Storage",
    "version": "16.0.1.0.0",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Akretion,Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    "external_dependencies": {"python": ["paramiko"]},
    "depends": ["storage_backend"],
    "data": ["views/backend_storage_view.xml"],
}
