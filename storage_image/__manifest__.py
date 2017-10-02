# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage Image",
    "summary": "Store image and resized image in a storage backend",
    "version": "8.0.1.0.0",
    "category": "Uncategorized",
    "website": "www.akretion.com",
    "author": " Akretion",
    "license": "AGPL-3",
    'installable': True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "storage_file",
        'product',
    ],
    "data": [
        'views/storage_thumbnail_view.xml',
        'views/storage_image_view.xml',
        # TODO fix js
        # 'views/js.xml',
        # 'views/image_resize_view.xml',
        'data/ir_parameter.xml',
        'security/ir.model.access.csv',
    ],
    "demo": [
    ],
    "qweb": [
        'static/src/xml/custom_xml.xml',
    ]
}
