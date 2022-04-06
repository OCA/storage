# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": "Storage Backend FTP",
    "summary": "Implement FTP Storage",
    "version": "15.0.1.0.1",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Acsone SA/NV,Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "external_dependencies": {"python": ["pyftpdlib"]},
    "depends": ["storage_backend"],
    "data": ["views/backend_storage_view.xml"],
}
