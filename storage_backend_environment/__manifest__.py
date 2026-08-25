# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage Backend Environment",
    "summary": "Allows to use server environment with storage backend",
    "version": "18.0.1.0.0",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Akretion, Camptocamp, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Beta",
    "installable": True,
    "depends": ["storage_backend", "server_environment"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "auto_install": True,
}
