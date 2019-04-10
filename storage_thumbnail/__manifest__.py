# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage Thumbnail",
    "summary": "Abstract module that add the possibility to have thumbnail",
    "version": "10.0.1.0.0",
    "category": "Storage",
    "website": "www.akretion.com",
    "author": " Akretion",
    "license": "AGPL-3",
    "installable": True,
    "external_dependencies": {"python": [], "bin": []},
    "depends": ["storage_file"],
    "data": [
        "data/ir_parameter.xml",
        "views/storage_thumbnail_view.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [],
    "qweb": [],
}
