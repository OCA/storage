# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)

try:
    import boto3
except ImportError as err:  # pragma: no cover
    _logger.debug(err)


class StorageBackend(models.Model):
    _inherit = "storage.backend"

    backend_type = fields.Selection(selection_add=[("amazon_s3", "Amazon S3")])
    aws_host = fields.Char(
        string="AWS Host",
        help="If you are using a different host than standard AWS ones, "
        "eg: Exoscale, Openstack. Also called endpoint",
    )
    aws_bucket = fields.Char(string="Bucket")
    aws_access_key_id = fields.Char(string="Access Key ID")
    aws_secret_access_key = fields.Char(string="Secret Access Key")
    aws_region = fields.Char(string="Region",
        help="Can be empty for some providers")
    aws_cache_control = fields.Char(default="max-age=31536000, public")
    aws_file_acl = fields.Selection(selection=[
        ('', ''),
        ('private', 'private'),
        ('public-read', 'public-read'),
        ('public-read-write', 'public-read-write'),
        ('aws-exec-read', 'aws-exec-read'),
        ('authenticated-read', 'authenticated-read'),
        ('bucket-owner-read', 'bucket-owner-read'),
        ('bucket-owner-full-control', 'bucket-owner-full-control'),
    ])
    aws_available_regions = fields.Selection(
        selection="_selection_aws_region",
        help="Helper to choose a region.",
        store=False)

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update({
            "aws_host": {},
            "aws_bucket": {},
            "aws_access_key_id": {},
            "aws_secret_access_key": {},
            "aws_region": {},
            "aws_cache_control": {},
            "aws_file_acl": {},
        })
        return env_fields

    _aws_available_regions = None

    @classmethod
    def _selection_aws_region(self):
        if self._aws_available_regions:
            return self._aws_available_regions
        # This calls AWS web servers,
        # it introduce latency in rendering of
        # form view and tree view of storage.backend
        session = boto3.session.Session()
        self._aws_available_regions = [
            (region, region.replace("-", " ").capitalize())
            for region in session.get_available_regions("s3")
        ]
        return self._aws_available_regions

    @api.onchange("aws_available_regions")
    def _onchange_available_regions(self):
        # aws_available_region is an helper to set region
        # only if host is on amazon
        self.aws_region = self.aws_available_regions
