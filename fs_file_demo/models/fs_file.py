# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.fs_file import fields as fs_fields
from odoo.addons.fs_image import fields as fs_image_fields


class FsFile(models.Model):

    _name = "fs.file"
    _description = "Fs File"

    name = fields.Char()
    file = fs_fields.FSFile(string="File")

    fs_image_1920 = fs_image_fields.FSImage(
        string="Image", max_width=1920, max_height=1920
    )
    fs_image_128 = fs_image_fields.FSImage(
        string="Image",
        max_width=128,
        max_height=128,
        related="fs_image_1920",
        store=True,
    )
