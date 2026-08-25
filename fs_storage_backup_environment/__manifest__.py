# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Filesystem Attachment Backend",
    "summary": "Allows to use server environment with fs storage attachment",
    "version": "16.0.1.0.1",
    "category": "FS Storage",
    "website": "https://github.com/OCA/storage",
    "author": " ACSONE SA/NV, Dixmit, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Beta",
    "installable": True,
    "depends": ["fs_storage_environment", "fs_storage_backup"],
    "data": [],
    "auto_install": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
