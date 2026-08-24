# Copyright 2025 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import fsspec.asyn

from odoo import api, fields, models


class FsStorage(models.Model):
    _inherit = "fs.storage"

    azure_uses_signed_url_for_x_sendfile = fields.Boolean(
        string="Use signed URL for X-Accel-Redirect",
        help="If checked, the storage will use signed URLs for attachments "
        "when using X-Accel-Redirect. This is useful for Azure storage where the "
        "file path is not directly accessible without authentication.",
    )
    azure_signed_url_expiration = fields.Integer(
        string="Signed URL Expiration (seconds)",
        default=30,
        help="The expiration time for the signed URL in seconds. "
        "Default is 30 seconds.",
    )

    @property
    def _server_env_fields(self):
        """Override to include Azure specific fields."""
        fields = super()._server_env_fields
        fields.update(
            {
                "azure_uses_signed_url_for_x_sendfile": {},
                "azure_signed_url_expiration": {},
            }
        )
        return fields

    @property
    def is_azure_storage(self):
        """Check if the storage is an Azure storage."""
        self.ensure_one()
        fs = self._get_root_filesystem(self.fs)
        protocol = getattr(fs, "protocol", [])
        return self.protocol in protocol

    @api.model
    def _azure_call_synchronous(self, azure_client_function, *args, **kwargs):
        # adlfs uses asynchronous client
        # We need to run the async function in a synchronous context.
        return fsspec.asyn.sync(
            fsspec.asyn.get_loop(),
            azure_client_function,
            *args,
            timeout=None,
            **kwargs,
        )
