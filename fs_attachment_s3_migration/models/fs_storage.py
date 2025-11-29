# Copyright 2025 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class FsStorage(models.Model):
    _inherit = "fs.storage"

    migration_batch_size = fields.Integer(
        default=500,
        help="Number of attachments per background job batch.",
    )

    migration_channel = fields.Char(
        string="Queue Channel",
        default="root.s3_migration",
        help="queue_job channel to use for migration jobs.",
    )

    def action_open_migration_wizard(self):
        """Open the S3 migration wizard for this storage."""
        self.ensure_one()
        if not self.code:
            raise UserError(_("Storage must have a code to run migration."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "s3.migration.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_storage_id": self.id,
                "default_storage_code": self.code,
                "default_batch_size": self.migration_batch_size,
                "default_channel": self.migration_channel,
            },
        }
