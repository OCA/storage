# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging

import requests
from odoo import api, fields, models
from odoo.tools import image_resize_image

_logger = logging.getLogger(__name__)


class StorageThumbnail(models.Model):
    _name = "storage.thumbnail"
    _description = "Storage Thumbnail"
    _inherits = {"storage.file": "file_id"}

    size_x = fields.Integer("weight")
    size_y = fields.Integer("height")
    url_key = fields.Char(
        "Url key", help="Specific URL key for generating the url of the image"
    )
    file_id = fields.Many2one(
        "storage.file", "File", required=True, ondelete="cascade"
    )
    res_model = fields.Char(readonly=False, index=True)
    res_id = fields.Integer(readonly=False, index=True)

    def _prepare_thumbnail(self, image, size_x, size_y, url_key):
        image_resize_format = self.env["ir.config_parameter"].get_param(
            "storage.image.resize.format"
        )
        if image_resize_format:
            extension = image_resize_format
        else:
            extension = image.extension
        return {
            "data": self._resize(image, size_x, size_y),
            "res_model": image._name,
            "res_id": image.id,
            "name": "%s_%s_%s%s"
            % (url_key or image.filename, size_x, size_y, extension),
            "size_x": size_x,
            "size_y": size_y,
            "url_key": url_key,
        }

    def _resize(self, image, size_x, size_y):
        image_server_resize = self.env["ir.config_parameter"].get_param(
            "storage.image.server.resize"
        )
        if image_server_resize and image.backend_id.served_by != "odoo":
            image_resize_format = self.env["ir.config_parameter"].get_param(
                "storage.image.resize.format"
            )
            values = {"url": image.url, "width": size_x, "height": size_y}
            if image_resize_format:
                values["format"] = image_resize_format
            url = image_server_resize % values
            request = requests.get(url)
            return request.content.encode("base64")
        return image_resize_image(image.data, size=(size_x, size_y))

    def _get_backend_id(self):
        """Choose the correct backend.

        By default : it's the one configured as ir.config_parameter
        Overload this method if you need something more powerfull
        """
        return int(
            self.env["ir.config_parameter"].get_param(
                "storage.thumbnail.backend_id"
            )
        )

    @api.model
    def create(self, vals):
        vals.update(
            {"backend_id": self._get_backend_id(), "file_type": "thumbnail"}
        )
        return super(StorageThumbnail, self).create(vals)

    def unlink(self):
        files = self.mapped("file_id")
        result = super(StorageThumbnail, self).unlink()
        files.unlink()
        return result
