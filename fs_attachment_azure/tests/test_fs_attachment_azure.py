# Copyright 2025 ACSONE SA/NV (http://acsone.eu).
# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import datetime
import time
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qsl

from adlfs import AzureBlobFileSystem
from azure.storage.blob import UserDelegationKey

from odoo.exceptions import ValidationError

from odoo.addons.fs_attachment_azure import tools
from odoo.addons.fs_attachment_azure.models.fs_storage import (
    AZURE_CLOCK_SKEW_TOLERANCE,
    AZURE_MAX_DELEGATION_KEY_EXPIRATION,
)

from .common import TestFSAttachmentAzureCommon

PROTOCOL = "https"
ACCOUNT_NAME = "myaccount"
ACCOUNT_KEY = "123456789"
DOMAIN = "blob.core.windows.net"
CONTAINER = "test-blob"
PATH = "dir/sub"
FILENAME = "fake_azure_file.txt"
ACCOUNT_URL = f"{PROTOCOL}://{ACCOUNT_NAME}.{DOMAIN}"
FILE_PATH = f"{PATH}/{FILENAME}"
BASE_URL = f"{ACCOUNT_URL}/{CONTAINER}/{FILE_PATH}"
REDIRECT_PATH = (
    f"/fs_x_sendfile/{PROTOCOL}/{ACCOUNT_NAME}.{DOMAIN}/{CONTAINER}/{FILE_PATH}"
)
TOKEN = "1111-2222-3333-4444"
CONNECTION_STRING = f"DefaultEndpointsProtocol={PROTOCOL};AccountName={ACCOUNT_NAME};AccountKey={ACCOUNT_KEY};BlobEndpoint={PROTOCOL}://{DOMAIN}/{ACCOUNT_NAME};"
DELEGATION_KEY_OID = "00000000-0000-0000-0000-000000000001"


def _fake_delegation_key():
    key = UserDelegationKey()
    key.signed_oid = DELEGATION_KEY_OID
    key.signed_tid = "00000000-0000-0000-0000-000000000002"
    key.signed_start = "2026-01-01T00:00:00Z"
    key.signed_expiry = "2026-01-02T00:00:00Z"
    key.signed_service = "b"
    key.signed_version = "2023-11-03"
    # The value is used as an HMAC key, so it must be base64 decodable.
    key.value = base64.b64encode(b"delegation-key-secret").decode()
    return key


def _install_service_client(fs):
    mock_blob_client = MagicMock()
    mock_blob_client.url = BASE_URL
    mock_blob_client.account_name = ACCOUNT_NAME
    mock_service_client = MagicMock()
    mock_service_client.url = ACCOUNT_URL
    mock_service_client.get_container_client.return_value = MagicMock()
    mock_service_client.get_blob_client.return_value = mock_blob_client
    mock_service_client.close = AsyncMock(return_value="ok")
    mock_service_client.get_user_delegation_key = AsyncMock(
        return_value=_fake_delegation_key()
    )
    fs.service_client = mock_service_client


def _fake_do_connect_shared_key(self):
    """Connect with an account shared key: adlfs can sign URLs by itself."""
    self.connection_string = CONNECTION_STRING
    _install_service_client(self)


def _fake_do_connect_identity(self):
    """Connect with an identity: signing requires a user delegation key."""
    # Reset whatever the environment variables may have provided, so that the
    # tests do not depend on the host configuration.
    self.connection_string = None
    self.account_name = None
    self.account_key = None
    _install_service_client(self)


