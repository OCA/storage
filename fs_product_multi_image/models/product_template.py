# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.fs_image.fields import FSImage


class ProductTemplate(models.Model):

    _inherit = "product.template"

    image_ids = fields.One2many(
        string="Images", comodel_name="fs.product.image", inverse_name="product_tmpl_id"
    )
    main_image_id = fields.Many2one(
        string="Main Image",
        comodel_name="fs.product.image",
        compute="_compute_main_image_id",
        # Store it to improve perfs
        store=True,
    )
    image = FSImage(
        string="FS Main Image",
        related="main_image_id.image",
        readonly=True,
        store=False,
    )
    image_medium = FSImage(
        string="FS Image Medium",
        related="main_image_id.image_medium",
        readonly=True,
        store=False,
    )

    def _sort_multi_image_id_key(self, img):
        # this sort method is required to deal with
        # new id when the image is added with when
        # clicking on the add image button on the product
        # view (not the one into the widget)
        key = [img.sequence]
        id_ = img.id
        if isinstance(id_, models.NewId):
            if id_.origin:
                key.append(f"a{id_.origin}")
            elif id_.ref:
                key.append(id_.ref)
        else:
            key.append(f"a{id_}")
        return tuple(key)

    @api.depends("image_ids", "image_ids.sequence")
    def _compute_main_image_id(self):
        for record in self:
            image_ids = record.image_ids.sorted(key=self._sort_multi_image_id_key)
            record.main_image_id = image_ids and image_ids[0] or None
