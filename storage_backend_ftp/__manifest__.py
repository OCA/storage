# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Storage Backend FTP",
    "summary": "Implement FTP Storage",
    "version": "18.0.1.0.0",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Acsone SA/NV,Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "external_dependencies": {"python": ["pyftpdlib"],
    'installable': False,
},
    "depends": ["storage_backend"],
    "data": ["views/backend_storage_view.xml"],
    'installable': False,
}
