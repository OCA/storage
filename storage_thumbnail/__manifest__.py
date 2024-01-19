# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Storage Thumbnail",
    "summary": "Abstract module that add the possibility to have thumbnail",
    "version": "14.0.2.2.2",
    "category": "Storage",
    "website": "https://github.com/OCA/storage",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Production/Stable",
    "installable": True,
    "depends": ["storage_file"],
    "data": [
        "data/ir_parameter.xml",
        "views/storage_thumbnail_view.xml",
        "security/ir.model.access.csv",
    ],
}
