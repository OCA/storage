# Copyright 2026 Cetmix OU
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

    migration_use_storage_force_db_rules = fields.Boolean(
        string="Use Storage Force-DB Rules",
        default=True,
        help="If checked, respect force_db_for_default_attachment_rules during "
        "migration. Small images and assets will be skipped.",
    )

    def action_open_migration_wizard(self):
        """Open the S3 migration wizard for this storage."""
        self.ensure_one()
        if not self.code:
            raise UserError(_("Storage must have a code to run migration."))
        if self.protocol != "s3":
            raise UserError(_("Target storage must use the S3 protocol."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "s3.migration.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_storage_id": self.id,
            },
        }
