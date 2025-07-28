# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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

    def _get_x_accel_redirect_base_url(
        self, attachment: IrAttachment, raise_if_not_found: bool = True
    ) -> str:
        x_accel_base_url = super()._get_x_accel_redirect_base_url(
            attachment, raise_if_not_found=False
        )
        if not x_accel_base_url:
            root_fs = self._get_root_filesystem(self.fs)
            s3_client = root_fs.s3 if hasattr(root_fs, "s3") else None
            if s3_client:
                x_accel_base_url = s3_client.meta.endpoint_url
        if not x_accel_base_url:
            return super()._get_x_accel_redirect_base_url(
                attachment, raise_if_not_found=raise_if_not_found
            )
        return x_accel_base_url.rstrip("/")

    def _get_x_accel_redirect_sub_path(self, attachment: IrAttachment) -> str:
        fs, _storage_code, file_path = attachment._get_fs_parts()
        root_fs = self._get_root_filesystem(fs)
        if self.s3_uses_signed_url_for_x_accel_redirect and hasattr(root_fs, "s3"):
            # for S3 storage, we use a signed URL
            s3_client = root_fs.s3
            url = self._s3_call_generate_presigned_url(
                s3_client,
                "get_object",
                Params={"Bucket": self.directory_path, "Key": file_path},
                ExpiresIn=self.s3_signed_url_expiration,
            )
            # exclude the endpoint_url from the path
            endpoint_url = s3_client.meta.endpoint_url
            return url.replace(endpoint_url, "").lstrip("/")
        else:
            return super()._get_x_accel_redirect_sub_path(attachment)

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
            **kwargs
        )
