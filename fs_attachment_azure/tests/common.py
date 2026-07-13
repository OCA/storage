# Copyright 2025 ACSONE SA/NV (http://acsone.eu).
# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestFSAttachmentAzureCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.azure_backend_config = {
            "name": "Azure Storage",
            "protocol": "az",
            "code": "azure",
            "directory_path": "test-blob",
        }
        cls.azure_backend = cls.env["fs.storage"].create(cls.azure_backend_config)
        cls.ir_attachment_model = cls.env["ir.attachment"]

        cls.fake_attachment_azure = cls.env["ir.attachment"].create(
            {
                "name": "fake_azure_file.txt",
                "fs_storage_id": cls.azure_backend.id,
            }
        )
        cls.fake_attachment_azure.flush_recordset()
        # update the attachment into database since we don't have a real blob storage
        cls.env.cr.execute(
            """
                UPDATE
                    ir_attachment
                SET
                    store_fname = 'azure://dir/sub/fake_azure_file.txt',
                    fs_filename = 'fake_azure_file.txt',
                    fs_storage_code = 'azure',
                    checksum = 234,
                    file_size = 1234,
                    fs_storage_id = %s
                WHERE
                    id = %s
            """,
            (cls.azure_backend.id, cls.fake_attachment_azure.id),
        )
        cls.fake_attachment_azure.invalidate_recordset()
