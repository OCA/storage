# Copyright 2025 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class S3MigrationWizard(models.TransientModel):
    _name = "s3.migration.wizard"
    _description = "Migrate existing attachments to S3"

    storage_id = fields.Many2one("fs.storage", required=True)
    storage_code = fields.Char(required=True)
    batch_size = fields.Integer(default=500)
    channel = fields.Char(default="root.s3_migration")
    max_batches = fields.Integer(
        string="Max Batches (per click)",
        help="Limit number of batches to enqueue now. Leave 0 for unlimited.",
        default=0,
    )

    @api.onchange("storage_id")
    def _onchange_storage(self):
        if self.storage_id:
            self.storage_code = self.storage_id.code
            if self.storage_id.migration_batch_size:
                self.batch_size = self.storage_id.migration_batch_size
            if self.storage_id.migration_channel:
                self.channel = self.storage_id.migration_channel

    def action_confirm(self):
        self.ensure_one()
        if not self.storage_code:
            raise UserError(_("Storage code is required."))
        max_batches = self.max_batches or None
        total = self.env["ir.attachment"].s3_enqueue_migration(
            self.storage_code,
            batch_size=self.batch_size,
            max_batches=max_batches,
            channel=self.channel,
        )
        return [
            {"type": "ir.actions.act_window_close"},
            {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Migration Enqueued"),
                    "message": _("%s attachments enqueued for migration.") % total,
                    "sticky": False,
                },
            },
        ]
