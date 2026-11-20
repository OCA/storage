# Copyright 2023 ACSONE SA/NV
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <https://github.com/hparfr>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class ImageTag(models.Model):
    _name = "image.tag"
    _inherit = ["image.tag", "server.env.techname.mixin"]
