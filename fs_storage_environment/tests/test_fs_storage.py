# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from unittest import mock

from odoo.addons.fs_storage.tests.common import TestFSStorageCase


class TestFSStorageEnv(TestFSStorageCase):
    def test_options_env(self):
        self.backend.json_options = {"key": {"sub_key": "$KEY_VAR"}}
        eval_json_options = {"key": {"sub_key": "TEST"}}
        options = self.backend._get_fs_options()
        self.assertDictEqual(options, self.backend.json_options)
        self.backend.eval_options_from_env = True
        with mock.patch.dict("os.environ", {"KEY_VAR": "TEST"}):
            options = self.backend._get_fs_options()
            self.assertDictEqual(options, eval_json_options)
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertLogs(
                "odoo.addons.fs_storage_environment.models.fs_storage",
                level="WARNING",
            ) as log:
                options = self.backend._get_fs_options()

        self.assertDictEqual(options, self.backend.json_options)
        self.assertIn(
            (
                f"Environment variable KEY_VAR is not set for "
                f"fs_storage {self.backend.display_name}."
            ),
            log.output[0],
        )
