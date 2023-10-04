# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_media_ids = fields.Many2many(
        "fs.product.media",
        compute="_compute_variant_media_ids",
        store=True,
        string="Variant Medias",
    )

    @api.depends(
        "product_tmpl_id.media_ids",
        "product_tmpl_id.media_ids.sequence",
        "product_tmpl_id.media_ids.attribute_value_ids",
        "product_template_attribute_value_ids",
    )
    def _compute_variant_media_ids(self):
        for variant in self:
            variant_media_ids = variant.media_ids.filtered(
                lambda i: i._match_variant(variant)
            )
            variant_media_ids = variant_media_ids.sorted(
                key=lambda i: (i.sequence, i.name)
            )
            variant.variant_media_ids = variant_media_ids
