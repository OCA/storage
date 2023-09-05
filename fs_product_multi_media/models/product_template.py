# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):

    _inherit = "product.template"

    media_ids = fields.One2many(
        string="Medias",
        comodel_name="fs.product.media",
        inverse_name="product_tmpl_id",
    )
