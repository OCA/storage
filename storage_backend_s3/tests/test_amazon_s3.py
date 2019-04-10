# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=missing-manifest-dependency
# disable warning on 'vcr' missing in manifest: this is only a dependency for
# dev/tests

import logging
import os
from os.path import dirname, join

from odoo.addons.storage_backend.tests.common import Common, GenericStoreCase
from vcr import VCR

_logger = logging.getLogger(__name__)


logging.getLogger("vcr").setLevel(logging.WARNING)

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "fixtures/cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization"],
)


class AmazonS3Case(Common, GenericStoreCase):
    def setUp(self):
        super(AmazonS3Case, self).setUp()
        self.backend.write(
            {
                "backend_type": "amazon_s3",
                "aws_bucket": os.environ.get(
                    "AWS_BUCKET", "ak-testing-bucket"
                ),
                "aws_region": os.environ.get("AWS_REGION", "eu-west-3"),
                "aws_access_key_id": os.environ.get(
                    "AWS_ACCESS_KEY_ID", "FAKEID"
                ),
                "aws_secret_access_key": os.environ.get(
                    "AWS_SECRET_ACCESS_KEY", "FAKESECRET"
                ),
            }
        )

    @recorder.use_cassette
    def test_setting_and_getting_data_from_root(self):
        super(AmazonS3Case, self).test_setting_and_getting_data_from_root()

    @recorder.use_cassette
    def test_setting_and_getting_data_from_dir(self):
        super(AmazonS3Case, self).test_setting_and_getting_data_from_dir()
