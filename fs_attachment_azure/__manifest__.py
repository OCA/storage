# Copyright 2025 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fs Attachment Azure",
    "summary": """Store attachments into Azure Blob storage""",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Camptocamp,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/storage",
    "depends": ["fs_attachment"],
    "external_dependencies": {
        "python": [
            "adlfs",
        ],
    },
    "data": [
        "views/fs_storage.xml",
    ],
    "maintainers": ["grindtildeath"],
}
