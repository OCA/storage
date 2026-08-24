# Copyright 2025 ACSONE SA/NV (http://acsone.eu).
# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from adlfs import AzureBlobFileSystem

from .common import TestFSAttachmentAzureCommon

PROTOCOL = "https"
ACCOUNT_NAME = "myaccount"
ACCOUNT_KEY = "123456789"
DOMAIN = "blob.core.windows.net"
CONTAINER = "test-blob"
PATH = "dir/sub"
FILENAME = "fake_azure_file.txt"
BASE_URL = f"{PROTOCOL}://{ACCOUNT_NAME}.{DOMAIN}/{CONTAINER}/{PATH}/{FILENAME}"
TOKEN = "1111-2222-3333-4444"
CONNECTION_STRING = f"DefaultEndpointsProtocol={PROTOCOL};AccountName={ACCOUNT_NAME};AccountKey={ACCOUNT_KEY};BlobEndpoint={PROTOCOL}://{DOMAIN}/{ACCOUNT_NAME};"


def _fake_do_connect(self):
    mock_service_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_blob_client.url = BASE_URL
    mock_service_client.get_container_client.return_value = Mock()
    mock_service_client.get_blob_client.return_value = mock_blob_client
    mock_service_client.connection_string = CONNECTION_STRING
    mock_service_client.url.return_value = "?".join([BASE_URL, TOKEN])
    mock_service_client.close = AsyncMock(return_value="ok")
    self.service_client = mock_service_client


class TestFSAttachementAzure(TestFSAttachmentAzureCommon):
    def test_get_x_sendfile_path_azure_signed(self):
        """Test the X-Accel-Redirect path generation for azure storage."""
        self.azure_backend.write(
            {
                "azure_uses_signed_url_for_x_sendfile": True,
                "azure_signed_url_expiration": 60,
            }
        )
        with patch.object(AzureBlobFileSystem, "do_connect", _fake_do_connect):
            url = self.fake_attachment_azure._get_x_sendfile_path()
        self.assertTrue(
            url.startswith(
                "/fs_x_sendfile/https/myaccount.blob.core.windows.net/test-blob/dir/sub/fake_azure_file.txt?1111-2222-3333-4444"
            ),
            "The end of the path should contain the path to the file "
            f"name and query parameters. ({url})",
        )

    def test_get_x_sendfile_path_azure(self):
        """Test the X-Accel-Redirect path generation."""
        with patch.object(AzureBlobFileSystem, "do_connect", _fake_do_connect):
            url = self.fake_attachment_azure._get_x_sendfile_path()

        self.assertEqual(
            url,
            "/fs_x_sendfile/https/myaccount.blob.core.windows.net/test-blob/dir/sub/fake_azure_file.txt",
            f"The X-Accel-Redirect path should match the expected format. ({url})",
        )