class TestFSAttachementAzure(TestFSAttachmentAzureCommon):
    def setUp(self):
        super().setUp()
        # The filesystem instances and the delegation keys are cached process
        # wide: reset them so that each test connects with its own mock and
        # doesn't leak into the next one.
        self._clear_caches()
        self.addCleanup(self._clear_caches)

    def _clear_caches(self):
        # The delegation keys live in the registry cache, the filesystem
        # instances in the fsspec one.
        self.env.registry.clear_cache()
        AzureBlobFileSystem.clear_instance_cache()

    @contextmanager
    def _time_advanced_by(self, seconds):
        """Run the block as if ``seconds`` had passed, for the caches.

        Only the clock the cache reads is moved: patching time.monotonic
        itself would also move the one the asyncio event loop runs on.
        """
        later = time.monotonic() + seconds
        with patch.object(tools, "time", SimpleNamespace(monotonic=lambda: later)):
            yield

    def _get_service_client(self):
        """Return the mocked service client used by the storage.

        Must be called while ``do_connect`` is still patched.
        """
        fs_storage = self.env["fs.storage"]
        fs = fs_storage.get_fs_by_code(self.azure_backend.code)
        return fs_storage._get_root_filesystem(fs).service_client

    def _enable_signed_url(self, expiration=60, **vals):
        self.azure_backend.write(
            {
                "azure_uses_signed_url_for_x_sendfile": True,
                "azure_signed_url_expiration": expiration,
                **vals,
            }
        )

    def test_get_x_sendfile_path_azure(self):
        """Test the X-Accel-Redirect path generation."""
        with patch.object(AzureBlobFileSystem, "do_connect", _fake_do_connect_identity):
            url = self.fake_attachment_azure._get_x_sendfile_path()
            service_client = self._get_service_client()

        self.assertEqual(
            url,
            REDIRECT_PATH,
            f"The X-Accel-Redirect path should match the expected format. ({url})",
        )
        service_client.get_user_delegation_key.assert_not_awaited()

    def test_get_x_sendfile_path_azure_signed_shared_key(self):
        """With a shared key, the URL is signed by adlfs itself."""
        self._enable_signed_url()
        with patch.object(
            AzureBlobFileSystem, "do_connect", _fake_do_connect_shared_key
        ), patch.object(
            AzureBlobFileSystem, "url", return_value=f"{BASE_URL}?{TOKEN}"
        ) as mock_url:
            url = self.fake_attachment_azure._get_x_sendfile_path()
            service_client = self._get_service_client()

        mock_url.assert_called_once_with(f"{CONTAINER}/{FILE_PATH}", expires=60)
        self.assertEqual(url, f"{REDIRECT_PATH}?{TOKEN}")
        # No delegation key is needed to sign with a shared key.
        service_client.get_user_delegation_key.assert_not_awaited()

    def test_get_x_sendfile_path_azure_signed_delegation_key(self):
        """Without a shared key, the URL is signed with a delegation key."""
        self._enable_signed_url()
        before = datetime.datetime.now(datetime.timezone.utc)
        with patch.object(AzureBlobFileSystem, "do_connect", _fake_do_connect_identity):
            url = self.fake_attachment_azure._get_x_sendfile_path()
            service_client = self._get_service_client()

        path, _sep, query = url.partition("?")
        self.assertEqual(path, REDIRECT_PATH)
        params = dict(parse_qsl(query))
        self.assertEqual(
            params.get("skoid"),
            DELEGATION_KEY_OID,
            f"The signature should be built from the delegation key. ({url})",
        )
        self.assertIn("sig", params)
        self.assertIn("se", params)
        self.assertNotIn(
            "st",
            params,
            "The signature should not have a start time, so that it is valid "
            f"as soon as Azure receives it. ({url})",
        )

        key_args = service_client.get_user_delegation_key.await_args.kwargs
        self.assertLess(
            key_args["key_start_time"],
            before,
            "The delegation key start time should be backdated to tolerate "
            "clock skew.",
        )
        self.assertEqual(
            key_args["key_expiry_time"] - key_args["key_start_time"],
            datetime.timedelta(
                seconds=self.azure_backend.azure_delegation_key_expiration
                + self.azure_backend.azure_signed_url_expiration
                + 2 * AZURE_CLOCK_SKEW_TOLERANCE
            ),
            "The key must cover the whole time it is cached, plus the "
            "signatures generated by the last call served from the cache.",
        )

    def test_delegation_key_is_cached(self):
        """The delegation key is fetched once and reused."""
        self._enable_signed_url()
        with patch.object(AzureBlobFileSystem, "do_connect", _fake_do_connect_identity):
            urls = [
                self.fake_attachment_azure._get_x_sendfile_path() for _i in range(3)
            ]
            service_client = self._get_service_client()

        self.assertEqual(service_client.get_user_delegation_key.await_count, 1)
        for url in urls:
            self.assertIn("skoid", url)

    def test_delegation_key_refreshed_once_expired(self):
        """The key is fetched again by the first call made after it expired."""
        self._enable_signed_url()
        with patch.object(AzureBlobFileSystem, "do_connect", _fake_do_connect_identity):
            self.fake_attachment_azure._get_x_sendfile_path()
            service_client = self._get_service_client()
            self.assertEqual(service_client.get_user_delegation_key.await_count, 1)
            # Right before the end of the caching duration, the key is reused.
            with self._time_advanced_by(
                self.azure_backend.azure_delegation_key_expiration - 1
            ):
                self.fake_attachment_azure._get_x_sendfile_path()
                self.assertEqual(service_client.get_user_delegation_key.await_count, 1)
            # Past it, a new one is requested.
            with self._time_advanced_by(
                self.azure_backend.azure_delegation_key_expiration + 1
            ):
                self.fake_attachment_azure._get_x_sendfile_path()

        self.assertEqual(service_client.get_user_delegation_key.await_count, 2)

    def test_delegation_key_dropped_when_storage_is_written(self):
        """Reconfiguring the storage drops the key cached for it.

        This is what makes a new configuration effective right away instead of
        at the end of the caching duration.
        """
        self._enable_signed_url()
        with patch.object(AzureBlobFileSystem, "do_connect", _fake_do_connect_identity):
            self.fake_attachment_azure._get_x_sendfile_path()
            service_client = self._get_service_client()
            self.assertEqual(service_client.get_user_delegation_key.await_count, 1)
            self.azure_backend.azure_delegation_key_expiration = 7200
            self.fake_attachment_azure._get_x_sendfile_path()

        self.assertEqual(service_client.get_user_delegation_key.await_count, 2)

    def test_delegation_key_expiration_constraint(self):
        """Azure only issues delegation keys valid for up to 7 days."""
        for expiration in (0, -1, AZURE_MAX_DELEGATION_KEY_EXPIRATION):
            with self.subTest(expiration=expiration), self.assertRaises(
                ValidationError
            ), self.env.cr.savepoint():
                self.azure_backend.azure_delegation_key_expiration = expiration
        # The signed URL expiration and the clock skew tolerance are part of
        # the lifetime the key is requested for, so they leave less room.
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.azure_backend.write(
                {
                    "azure_delegation_key_expiration": (
                        AZURE_MAX_DELEGATION_KEY_EXPIRATION - AZURE_CLOCK_SKEW_TOLERANCE
                    ),
                    "azure_signed_url_expiration": 1,
                }
            )
        # The largest configuration Azure accepts.
        self.azure_backend.write(
            {
                "azure_delegation_key_expiration": (
                    AZURE_MAX_DELEGATION_KEY_EXPIRATION
                    - AZURE_CLOCK_SKEW_TOLERANCE
                    - 30
                ),
                "azure_signed_url_expiration": 30,
            }
        )
