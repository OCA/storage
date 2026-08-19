# Copyright 2026 Dixmit
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Filesystem Storage Backend",
    "summary": "Allows to use server environment with fs storage",
    "version": "18.0.1.0.0",
    "category": "FS Storage",
    "website": "https://github.com/OCA/storage",
    "author": " ACSONE SA/NV, Dixmit, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Beta",
    "installable": True,
    "depends": ["fs_storage", "server_environment"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
