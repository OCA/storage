# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=missing-manifest-dependency
# disable warning on 'vcr' missing in manifest: this is only a dependency for
# dev/tests

import logging
import os

from vcr_unittest import VCRMixin

from odoo.addons.storage_backend.tests.common import BackendStorageTestMixin, CommonCase

_logger = logging.getLogger(__name__)


class AmazonS3Case(VCRMixin, CommonCase, BackendStorageTestMixin):
    def _get_vcr_kwargs(self, **kwargs):
        return {
            "record_mode": "once",
            "match_on": ["method", "path", "query", "body"],
            "filter_headers": ["Authorization"],
            "decode_compressed_response": True,
        }

    def setUp(self):
        super(AmazonS3Case, self).setUp()
        self.backend.write(
            {
                "backend_type": "amazon_s3",
                "aws_bucket": os.environ.get("AWS_BUCKET", "test-storage-backend"),
                "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", ""),
                "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
                "aws_host": os.environ.get("AWS_HOST", "https://sos-ch-dk-2.exo.io"),
            }
        )

    def test_setting_and_getting_data_from_root(self):
        self._test_setting_and_getting_data_from_root()

    def test_setting_and_getting_data_from_dir(self):
        self._test_setting_and_getting_data_from_dir()

    def test_params(self):
        adapter = self.backend._get_adapter()
        self.backend.aws_host = ""
        params = adapter._aws_bucket_params()
        self.assertNotIn("endpoint_url", params)
        self.backend.aws_host = "another.s3.endpoint.com"
        params = adapter._aws_bucket_params()
        self.assertEqual(params["endpoint_url"], "another.s3.endpoint.com")

    def test_aws_other_region_filled(self):
        adapter = self.backend._get_adapter()
        self.assertFalse(self.backend.aws_region)
        self.backend.aws_other_region = "fr-par"
        params = adapter._aws_bucket_params()
        # no region as "aws_region" is empty
        self.assertNotIn("region_name", params)
        self.backend.aws_region = "other"
        params = adapter._aws_bucket_params()
        self.assertEqual(params["region_name"], "fr-par")

    def test_aws_other_region_empty(self):
        self.backend.aws_other_region = ""
        adapter = self.backend._get_adapter()
        params = adapter._aws_bucket_params()
        self.assertNotIn("region_name", params)
