# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class StorageMainImageMixin(models.AbstractModel):

    _name = "storage.main.image.mixin"
    _description = "This is a helper that retrieves the main image for a record"
    # To inherit - this points to the image relation model depending on the record
    # model and that inherits from image.relation.abstract
    _field_image_ids = None

    main_image_id = fields.Many2one(
        "storage.image",
        string="Main Image",
        compute="_compute_main_image_id",
        # Store it for performances
        store=True,
    )

    @api.model
    def _main_image_id_depends(self):
        return (
            [".".join([self._field_image_ids, "sequence"])]
            if self._field_image_ids
            else []
        )

    @api.depends(lambda self: self._main_image_id_depends())
    def _compute_main_image_id(self):
        for record in self:
            record.main_image_id = record._get_main_image()

    def _select_main_image(self, images):
        return fields.first(
            images.sorted(key=lambda i: (i.sequence, i.image_id))
        ).image_id

    def _filter_main_image_id(self):
        """
            Helper to bypass the main image selected by sequence
        """
        return self[self._field_image_ids].browse()

    def _get_main_image(self):
        match_image = self._filter_main_image_id()
        if match_image:
            return self._select_main_image(match_image)
        return self._select_main_image(self[self._field_image_ids])
