# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage Backend S3",
    "summary": "Implement amazon S3 Storage",
    "version": "15.0.1.0.1",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    "external_dependencies": {"python": ["boto3<=1.15.18"]},
    "depends": ["storage_backend"],
    "data": ["views/backend_storage_view.xml"],
}
