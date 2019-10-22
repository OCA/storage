# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from slugify import slugify
except ImportError:
    _logger.debug("Cannot `import slugify`.")


class ThumbnailMixing(models.AbstractModel):
    _name = "thumbnail.mixin"
    _description = "Thumbnail Mixin add the thumbnail capability"

    thumbnail_ids = fields.One2many(
        comodel_name="storage.thumbnail",
        string="Thumbnails",
        inverse_name="res_id",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    image_medium_url = fields.Char(readonly=True)
    image_small_url = fields.Char(readonly=True)

    def _get_medium_thumbnail(self):
        return self.get_or_create_thumbnail(128, 128)

    def _get_small_thumbnail(self):
        return self.get_or_create_thumbnail(64, 64)

    def get_or_create_thumbnail(self, size_x, size_y, url_key=None):
        self.ensure_one()
        if url_key:
            url_key = slugify(url_key)
        thumbnail = self.env["storage.thumbnail"].browse()
        for th in self.thumbnail_ids:
            if th.size_x == size_x and th.size_y == size_y:
                if url_key and url_key != th.url_key:
                    continue
                thumbnail = th
                break
        if not thumbnail and self.data:
            vals = self.env["storage.thumbnail"]._prepare_thumbnail(
                self, size_x, size_y, url_key
            )
            thumbnail = self.thumbnail_ids.create(vals)
            # invalidate field since a new record is created
            # The actual model is a mixin, therefore the inverse into
            # storage.thumbnail is not defined as a one2many to this mixin.
            # As consequence, the ORM is not able to trigger the invalidation
            # of thumbnail_ids on our mixin
            self.thumbnail_ids.refresh()
        return thumbnail

    def generate_odoo_thumbnail(self):
        self_sudo = self.sudo()
        self.write(
            {
                "image_medium_url": self_sudo._get_medium_thumbnail().url,
                "image_small_url": self_sudo._get_small_thumbnail().url,
            }
        )
        return True

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.generate_odoo_thumbnail()
        return record
