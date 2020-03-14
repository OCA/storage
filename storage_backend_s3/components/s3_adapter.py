# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2019 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import io
import logging

from odoo import _, exceptions

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError, EndpointConnectionError

except ImportError as err:  # pragma: no cover
    _logger.debug(err)


class S3StorageAdapter(Component):
    _name = "s3.adapter"
    _inherit = "base.storage.adapter"
    _usage = "amazon_s3"

    def _aws_bucket_params(self):
        params = {
            "aws_access_key_id": self.collection.aws_access_key_id,
            "aws_secret_access_key": self.collection.aws_secret_access_key,
        }
        if self.collection.aws_host:
            params["endpoint_url"] = self.collection.aws_host

        if self.collection.aws_region:
            if self.collection.aws_region != "other":
                params["region_name"] = self.collection.aws_region
            elif self.collection.aws_other_region:
                params["region_name"] = self.collection.aws_other_region
        return params

    def _get_bucket(self):
        params = self._aws_bucket_params()
        s3 = boto3.resource("s3", **params)
        bucket_name = self.collection.aws_bucket
        bucket = s3.Bucket(bucket_name)
        exists = True
        try:
            s3.meta.client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                exists = False
        except EndpointConnectionError as error:
            # log verbose error from s3, return short message for user
            _logger.exception("Error during connection on S3")
            raise exceptions.UserError(str(error))
        region_name = params.get("region_name")
        if not exists:
            if not region_name:
                bucket = s3.create_bucket(Bucket=bucket_name)
            else:
                bucket = s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region_name},
                )
        return bucket

    def _get_object(self, relative_path=None):
        bucket = self._get_bucket()
        path = None
        if relative_path:
            path = self._fullpath(relative_path)
        return bucket.Object(key=path)

    def add(self, relative_path, bin_data, mimetype=None, **kwargs):
        s3object = self._get_object(relative_path)
        file_params = self._aws_upload_fileobj_params(mimetype=mimetype, **kwargs)
        with io.BytesIO() as fileobj:
            fileobj.write(bin_data)
            fileobj.seek(0)
            try:
                s3object.upload_fileobj(fileobj, **file_params)
            except ClientError as error:
                # log verbose error from s3, return short message for user
                _logger.exception("Error during storage of the file %s" % relative_path)
                raise exceptions.UserError(
                    _("The file could not be stored: %s") % str(error)
                )

    def _aws_upload_fileobj_params(self, mimetype=None, **kw):
        extra_args = {}
        if mimetype:
            extra_args["ContentType"] = mimetype
        if self.collection.aws_cache_control:
            extra_args["CacheControl"] = self.collection.aws_cache_control
        if self.collection.aws_file_acl:
            extra_args["ACL"] = self.collection.aws_file_acl
        if extra_args:
            return {"ExtraArgs": extra_args}
        return {}

    def get(self, relative_path):
        s3object = self._get_object(relative_path)
        return s3object.get()["Body"].read()

    def list(self, relative_path):
        bucket = self._get_bucket()
        dir_path = self.collection.directory_path or ""
        return [
            o.key.replace(dir_path, "").lstrip("/")
            for o in bucket.objects.filter(Prefix=dir_path)
        ]

    def delete(self, relative_path):
        s3object = self._get_object(relative_path)
        s3object.delete()
