# Copyright 2020 ACSONE SA/NV
# Copyright 2021 Camptocamp (http://www.camptocamp.com).
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.fs_image.fields import FSImage


class ProductBrand(models.Model):
    _inherit = "product.brand"

    image_ids = fields.One2many(
        string="Images",
        comodel_name="fs.product.brand.image",
        inverse_name="brand_id",
    )
    image = FSImage(related="image_ids.image", readonly=True, store=False)
    image_medium = FSImage(related="image_ids.image_medium", readonly=True, store=False)
