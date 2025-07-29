# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from urllib.parse import urlparse

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
                "s3_uses_signed_url_for_x_accel_redirect": {},
                "s3_signed_url_expiration": {},
            }
        )
        return fields

    @api.model
    def _get_x_accel_redirect_path(self, attachment: IrAttachment):
        redirect_path = super()._get_x_accel_redirect_path(attachment)
        fs = self.get_fs_by_code(attachment.fs_storage_code)
        root_fs = self._get_root_filesystem(fs)
        if hasattr(root_fs, "s3"):
            redirect_path = self._get_s3_x_accel_redirect_path(attachment)
        return redirect_path

    @api.model
    def _get_s3_x_accel_redirect_path(self, attachment: IrAttachment):
        """Generate the X-Accel-Redirect path for S3 storage.

        This method is used to generate the path for S3 storage when using
        X-Accel-Redirect. It constructs the path based on the S3 bucket and
        file path, ensuring that it is compatible with the S3 storage
        configuration and the Odoo file storage system.

        Args:
            attachment (IrAttachment): The attachment record for which the
                X-Accel-Redirect path is being generated.
        Returns:
            str: The X-Accel-Redirect path for the S3 storage.

        The path is formatted as:
            /fs_x_accel_redirect/<scheme>/<netloc>/<path>

        where:
        - `<scheme>` is the scheme of the base URL (e.g., 'https').
        - `<netloc>` is the netloc of the base URL (e.g., 's3.amazonaws.com').
        - `<path>` is the path to the file in the S3 bucket, including the
          bucket name
        """
        fs, storage_code, file_path = attachment._get_fs_parts()
        storage = self.sudo().get_by_code(storage_code)
        root_fs = self._get_root_filesystem(fs)
        s3_client = root_fs.s3
        bucket_name = storage.directory_path.strip("/").rstrip("/")
        if storage.s3_uses_signed_url_for_x_accel_redirect:
            file_url = self._s3_call_generate_presigned_url(
                s3_client,
                "get_object",
                Params={"Bucket": bucket_name, "Key": file_path},
                ExpiresIn=storage.s3_signed_url_expiration,
            )
        else:
            file_url = (
                f"{s3_client.meta.endpoint_url.rstrip('/')}/"
                f"{bucket_name}/{file_path.lstrip('/')}"
            )

        parsed_url = urlparse(file_url)
        path = parsed_url.path.strip("/")
        query = parsed_url.query
        redirect_path = (
            f"/fs_x_accel_redirect/{parsed_url.scheme}/{parsed_url.netloc}/{path}"
        )
        if query:
            redirect_path += f"?{query}"
        return redirect_path

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
