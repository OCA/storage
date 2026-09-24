# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Filesystem Attachment Backend Azure",
    "summary": "Allows to use server environment with fs storage attachment Azure",
    "version": "17.0.1.0.0",
    "category": "FS Storage",
    "website": "https://github.com/OCA/storage",
    "author": "ACSONE SA/NV,Camptocamp,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Beta",
    "installable": True,
    "depends": ["fs_attachment_environment", "fs_attachment_azure"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "maintainers": ["grindtildeath"],
}
