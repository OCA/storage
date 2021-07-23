# Copyright 2021 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class FakeProductImageRelation(models.Model):
    _inherit = ["product.image.relation"]
