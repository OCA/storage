# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Pierrick Brun <https://github.com/pierrickbrun>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Storage Image Category POS",
    "summary": "Add image handling to product category and use it for POS",
    "version": "10.0.1.0.0",
    "category": "Storage",
    "website": "www.akretion.com",
    "author": " Akretion",
    "license": "AGPL-3",
    "installable": False,
    "depends": ["storage_image_product_pos", "pos_remove_pos_category"],
    "data": ["views/product_category.xml"],
}
