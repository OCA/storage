# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)

try:
    import boto3
except ImportError as err:
    _logger.debug(err)


class StorageBackend(models.Model):
    _inherit = 'storage.backend'

    def _get_aws_region(self):
        session = boto3.session.Session()
        return [
            (region, region.replace('-', ' ').capitalize())
            for region in session.get_available_regions('s3')]

    backend_type = fields.Selection(
        selection_add=[('amazon_s3', 'Amazon S3')])
    aws_bucket = fields.Char(
        sparse="data",
        string="Bucket")
    aws_access_key_id = fields.Char(
        sparse="data",
        string="Access Key ID")
    aws_secret_access_key = fields.Char(
        related="password",
        string="Secret Access Key")
    aws_region = fields.Selection(
        selection=_get_aws_region,
        sparse="data",
        string="Region")
    aws_cache_control = fields.Char(
        default='max-age=31536000, public')
