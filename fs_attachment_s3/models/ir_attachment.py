# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from urllib.parse import urlparse

from odoo import models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _storage_write_option(self, fs):
        option = super()._storage_write_option(fs)
        mimetype = self.env.context.get("mimetype")
        if mimetype:
            root_fs = self.env["fs.storage"]._get_root_filesystem(fs)
            if hasattr(root_fs, "s3"):
                option["ContentType"] = mimetype
        return option

    def _get_x_sendfile_path(self):
        self.ensure_one()
        storage = self.fs_storage_id
        if storage.is_s3_storage:
            return self._get_s3_x_sendfile_path()
        return super()._get_x_sendfile_path()

    def _fs_use_x_sendfile(self):
        self.ensure_one()
        storage = self.fs_storage_id
        if storage.is_s3_storage:
            return storage.use_x_sendfile_to_serve_internal_url
        return super()._fs_use_x_sendfile()

    def _get_s3_x_sendfile_path(self):
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
            /fs_x_sendfile/<scheme>/<netloc>/<path>

        where:
        - `<scheme>` is the scheme of the base URL (e.g., 'https').
        - `<netloc>` is the netloc of the base URL (e.g., 's3.amazonaws.com').
        - `<path>` is the path to the file in the S3 bucket, including the
          bucket name
        """
        fs, storage_code, file_path = self._get_fs_parts()
        storage = self.env["fs.storage"].sudo().get_by_code(storage_code)
        root_fs = storage._get_root_filesystem(fs)
        s3_client = root_fs.s3
        bucket_name = storage.directory_path.strip("/").rstrip("/")
        if storage.s3_uses_signed_url_for_x_sendfile:
            file_url = storage._s3_call_generate_presigned_url(
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
        redirect_path = f"/fs_x_sendfile/{parsed_url.scheme}/{parsed_url.netloc}/{path}"
        if query:
            redirect_path += f"?{query}"
        return redirect_path
