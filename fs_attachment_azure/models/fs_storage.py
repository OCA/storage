# Copyright 2025 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

import fsspec.asyn

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..tools import ormcache_expiring

# Start times are backdated by this many seconds, to tolerate clock skew
# between this host and Azure.
AZURE_CLOCK_SKEW_TOLERANCE = 300

# Azure refuses to issue a user delegation key valid for more than 7 days.
AZURE_MAX_DELEGATION_KEY_EXPIRATION = 7 * 24 * 3600

# Azure accepts at most 256 subrequests in a single blob batch request.
AZURE_MAX_BLOBS_PER_BATCH = 256


async def _azure_delete_blobs_batch(service_client, container_name, blob_names):
    """Delete blobs in one batch request, returning a status code per blob.

    The container client is used as a context manager, the same way adlfs
    does when it needs a blob client.
    """
    async with service_client.get_container_client(container_name) as container_client:
        responses = await container_client.delete_blobs(
            *blob_names,
            # A single blob that cannot be deleted must not discard the whole
            # batch: the status of each subrequest is inspected instead.
            raise_on_any_failure=False,
        )
        return [response.status_code async for response in responses]


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
    azure_delegation_key_expiration = fields.Integer(
        string="Delegation Key Expiration (seconds)",
        default=3600,
        help="How long the user delegation key used to sign URLs is cached, when "
        "the storage authenticates with an identity instead of a shared key. A "
        "higher value means fewer calls to Azure, but a longer window during "
        "which the key of a revoked identity remains usable. Azure does not "
        "issue keys valid for more than 7 days, which this and the signed URL "
        "expiration must leave room for.",
    )

    @api.constrains("azure_delegation_key_expiration", "azure_signed_url_expiration")
    def _check_azure_delegation_key_expiration(self):
        for rec in self:
            if rec.azure_delegation_key_expiration <= 0:
                raise ValidationError(
                    _("The delegation key expiration must be at least 1 second.")
                )
            # See _azure_get_user_delegation_key for the lifetime the key is
            # requested for.
            requested = (
                rec.azure_delegation_key_expiration
                + rec.azure_signed_url_expiration
                + AZURE_CLOCK_SKEW_TOLERANCE
            )
            if requested > AZURE_MAX_DELEGATION_KEY_EXPIRATION:
                raise ValidationError(
                    _(
                        "Azure does not issue delegation keys valid for more than "
                        "7 days. The delegation key expiration, the signed URL "
                        "expiration and a %(skew)s seconds clock skew tolerance "
                        "must not add up to more than %(max)s seconds.",
                        skew=AZURE_CLOCK_SKEW_TOLERANCE,
                        max=AZURE_MAX_DELEGATION_KEY_EXPIRATION,
                    )
                )

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

    @ormcache_expiring(
        "self.id",
        "service_client.url",
        expiration="self.azure_delegation_key_expiration",
    )
    def _azure_get_user_delegation_key(self, service_client):
        """Return a user delegation key to sign URLs for this storage.

        The key is cached for ``azure_delegation_key_expiration`` seconds and
        shared by all the attachments of the storage. It is requested for a
        bit longer than that, so that it still covers the signatures generated
        by the very last call served from the cache.

        Getting such a key requires the identity to have the "Storage Blob
        Delegator" role on the storage account, on top of a data plane role.
        """
        self.ensure_one()
        now = datetime.datetime.now(datetime.timezone.utc)
        skew = datetime.timedelta(seconds=AZURE_CLOCK_SKEW_TOLERANCE)
        expiry_time = (
            now
            + datetime.timedelta(seconds=self.azure_delegation_key_expiration)
            + datetime.timedelta(seconds=self.azure_signed_url_expiration)
            + skew
        )
        return self._azure_call_synchronous(
            service_client.get_user_delegation_key,
            key_start_time=now - skew,
            key_expiry_time=expiry_time,
        )

    def _azure_delete_blobs(self, blob_names):
        """Delete the given blobs from this storage's container.

        The deletion is sent as a single batch request, so the caller is the
        one splitting larger lists, one batch at a time.

        :return: the blobs that are gone, either because they were deleted or
            because they were already missing, which is as good as deleted.
        :raise ValueError: if more blobs than a batch can hold are given.
        """
        self.ensure_one()
        if not blob_names:
            return []
        if len(blob_names) > AZURE_MAX_BLOBS_PER_BATCH:
            raise ValueError(
                f"A blob batch request holds at most "
                f"{AZURE_MAX_BLOBS_PER_BATCH} blobs, got {len(blob_names)}."
            )
        root_fs = self._get_root_filesystem()
        status_codes = self._azure_call_synchronous(
            _azure_delete_blobs_batch,
            root_fs.service_client,
            self.get_directory_path(),
            blob_names,
        )
        return [
            blob_name
            for blob_name, status_code in zip(blob_names, status_codes, strict=True)
            if 200 <= status_code < 300 or status_code == 404
        ]
