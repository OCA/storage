# Copyright 2024 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Filesystem Storage For Microsoft Drives",
    "summary": "Add the microsoft drives (OneDrive, Sharepoint) as a storage backend",
    "version": "18.0.1.0.0",
    "category": "FS Storage",
    "website": "https://github.com/OCA/storage",
    "author": " ACSONE SA/NV, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Beta",
    "installable": False,
    "depends": [
        "microsoft_drive_account",
        "fs_storage",
    ],
    "external_dependencies": {"python": ["msgraphfs", "fsspec>=2025.0.0"]},
    "maintainers": ["lmignon"],
}
