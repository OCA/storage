# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MediaType(models.Model):
    _name = "storage.media.type"
    _description = "Storage Media Type"

    name = fields.Char(translate=True, required=True)
    code = fields.Char()
