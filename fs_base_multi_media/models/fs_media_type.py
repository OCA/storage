# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class FsMediaType(models.Model):
    _name = "fs.media.type"
    _description = "Media Type"

    name = fields.Char(translate=True, required=True)
    code = fields.Char()
