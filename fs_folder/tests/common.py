# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import shutil
import tempfile

from odoo_test_helper import FakeModelLoader

from odoo.tests.common import TransactionCase

from odoo.addons.base.tests.common import BaseCommon


class FsFolderTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env["base"].with_context(**BaseCommon.default_env_context()).env
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        cls.addClassCleanup(cls.loader.restore_registry)
        from .models import FsTestModel, FsTestModelInherits, FsTestModelRelated

        cls.loader.update_registry(
            (FsTestModel, FsTestModelInherits, FsTestModelRelated)
        )
        cls.fs_test_model = cls.env[FsTestModel._name]
        cls.fs_test_model_inherits = cls.env[FsTestModelInherits._name]
        cls.fs_test_model_related = cls.env[FsTestModelRelated._name]

        cls.temp_dir = tempfile.mkdtemp()
        # Disable exisiting backend used as default for fs contents
        cls.env["fs.storage"].search([]).filtered(
            "use_as_default_for_fs_contents"
        ).unlink()
        cls.temp_backend = cls.env["fs.storage"].create(
            {
                "name": "Temp FS Storage",
                "protocol": "file",
                "code": "tmp_dir",
                "directory_path": cls.temp_dir,
                "use_as_default_for_fs_contents": True,
            }
        )

        @cls.addClassCleanup
        def cleanup_tempdir():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        super().setUp()
        # enforce temp_backend field since it seems that they are reset on
        # savepoint rollback when managed by server_environment -> TO Be investigated
        self.temp_backend.write(
            {
                "protocol": "file",
                "code": "tmp_dir",
                "directory_path": self.temp_dir,
                "use_as_default_for_fs_contents": True,
            }
        )
