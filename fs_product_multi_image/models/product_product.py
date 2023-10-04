# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from odoo.addons.fs_image.fields import FSImage


class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_image_ids = fields.Many2many(
        "fs.product.image",
        compute="_compute_variant_image_ids",
        store=True,
        string="Variant Images",
    )
    main_image_id = fields.Many2one(
        string="Main Image",
        comodel_name="fs.product.image",
        compute="_compute_main_image_id",
        # Store it to improve perfs
        store=True,
    )
    image = FSImage(related="main_image_id.image", readonly=True, store=False)
    image_medium = FSImage(
        related="main_image_id.image_medium", readonly=True, store=False
    )

    @api.depends(
        "product_tmpl_id.image_ids",
        "product_tmpl_id.image_ids.sequence",
        "product_tmpl_id.image_ids.attribute_value_ids",
        "product_template_attribute_value_ids",
    )
    def _compute_variant_image_ids(self):
        for variant in self:
            variant_image_ids = variant.image_ids.filtered(
                lambda i: i._match_variant(variant)
            )
            variant_image_ids = variant_image_ids.sorted(
                key=lambda i: (i.sequence, i.name)
            )
            variant.variant_image_ids = variant_image_ids

    @api.depends("variant_image_ids", "variant_image_ids.sequence")
    def _compute_main_image_id(self):
        for record in self:
            record.main_image_id = record._get_main_image()

    def _select_main_image(self, images):
        return fields.first(images.sorted(key=lambda i: (i.sequence, i.id))).id

    def _get_main_image(self):
        match_image = self.variant_image_ids.filtered(
            lambda i: i.attribute_value_ids
            == self.mapped(
                "product_template_attribute_value_ids.product_attribute_value_id"
            )
        )
        if match_image:
            return self._select_main_image(match_image)
        return self._select_main_image(self.variant_image_ids)
