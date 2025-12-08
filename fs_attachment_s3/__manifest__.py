# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Attachment S3",
    "summary": """Store attachments into S3 complient filesystem""",
    "version": "19.0.1.1.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_attachment"],
    "external_dependencies": {
        "python": [
            "fsspec[s3]",
        ],
    },
    "data": [
        "views/fs_storage.xml",
    ],
    "maintainers": ["lmignon"],
    "installable": True,
}
