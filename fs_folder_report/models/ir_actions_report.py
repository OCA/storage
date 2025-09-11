# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, time


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    save_in_fs_folder = fields.Boolean(
        string="Store in Folder Structure",
        help="If checked, the report will be saved in the folder linked to the record.",
        default=False,
    )
    is_save_in_fs_folder_possible = fields.Boolean(
        string="Is Save in Folder Possible",
        compute="_compute_is_save_in_fs_folder_possible",
        help="If checked, the report can be saved in a fs folder declared on "
        "the record.",
    )
    fs_folder_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Folder Field",
        help="The folder field to use when saving the report in a folder.",
    )
    fs_folder_path = fields.Char(
        string="Folder Path",
        help="The path where the report will be saved in the folder."
        "You can use a python expression with the object and time variables.",
    )

    def _get_fs_folder_path(self, record):
        """Return the name of the folder field."""
        self.ensure_one()
        eval_ctx = self._get_fs_folder_path_eval_context(record)
        return safe_eval(self.fs_folder_path, eval_ctx) if self.fs_folder_path else ""

    def _get_fs_folder_path_eval_context(self, record):
        """Return the context to use for evaluating the fs_folder_path."""
        return {
            "object": record,
            "time": time,
        }

    @api.depends("model")
    def _compute_is_save_in_fs_folder_possible(self):
        """Check if the model has a folder defined."""
        for record in self:
            record.is_save_in_fs_folder_possible = False
            model = self.env[record.model]
            for field in model._fields.values():
                if field.type == "fs_folder":
                    record.is_save_in_fs_folder_possible = True
                    break

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        self_with_context = self.with_context(report_id=report.id)
        return super(IrActionsReport, self_with_context)._render_qweb_pdf(
            report_ref, res_ids=res_ids, data=data
        )

    @api.constrains("save_in_fs_folder", "fs_folder_field_id")
    def _check_fs_folder_field(self):
        """Ensure that the fs_folder_field_id is set when save_in_fs_folder is True."""
        for record in self:
            if record.save_in_fs_folder and not record.fs_folder_field_id:
                raise ValidationError(
                    self.env._(
                        "The 'Folder Field' must be set when 'Store in Folder "
                        "Structure' is set."
                    )
                )
