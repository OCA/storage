# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import fsspec.asyn

from odoo import api, fields, models


class FsStorage(models.Model):
    _inherit = "fs.storage"

    s3_uses_signed_url_for_x_sendfile = fields.Boolean(
        string="Use signed URL for X-Accel-Redirect",
        help="If checked, the storage will use signed URLs for attachments "
        "when using X-Accel-Redirect. This is useful for S3 storage where the "
        "file path is not directly accessible without authentication.",
    )
    s3_signed_url_expiration = fields.Integer(
        string="Signed URL Expiration (seconds)",
        default=30,
        help="The expiration time for the signed URL in seconds. "
        "Default is 30 seconds.",
    )

    @property
    def _server_env_fields(self):
        """Override to include S3 specific fields."""
        fields = super()._server_env_fields
        fields.update(
            {
                "s3_uses_signed_url_for_x_sendfile": {},
                "s3_signed_url_expiration": {},
            }
        )
        return fields

    @property
    def is_s3_storage(self):
        """Check if the storage is an S3 storage."""
        self.ensure_one()
        return hasattr(self._get_root_filesystem(self.fs), "s3")

    @api.model
    def _s3_call_generate_presigned_url(self, s3_client, *args, **kwargs):
        """Generate a presigned URL for S3 operations."""
        # s3fs uses aiobotocore as s3 client, which is asynchronous.
        # We need to run the async function in a synchronous context.
        return fsspec.asyn.sync(
            fsspec.asyn.get_loop(),
            s3_client.generate_presigned_url,
            *args,
            timeout=None,
            **kwargs,
        )
