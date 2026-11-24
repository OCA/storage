# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class ImageTag(models.Model):
    _name = "image.tag"
    _inherit = ["image.tag", "server.env.mixin"]

    # `tech_name` is provided by `storage_image_product`
    _server_env_section_name_field = "tech_name"
