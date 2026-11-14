# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrBinary(models.AbstractModel):
    _inherit = "ir.binary"

    def _record_to_stream(self, record, field_name):
        """
        We want here to retrieve the whole image content data.

        So, put in context to let Odoo choose how to manage bin_size
        """
        return super()._record_to_stream(
            record.with_context(leave_bin_size_alone=True), field_name
        )
