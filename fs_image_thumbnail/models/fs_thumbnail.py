# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class FsThumbnail(models.Model):

    _name = "fs.thumbnail"
    _inherit = "fs.image.thumbnail.mixin"
    _description = "Image Thumbnail"
