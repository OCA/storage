# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging

from odoo import api, fields, models, tools

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
    thumb_medium_id = fields.Many2one(
        comodel_name="storage.thumbnail",
        compute="_compute_main_thumbs",
        store=True,
        readonly=False,
    )
    thumb_small_id = fields.Many2one(
        comodel_name="storage.thumbnail",
        compute="_compute_main_thumbs",
        store=True,
        readonly=False,
    )
    image_medium_url = fields.Char(
        string="Medium thumb URL",
        compute="_compute_thumb_urls",
    )
    image_small_url = fields.Char(
        string="Small thumb URL",
        compute="_compute_thumb_urls",
    )

    _image_scale_mapping = {
        "medium": (128, 128),
        "small": (64, 64),
    }

    @api.depends("thumbnail_ids.size_x", "thumbnail_ids.size_y")
    def _compute_main_thumbs(self):
        for rec in self:
            for scale in self._image_scale_mapping.keys():
                fname = "thumb_%s_id" % scale
                rec[fname] = rec._get_thumb(scale_key=scale)

    @api.depends(
        "thumb_medium_id", "thumb_small_id", "backend_id.backend_view_use_internal_url"
    )
    def _compute_thumb_urls(self):
        for backend, records in tools.groupby(self, lambda x: x.backend_id):
            url_fname = "url"
            if backend.backend_view_use_internal_url:
                url_fname = "internal_url"
            for rec in records:
                rec.image_medium_url = rec.thumb_medium_id[url_fname]
                rec.image_small_url = rec.thumb_small_id[url_fname]

    def _get_thumb(self, scale_key=None, scale=None):
        """Retrievet the first thumb matching given scale."""
        assert scale_key or scale
        scale = scale or self._image_scale_mapping[scale_key]
        size_x, size_y = scale
        for thumb in self.thumbnail_ids:
            if thumb.size_x == size_x and thumb.size_y == size_y:
                return thumb

    def _get_medium_thumbnail(self):
        return self.get_or_create_thumbnail(*self._image_scale_mapping["medium"])

    def _get_small_thumbnail(self):
        return self.get_or_create_thumbnail(*self._image_scale_mapping["small"])

    def _get_url_key(self, url_key):
        if url_key:
            url_key = slugify(url_key)
        return url_key

    def get_or_create_thumbnail(self, size_x, size_y, url_key=None):
        self.ensure_one()
        url_key = self._get_url_key(url_key)
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
        self_sudo._get_small_thumbnail()
        self_sudo._get_medium_thumbnail()
        return True

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.generate_odoo_thumbnail()
        return record
