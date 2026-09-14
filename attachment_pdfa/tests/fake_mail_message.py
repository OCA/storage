# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class FakeMailMessage(models.Model):
    _name = "mail.message"
    _description = "Fake Mail Message for PDF/A Tests"

    model = fields.Char()
    res_id = fields.Integer()
