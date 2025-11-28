# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import base64
import os
import shutil
import tempfile
from unittest import mock

from odoo.fields import Command
from odoo.tests.common import TransactionCase

from ..models.fs_storage import FSStorage


class TestFSStorageCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.backend: FSStorage = cls.env["fs.storage"].create(
            {
                "name": "Odoo Filesystem Backend",
                "protocol": "odoofs",
                "code": "odoofs",
            }
        )
        cls.backend.json_options = {"target_options": {"auto_mkdir": "True"}}
        cls.filedata = base64.b64encode(b"This is a simple file")
        cls.filename = "test_file.txt"
        cls.case_with_subdirectory = "subdirectory/here"
        cls.demo_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Test User",
                    "login": "demo",
                    "password": "demo",
                    "email": "test@yourcompany.com",
                    "company_id": cls.env.ref("base.main_company").id,
                    "group_ids": [Command.link(cls.env.ref("base.group_user").id)],
                }
            )
        )
        cls.temp_dir = tempfile.mkdtemp()

    def setUp(self):
        super().setUp()
        mocked_backend = mock.patch.object(
            self.backend.__class__, "_get_filesystem_storage_path"
        )
        mocked_get_filesystem_storage_path = mocked_backend.start()
        mocked_get_filesystem_storage_path.return_value = self.temp_dir
        self.backend.write({"directory_path": self.temp_dir})

        # pylint: disable=unused-variable
        @self.addCleanup
        def stop_mock():
            mocked_backend.stop()
            # recursively delete the tempdir
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)

    def _create_file(self, backend: FSStorage, filename: str, filedata: str):
        with backend.fs.open(filename, "wb") as f:
            f.write(filedata)
