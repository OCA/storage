# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AvatarMixin(models.AbstractModel):
    _inherit = "avatar.mixin"

    avatar_128 = fields.Image(store=True)
