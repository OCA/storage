# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage Backend SFTP",
    "summary": "Implement SFTP Storage",
    "version": "14.0.1.0.0",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Akretion,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "external_dependencies": {"python": ["paramiko"]},
    "depends": ["storage_backend"],
    "data": ["views/backend_storage_view.xml"],
}
