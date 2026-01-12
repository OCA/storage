# Copyright 2025 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

MIGRATION_CHANNEL_XMLID = "fs_attachment_s3_migration.queue_channel_s3_migration"


class S3MigrationWizard(models.TransientModel):
    _name = "s3.migration.wizard"
    _description = "Migrate existing attachments to S3"

    storage_id = fields.Many2one(
        "fs.storage",
        string="Target Storage",
        required=True,
    )
    storage_code = fields.Char(
        compute="_compute_storage_code",
        store=True,
        readonly=False,
        required=True,
    )
    batch_size = fields.Integer(
        compute="_compute_batch_size",
        store=True,
        readonly=False,
    )
    channel = fields.Char(
        string="Queue Channel",
        compute="_compute_channel",
        store=True,
        readonly=False,
    )
    max_batches = fields.Integer(
        string="Max Batches (per click)",
        help="Limit number of batches to enqueue now. Leave 0 for unlimited.",
        default=0,
    )

    @api.model
    def _get_default_channel(self):
        """Get default channel name from XML record."""
        channel = self.env.ref(MIGRATION_CHANNEL_XMLID, raise_if_not_found=False)
        return channel.complete_name if channel else "root.s3_migration"

    @api.depends("storage_id")
    def _compute_storage_code(self):
        for wizard in self:
            wizard.storage_code = wizard.storage_id.code if wizard.storage_id else False

    @api.depends("storage_id")
    def _compute_batch_size(self):
        for wizard in self:
            if wizard.storage_id and wizard.storage_id.migration_batch_size:
                wizard.batch_size = wizard.storage_id.migration_batch_size
            elif not wizard.batch_size:
                wizard.batch_size = 500

    @api.depends("storage_id")
    def _compute_channel(self):
        for wizard in self:
            if wizard.storage_id and wizard.storage_id.migration_channel:
                wizard.channel = wizard.storage_id.migration_channel
            elif not wizard.channel:
                wizard.channel = wizard._get_default_channel()

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
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Migration Enqueued"),
                "message": _(
                    "%(count)s attachments enqueued for migration.",
                    count=total,
                ),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
