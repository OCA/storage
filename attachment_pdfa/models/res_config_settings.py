# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    attachment_pdfa_method = fields.Selection(
        selection=[
            ("ghostscript", "Ghostscript"),
            ("odoo", "Odoo"),
            ("disable", "Disable"),
        ],
        string="PDF to PDF/A Conversion Method",
        config_parameter="attachment_pdfa.method",
        default="ghostscript",
        help="Choose the underlying engine to convert PDF to PDF/A.",
    )
    attachment_pdfa_mode = fields.Selection(
        selection=[
            ("replace", "Replace Original File"),
            ("beside", "Store Beside Original File"),
        ],
        string="PDF/A Storage Strategy",
        config_parameter="attachment_pdfa.mode",
        default="replace",
        help="Choose whether to replace the original PDF attachment or create a new "
        "attachment beside it.",
    )
