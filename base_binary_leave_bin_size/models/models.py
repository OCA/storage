# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.private
    def manage_bin_size(self):
        if self.env.context.get("leave_bin_size_alone"):
            bin_size = self.env.context.get("bin_size")
        else:
            # Force bin_size so we don't do a slow fetch of the image from S3
            # just to compute the image size.
            bin_size = True
        return self.with_context(bin_size=bin_size)
