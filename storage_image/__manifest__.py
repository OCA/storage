# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage Image",
    "summary": "Store image and resized image in a storage backend",
    "version": "12.0.2.0.0",
    "category": "Storage",
    "website": "https://www.github.com/OCA/storage",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Stable/Production",
    "installable": True,
    "depends": ["storage_thumbnail"],
    "external_dependencies": {"python": ["requests_mock"]},
    "data": [
        "views/storage_image_view.xml",
        "views/js.xml",
        "data/ir_parameter.xml",
        "security/res_group.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
    ],
    "qweb": ["static/src/xml/custom_xml.xml"],
}
