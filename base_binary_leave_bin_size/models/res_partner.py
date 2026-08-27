# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "avatar.mixin"]

    def _compute_avatar(self, avatar_field, image_field):
        return super(ResPartner, self.manage_bin_size())._compute_avatar(
            avatar_field, image_field
        )
