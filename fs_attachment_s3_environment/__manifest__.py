# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Filesystem Attachment Backend S3",
    "summary": "Allows to use server environment with fs storage attachment S3",
    "version": "18.0.1.0.0",
    "category": "FS Storage",
    "website": "https://github.com/OCA/storage",
    "author": " ACSONE SA/NV, Dixmit, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Beta",
    "installable": True,
    "depends": ["fs_attachment_environment", "fs_attachment_s3"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
