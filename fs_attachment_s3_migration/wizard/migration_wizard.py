# Copyright 2026 Cetmix OU
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

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
    )
    batch_size = fields.Integer(
        compute="_compute_batch_size",
        store=True,
        readonly=False,
    )
    channel_id = fields.Many2one(
        "queue.job.channel",
        string="Queue Channel",
        compute="_compute_channel_id",
        store=True,
        readonly=False,
        default=lambda self: self._get_default_channel_id(),
    )
    max_batches = fields.Integer(
        string="Max Batches (per click)",
        help="Limit number of batches to enqueue now. Leave 0 for unlimited.",
        default=0,
    )

    @api.model
    def _get_default_channel_id(self):
        """Return the XML-defined migration channel id, if present."""
        return self.env["ir.model.data"]._xmlid_to_res_id(
            MIGRATION_CHANNEL_XMLID, raise_if_not_found=False
        )

    @api.depends("storage_id", "storage_id.code")
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

    @api.depends("storage_id", "storage_id.migration_channel")
    def _compute_channel_id(self):
        default_id = self._get_default_channel_id()
        Channel = self.env["queue.job.channel"].sudo()
        for wizard in self:
            channel = Channel.browse()
            complete_name = (
                wizard.storage_id.migration_channel if wizard.storage_id else False
            )
            if complete_name:
                channel = Channel.search(
                    [("complete_name", "=", complete_name)], limit=1
                )
            wizard.channel_id = channel.id or default_id

    @api.constrains("batch_size")
    def _check_batch_size(self):
        for wizard in self:
            if wizard.batch_size <= 0:
                raise ValidationError(_("Batch size must be greater than 0."))

    @api.constrains("max_batches")
    def _check_max_batches(self):
        for wizard in self:
            if wizard.max_batches < 0:
                raise ValidationError(_("Max batches cannot be negative."))

    def action_confirm(self):
        self.ensure_one()
        if not self.storage_id:
            raise UserError(_("Storage is required."))
        if self.storage_id.protocol != "s3":
            raise UserError(_("Target storage must use the S3 protocol."))
        if not self.channel_id or not self.channel_id.complete_name:
            raise UserError(_("Queue channel is required."))
        max_batches = self.max_batches or None
        total = self.env["ir.attachment"]._s3_enqueue_migration(
            self.storage_id.code,
            batch_size=self.batch_size,
            max_batches=max_batches,
            channel=self.channel_id.complete_name,
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
