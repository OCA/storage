# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    def _storage_write_option(self, fs):
        option = super()._storage_write_option(fs)
        mimetype = self.env.context.get("mimetype")
        if mimetype:
            root_fs = self.env["fs.storage"]._get_root_filesystem(fs)
            if hasattr(root_fs, "s3"):
                option["ContentType"] = mimetype
        return option
