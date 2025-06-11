# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Py3oReport(models.TransientModel):
    _inherit = "py3o.report"

    def _postprocess_report(self, model_instance, result_path):
        self_with_context = self
        if len(model_instance) == 1 and self.ir_actions_report_id:
            self_with_context = self.with_context(
                report_id=self.ir_actions_report_id.id
            )
        return super(Py3oReport, self_with_context)._postprocess_report(
            model_instance, result_path
        )
