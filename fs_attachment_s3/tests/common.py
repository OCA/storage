# Copyright 2025 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestFSAttachmentS3Common(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.s3_backend_config = {
            "name": "S3 Storage",
            "protocol": "s3",
            "code": "s3tst",
            "directory_path": "test-bucket",
            "json_options": {
                "key": "aws-key",
                "secret": "aws-secret",
                "client_kwargs": {
                    "endpoint_url": "http://minio.minio/",
                    "region_name": "aws-region",
                },
            },
            "base_url": False,  # S3 does not use base_url for x-sendfile
        }
        cls.s3_backend = cls.env["fs.storage"].create(cls.s3_backend_config)
        cls.ir_attachment_model = cls.env["ir.attachment"]

        cls.fake_attachment_s3 = cls.env["ir.attachment"].create(
            {
                "name": "fake_s3_file.txt",
                "fs_storage_id": cls.s3_backend.id,
            }
        )
        cls.fake_attachment_s3.flush_recordset()
        # update the attachment into database since we don't have a real S3 bucket
        # and we can't use moto to mock S3 since s3fs rely on aiobotocore
        cls.env.cr.execute(
            """
                UPDATE
                    ir_attachment
                SET
                    store_fname = 's3tst://dir/sub/fake_s3_file.txt',
                    fs_filename = 'fake_s3_file.txt',
                    fs_storage_code = 's3tst',
                    checksum = 234,
                    file_size = 1234,
                    fs_storage_id = %s
                WHERE
                    id = %s
            """,
            (cls.s3_backend.id, cls.fake_attachment_s3.id),
        )
        cls.fake_attachment_s3.invalidate_recordset()

    def setUp(self):
        super().setUp()
        # enforce backend_config fields since it seems that they are reset on
        # savepoint rollback when managed by server_environment -> TO Be investigated
        self.s3_backend.write(self.s3_backend_config)
