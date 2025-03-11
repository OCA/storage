# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Filesystem Storage Backend",
    "summary": "Implement the concept of Storage with amazon S3, sftp...",
    "version": "16.0.1.3.4",
    "category": "FS Storage",
    "website": "https://github.com/OCA/storage",
    "author": " ACSONE SA/NV, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Beta",
    "installable": True,
    "depends": ["base", "base_sparse_field", "server_environment"],
    "data": [
        "views/fs_storage_view.xml",
        "security/ir.model.access.csv",
        "wizards/fs_test_connection.xml",
    ],
    "demo": ["demo/fs_storage.xml"],
    "external_dependencies": {"python": ["fsspec>=2024.5.0"]},
}
