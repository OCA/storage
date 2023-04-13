# Copyright 2017-2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


{
    "name": "Base Attachment Object Store",
    "summary": "Stora attachments on external object store",
    "version": "16.0.1.0.0",
    "author": "Camptocamp, ACSONE SA/NV, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Knowledge Management",
    "depends": ["fs_storage"],
    "website": "https://github.com/OCA/storage",
    "data": [
        "security/fs_file_gc.xml",
        "views/fs_storage.xml",
        "data/res_config_settings_data.xml",
    ],
    "external_dependencies": {"python": ["python_slugify"]},
    "installable": True,
    "auto_install": False,
}
