# Copyright 2023 ACSONE SA/NV
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ImageTag(models.Model):
    _name = "image.tag"
    _inherit = ["server.env.techname.mixin"]
    _description = "Image Tag"

    @api.model
    def _get_default_apply_on(self):
        return False

    name = fields.Char(required=True)
    apply_on = fields.Selection(
        selection=[],
        default=lambda self: self._get_default_apply_on(),
    )
