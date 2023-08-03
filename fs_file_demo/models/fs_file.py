# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.fs_file import fields as fs_fields


class FsFile(models.Model):

    _name = "fs.file"
    _description = "Fs File"

    name = fields.Char()
    file = fs_fields.FSFile(string="File")
