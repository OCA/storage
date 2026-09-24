# Copyright 2026 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Attachment S3 Migration",
    "summary": """Async migration of attachments from local datastore to S3""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA), Cetmix",
    "website": "https://github.com/OCA/storage",
    "depends": [
        "queue_job",
        "fs_attachment_s3",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/queue_job_channel_data.xml",
        "views/fs_storage_views.xml",
        "views/migration_wizard_views.xml",
    ],
}
