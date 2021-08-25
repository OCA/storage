# Copyright 2020 ACSONE SA/NV
# Copyright 2021 Camptocamp (http://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductBrand(models.Model):
    _inherit = "product.brand"

    image_ids = fields.One2many(
        comodel_name="product.brand.image.relation",
        inverse_name="brand_id",
        string="Images",
    )
    main_image_id = fields.Many2one(
        comodel_name="storage.image",
        compute="_compute_main_image_id",
        # Store it to improve perf on product views
        store=True,
    )
    image_small_url = fields.Char(
        string="Main Image URL (small)", related="main_image_id.image_small_url"
    )
    image_medium_url = fields.Char(
        string="Main Image URL (medium)", related="main_image_id.image_medium_url"
    )

    @api.depends("image_ids.sequence")
    def _compute_main_image_id(self):
        for rec in self:
            rec.main_image_id = fields.first(rec.image_ids).image_id
