# Copyright 2021 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def render_qweb_pdf(self, res_ids=None, data=None):
        return super(
            IrActionsReport, self.with_context(print_report_pdf=True)
        ).render_qweb_pdf(res_ids=res_ids, data=data)
