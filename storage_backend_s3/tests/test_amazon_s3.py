# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=missing-manifest-dependency
# disable warning on 'vcr' missing in manifest: this is only a dependency for
# dev/tests

import logging
import os

from vcr_unittest import VCRMixin

from odoo.addons.storage_backend.tests.common import Common, GenericStoreCase

_logger = logging.getLogger(__name__)


class AmazonS3Case(VCRMixin, Common, GenericStoreCase):
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
                "aws_bucket": os.environ.get("AWS_BUCKET", "ak-testing-bucket"),
                "aws_region": os.environ.get("AWS_REGION", "eu-west-3"),
                "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "FAKEID"),
                "aws_secret_access_key": os.environ.get(
                    "AWS_SECRET_ACCESS_KEY", "FAKESECRET"
                ),
            }
        )
