# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Pierrick Brun <https://github.com/pierrickbrun>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage Image Product POS",
    "summary": "Link images to products and categories inside POS",
    "version": "10.0.1.0.0",
    "category": "Storage",
    "website": "https://www.github.com/OCA/storage",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": False,
    "depends": ["storage_image_product", "point_of_sale"],
    "data": ["views/pos_product.xml"],
}
