# Copyright 2019 KMEE (http://www.akretion.com).
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
from odoo.addons.storage_backend.tests.common import Common

_logger = logging.getLogger(__name__)


class FakeS3Case(Common):

    def setUp(self):
        super(FakeS3Case, self).setUp()
        self.backend.write(
            {
                "backend_type": "amazon_s3",
                "aws_bucket": os.environ.get(
                    "AWS_BUCKET", "test-storage-backend"
                ),
                "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", ""),
                "aws_secret_access_key": os.environ.get(
                    "AWS_SECRET_ACCESS_KEY", ""
                ),
                "aws_host": os.environ.get(
                    "AWS_HOST", "http://s3.fr-par.scw.cloud"
                ),
                "aws_region": "other",
            }
        )

    def test_aws_other_region_filled(self):
        self.backend.aws_other_region = "fr-par"
        adapter = self.backend._get_adapter()
        params = adapter._aws_bucket_params()
        self.assertIn("region_name", params)
        self.assertEqual(params["region_name"], "fr-par")

    def test_aws_other_region_empty(self):
        self.backend.aws_other_region = ""
        adapter = self.backend._get_adapter()
        params = adapter._aws_bucket_params()
        self.assertNotIn("region_name", params)
