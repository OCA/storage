# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import base64
import shutil
import tempfile
from unittest import mock

from odoo.tests.common import TransactionCase

from ..models.fs_storage import FSStorage


class TestFSStorageCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.backend: FSStorage = cls.env.ref("fs_storage.default_fs_storage")
        cls.backend.json_options = {"target_options": {"auto_mkdir": "True"}}
        cls.filedata = base64.b64encode(b"This is a simple file")
        cls.filename = "test_file.txt"
        cls.case_with_subdirectory = "subdirectory/here"
        cls.demo_user = cls.env.ref("base.user_demo")

    def setUp(self):
        super().setUp()
        mocked_backend = mock.patch.object(
            self.backend.__class__, "_get_filesystem_storage_path"
        )
        mocked_get_filesystem_storage_path = mocked_backend.start()
        tempdir = tempfile.mkdtemp()
        mocked_get_filesystem_storage_path.return_value = tempdir

        # pylint: disable=unused-variable
        @self.addCleanup
        def stop_mock():
            mocked_backend.stop()
            # recursively delete the tempdir
            shutil.rmtree(tempdir)

    def _create_file(self, backend: FSStorage, filename: str, filedata: str):
        with backend.fs.open(filename, "wb") as f:
            f.write(filedata)
