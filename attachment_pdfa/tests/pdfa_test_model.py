# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class PdfaTestModel(models.Model):
    _name = "pdfa.test.model"
    _description = "PDF/A Test Model"
    _inherit = ["attachment.pdfa.mixin"]

    must_convert = fields.Boolean(default=True)

    def _attachment_must_be_pdfa(self, attachment):
        return self.must_convert
