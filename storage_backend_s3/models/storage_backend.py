# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

try:
    import boto3
except ImportError as err:  # pragma: no cover
    _logger.debug(err)


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    backend_type = fields.Selection(selection_add=[("amazon_s3", "Amazon S3")])
    aws_host = fields.Char(
        string="Host",
        help="If you are using a different host than standard AWS ones, "
        "eg: Exoscale",
    )
    aws_bucket = fields.Char(string="Bucket")
    aws_access_key_id = fields.Char(string="Access Key ID")
    aws_secret_access_key = fields.Char(string="Secret Access Key")
    aws_region = fields.Selection(
        selection='_selection_aws_region', string="Region"
    )
    aws_cache_control = fields.Char(default="max-age=31536000, public")

    def _selection_aws_region(self):
        session = boto3.session.Session()
        return [
            (region, region.replace("-", " ").capitalize())
            for region in session.get_available_regions("s3")
        ]
