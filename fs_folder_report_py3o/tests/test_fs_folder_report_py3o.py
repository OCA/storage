# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
import shutil
import tempfile
from unittest import mock

from odoo.tests.common import RecordCapturer

from odoo.addons.base.tests.test_mimetypes import PNG
from odoo.addons.fs_folder.tests.common import FsFolderTestCase


class TestReportPy3o(FsFolderTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.image_1920 = PNG
        cls.report = cls.env.ref("report_py3o.res_users_report_py3o")
        cls.py3o_report = cls.env["py3o.report"].create(
            {"ir_actions_report_id": cls.report.id}
        )
        # add fs folder field to the user model
        field = cls.env["ir.model.fields"].create(
            {
                "name": "x_fs_folder",
                "model": "res.users",
                "model_id": cls.env.ref("base.model_res_users").id,
                "field_description": "FS Folder",
                "ttype": "fs_folder",
                "store": True,
            }
        )
        cls.report.write(
            {
                "save_in_fs_folder": True,
                "fs_folder_field_id": field.id,
                "fs_folder_path": "'reports'",
                "attachment": 'object.name + "_report.pdf"',
            }
        )

    def tearDown(self):
        super().tearDown()
        # empty the temp dir
        for f in os.listdir(self.temp_dir):
            full_path = os.path.join(self.temp_dir, f)
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                shutil.rmtree(full_path)

    def _render_patched(self, result_text="test result", call_count=1):
        py3o_report = self.env["py3o.report"]
        py3o_report_obj = py3o_report.create({"ir_actions_report_id": self.report.id})
        with mock.patch.object(
            py3o_report.__class__, "_create_single_report"
        ) as patched_pdf:
            result = tempfile.mktemp(".txt")
            with open(result, "w") as fp:
                fp.write(result_text)
            patched_pdf.side_effect = (
                lambda record, data: py3o_report_obj._postprocess_report(record, result)
                or result
            )
            # test the call the the create method inside our custom parser
            self.report._render(self.report.id, self.env.user.ids)
            self.assertEqual(call_count, patched_pdf.call_count)
            # generated files no more exists
            self.assertFalse(os.path.exists(result))

    def test_render_report(self):
        with RecordCapturer(self.env["ir.attachment"], []) as rec:
            self._render_patched()
        attachment = rec.records
        self.assertEqual(len(attachment), 1)
        expected_store_fname = f"{self.temp_backend.code}://{self.env.user.name}/reports/{self.env.user.name}_report.pdf"
        self.assertEqual(attachment.store_fname, expected_store_fname)

    def test_multiple_render_report(self):
        for idx in range(3):
            with RecordCapturer(self.env["ir.attachment"], []) as rec:
                self._render_patched()
            attachment = rec.records
            self.assertEqual(len(attachment), 1)
            count = ""
            if idx > 0:
                count = f"({idx})"
            expected_store_fname = f"{self.temp_backend.code}://{self.env.user.name}/reports/{self.env.user.name}_report{count}.pdf"
            self.assertEqual(attachment.store_fname, expected_store_fname)
