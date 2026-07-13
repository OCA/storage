# Copyright 2025 ACSONE SA/NV
# Copyright 2025 XCG SAS
# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import datetime
from urllib.parse import urlparse

from adlfs.spec import BlobSasPermissions, generate_blob_sas

from odoo import models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _get_x_sendfile_path(self):
        self.ensure_one()
        storage = self.fs_storage_id
        if storage.is_azure_storage:
            return self._get_azure_x_sendfile_path()
        return super()._get_x_sendfile_path()

    def _fs_use_x_sendfile(self):
        self.ensure_one()
        storage = self.fs_storage_id
        if storage.is_azure_storage:
            return storage.use_x_sendfile_to_serve_internal_url
        return super()._fs_use_x_sendfile()

    def _get_azure_x_sendfile_path(self):
        """Generate the X-Accel-Redirect path for Azure storage.

        This method is used to generate the path for Azure storage when using
        X-Accel-Redirect. It constructs the path based on the Azure container and
        file path, ensuring that it is compatible with the Azure storage
        configuration and the Odoo file storage system.

        Args:
            attachment (IrAttachment): The attachment record for which the
                X-Accel-Redirect path is being generated.
        Returns:
            str: The X-Accel-Redirect path for the Azure storage.

        The path is formatted as:
            /fs_x_sendfile/<scheme>/<netloc>/<path>

        where:
        - `<scheme>` is the scheme of the base URL (e.g., 'https').
        - `<netloc>` is the netloc of the base URL
            (e.g., 'myaccount.blob.core.windows.net').
        - `<path>` is the path to the file in the Azure container, including the
          container name
        """
        fs, storage_code, file_path = self._get_fs_parts()
        storage = self.env["fs.storage"].sudo().get_by_code(storage_code)
        root_fs = storage._get_root_filesystem(fs)
        azure_client = root_fs.service_client
        container_name = storage.get_directory_path()
        blob_client = azure_client.get_blob_client(container_name, file_path)
        if storage.azure_uses_signed_url_for_x_sendfile:
            if (
                azure_client.connection_string
                or azure_client.account_name
                and azure_client.account_key
            ):
                file_url = azure_client.url(
                    file_path, expires=storage.azure_signed_url_expiration
                )
            else:
                # Ideally we would be able to call azure_client.url() as it is calling
                #  generate_blob_sas. However, it expects to use an account shared key
                #  (i.e either a connection string or account name/key pair).
                # For this we need to get a delegation key first
                now = datetime.datetime.now()
                expiry_time = now + datetime.timedelta(
                    seconds=storage.azure_signed_url_expiration
                )
                delegation_key = storage._azure_call_synchronous(
                    azure_client.get_user_delegation_key,
                    key_start_time=now,
                    key_expiry_time=expiry_time,
                )
                # Then we can call generate_blob_sas
                sas_token = storage._azure_call_synchronous(
                    generate_blob_sas,
                    fs.fs.account_name,
                    fs.path,
                    file_path,
                    user_delegation_key=delegation_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=expiry_time,
                )
                file_url = f"{blob_client.url}?{sas_token}"
        else:
            file_url = blob_client.url

        parsed_url = urlparse(file_url)
        path = parsed_url.path.strip("/")
        query = parsed_url.query
        redirect_path = f"/fs_x_sendfile/{parsed_url.scheme}/{parsed_url.netloc}/{path}"
        if query:
            redirect_path += f"?{query}"
        return redirect_path
