# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from pathlib import Path

import fsspec.asyn

from odoo import api, fields, models

from odoo.addons.fs_attachment.models.ir_attachment import IrAttachment


class FsStorage(models.Model):

    _inherit = "fs.storage"

    s3_uses_signed_url_for_x_accel_redirect = fields.Boolean(
        string="Use signed URL for X-Accel-Redirect",
        help="If checked, the storage will use signed URLs for attachments "
        "when using X-Accel-Redirect. This is useful for S3 storage where the "
        "file path is not directly accessible without authentication.",
    )
    s3_signed_url_expiration = fields.Integer(
        string="Signed URL Expiration (seconds)",
        default=60,
        help="The expiration time for the signed URL in seconds. "
        "Default is 60 seconds.",
    )

    @property
    def _server_env_fields(self):
        """Override to include S3 specific fields."""
        fields = super()._server_env_fields
        fields.update(
            {
                "s3_uses_signed_url_for_x_accel_redirect": {},
                "s3_signed_url_expiration": {},
            }
        )
        return fields

    @api.model
    def _get_x_accel_redirect_path(self, attachment: IrAttachment):
        """Get the path to use for X-Accel-Redirect

        The path always starts with the storage code as prefix and then the
        path to use to access the file in the storage.
        The use of the storage code as prefix is to ensure that you can
        define an internal location into your reverse proxy
        (nginx, apache, etc.) to serve the file.
        """
        path = super()._get_x_accel_redirect_path(attachment)
        fs, storage_code, file_path = attachment._get_fs_parts()
        root_fs = self.env["fs.storage"]._get_root_filesystem(fs)
        fs_storage = self.sudo().get_by_code(storage_code)
        if fs_storage.s3_uses_signed_url_for_x_accel_redirect and hasattr(
            root_fs, "s3"
        ):
            # for s3 storage, we use a signed URL
            s3_client = root_fs.s3
            url = self._s3_call_generate_presigned_url(
                s3_client,
                "get_object",
                Params={"Bucket": fs_storage.directory_path, "Key": file_path},
                ExpiresIn=fs_storage.s3_signed_url_expiration,
            )
            # exclude the endpoint_url from the path
            endpoint_url = s3_client.meta.endpoint_url
            url_path = url.replace(endpoint_url, "").lstrip("/")
            path = Path("/") / storage_code / url_path
        return str(path)

    def _s3_call_generate_presigned_url(self, s3_client, *args, **kwargs):
        """Generate a presigned URL for S3 operations."""
        # s3fs uses aiobotocore as s3 client, which is asynchronous.
        # We need to run the async function in a synchronous context.
        return fsspec.asyn.sync(
            fsspec.asyn.get_loop(),
            s3_client.generate_presigned_url,
            *args,
            timeout=None,
            **kwargs
        )
