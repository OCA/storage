# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_image_ids = fields.Many2many(
        "product.image.relation",
        compute="_compute_variant_image_ids",
        store=True,
        string="Variant Images",
    )
    main_image_id = fields.Many2one(
        "storage.image",
        compute="_compute_main_image_id",
        # Store it to improve perf on product views
        store=True,
    )
    # small and medium image are here to replace
    # native image field on form and kanban
    variant_image_small_url = fields.Char(
        string="Variant main small image URL", related="main_image_id.image_small_url"
    )
    variant_image_medium_url = fields.Char(
        string="Variant main medium image URL", related="main_image_id.image_medium_url"
    )

    @api.depends(
        "product_tmpl_id.image_ids",
        "product_tmpl_id.image_ids.attribute_value_ids",
        "product_template_attribute_value_ids",
    )
    def _compute_variant_image_ids(self):
        for variant in self:
            img_relations = set()
            # Not sure sorting is needed here
            sorted_image_relations = variant.image_ids.sorted(
                key=lambda i: (i.sequence, i.image_id)
            )
            for image_rel in sorted_image_relations:
                if image_rel._match_variant(variant):
                    img_relations.add(image_rel.id)
            variant.variant_image_ids = list(img_relations) if img_relations else False

    @api.depends("variant_image_ids.sequence")
    def _compute_main_image_id(self):
        for record in self:
            record.main_image_id = record._get_main_image()

    def _get_main_image(self):
        return fields.first(
            self.variant_image_ids.sorted(key=lambda i: (i.sequence, i.image_id))
        ).image_id
