# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import shutil
import tempfile

from odoo.orm.model_classes import add_to_registry
from odoo.tests.common import TransactionCase

from odoo.addons.base.tests.common import BaseCommon


class FsFolderTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env["base"].with_context(**BaseCommon.default_env_context()).env
        from .models import FsTestModel, FsTestModelInherits, FsTestModelRelated

        model_names = [
            FsTestModel._name,
            FsTestModelInherits._name,
            FsTestModelRelated._name,
        ]
        add_to_registry(cls.registry, FsTestModel)
        add_to_registry(cls.registry, FsTestModelInherits)
        add_to_registry(cls.registry, FsTestModelRelated)
        cls.registry._setup_models__(cls.env.cr, model_names)
        cls.registry.init_models(cls.env.cr, model_names, {"models_to_check": True})
        cls.addClassCleanup(cls.registry.__delitem__, FsTestModel._name)
        cls.addClassCleanup(cls.registry.__delitem__, FsTestModelInherits._name)
        cls.addClassCleanup(cls.registry.__delitem__, FsTestModelRelated._name)

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
        # Remove check_attrs cleanup if exists to avoid conflict with FakeModelLoader.
        # since superClass uses it for its own puposes not relevant for our tests.
        check_attrs = (getattr(self, "check_attrs", None), tuple(), {})
        if check_attrs in self._cleanups:
            self._cleanups.remove(check_attrs)
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
