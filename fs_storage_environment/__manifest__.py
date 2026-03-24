# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Filesystem Storage Backend - Server Environment",
    "summary": "Use Server Environment feature to manage the concept of Storage",
    "version": "18.0.1.0.0",
    "category": "FS Storage",
    "website": "https://github.com/OCA/storage",
    "author": " ACSONE SA/NV, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Beta",
    "installable": True,
    "depends": ["fs_storage", "server_environment"],
    "data": [
        "views/fs_storage_view.xml",
    ],
    "auto_install": True,
}
