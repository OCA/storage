# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

import requests

from odoo import api, fields, models
from odoo.tools import ImageProcess

_logger = logging.getLogger(__name__)


class StorageThumbnail(models.Model):
    _name = "storage.thumbnail"
    _description = "Storage Thumbnail"
    _inherits = {"storage.file": "file_id"}
    _default_file_type = "thumbnail"

    size_x = fields.Integer("weight")
    size_y = fields.Integer("height")
    url_key = fields.Char(
        "Url key", help="Specific URL key for generating the url of the image"
    )
    file_id = fields.Many2one("storage.file", "File", required=True, ondelete="cascade")
    res_model = fields.Char(readonly=False, index=True)
    res_id = fields.Integer(readonly=False, index=True)

    def _prepare_thumbnail(self, image, size_x, size_y, url_key):
        image_resize_format = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("storage.image.resize.format")
        )
        if image_resize_format:
            extension = image_resize_format
        else:
            extension = image.extension
        return {
            "data": self._resize(image, size_x, size_y, extension),
            "res_model": image._name,
            "res_id": image.id,
            "name": "%s_%s_%s%s"
            % (url_key or image.filename, size_x, size_y, extension),
            "size_x": size_x,
            "size_y": size_y,
            "url_key": url_key,
        }

    def _resize(self, image, size_x, size_y, fmt):
        image_resize_server = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("storage.image.resize.server")
        )
        if image_resize_server and image.backend_id.served_by != "odoo":
            values = {"url": image.url, "width": size_x, "height": size_y, "fmt": fmt}
            url = image_resize_server.format(**values)
            return base64.encodebytes(requests.get(url).content)
        image_process = ImageProcess(image.data)
        return image_process.resize(max_width=size_x, max_height=size_y).image_base64()

    def _get_default_backend_id(self):
        """Choose the correct backend.

        By default : it's the one configured as ir.config_parameter
        Overload this method if you need something more powerfull
        """
        return self.env["storage.backend"]._get_backend_id_from_param(
            self.env, "storage.thumbnail.backend_id"
        )

    @api.model
    def create(self, vals):
        vals["file_type"] = self._default_file_type
        if "backend_id" not in vals:
            vals["backend_id"] = self._get_default_backend_id()
        return super().create(vals)

    def unlink(self):
        files = self.mapped("file_id")
        result = super().unlink()
        files.unlink()
        return result
