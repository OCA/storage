# Copyright 2018 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    media_ids = fields.Many2many("storage.media")
