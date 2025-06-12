# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import os
import shutil
from importlib import resources as importlib_resources
from unittest import mock

from odoo.tests.common import RecordCapturer

from odoo.addons.fs_folder.tests.common import FsFolderTestCase


class TestFsFodlerFieldValueAdapter(FsFolderTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        field = cls.env["ir.model.fields"].search(
            [
                ("model", "=", cls.fs_test_model._name),
                ("name", "=", "fs_folder"),
            ]
        )
        cls.report = (
            cls.env["ir.actions.report"]
            .create(
                {
                    "name": "Test Report Partner",
                    "model": cls.fs_test_model._name,
                    "report_name": "test_report.test_report_partner",
                    "paperformat_id": cls.env.ref("base.paperformat_euro").id,
                    "report_type": "qweb-pdf",
                    "save_in_fs_folder": True,
                    "fs_folder_field_id": field.id,
                    "attachment": 'object.name + ".pdf"',
                    "attachment_use": False,
                }
            )
            .with_context(force_report_rendering=True)
        )

        cls.report_view = cls.env["ir.ui.view"].create(
            {
                "type": "qweb",
                "name": "test_report_partner",
                "key": "test_report.test_report_partner",
                "arch": """
                    <main>
                        <div t-foreach="docs" t-as="o">
                            <div class="article"
                              t-att-data-oe-model="o._name"
                              t-att-data-oe-id="o.id">
                                <span t-esc="o.display_name"/>
                            </div>
                        </div>
                    </main>
                """,
            }
        )
        cls.pdf_filename_1 = importlib_resources.files(
            "odoo.addons.fs_folder_report.tests"
        ).joinpath("dummy.pdf")
        with cls.pdf_filename_1.open("rb") as pdf:
            cls.pdf_content_1 = pdf.read()
        wkhtmltopdf_patcher = mock.patch.object(
            cls.report.__class__, "_run_wkhtmltopdf"
        )
        cls.mocked_wkhtmltopdf = wkhtmltopdf_patcher.start()
        cls.mocked_wkhtmltopdf.return_value = cls.pdf_content_1
        get_wkhtmltopdf_state_patcher = mock.patch.object(
            cls.report.__class__, "get_wkhtmltopdf_state"
        )
        cls.mocked_get_wkhtmltopdf_state = get_wkhtmltopdf_state_patcher.start()
        cls.mocked_get_wkhtmltopdf_state.return_value = "ok"

        @cls.addClassCleanup
        def stop_mock():
            wkhtmltopdf_patcher.stop()
            get_wkhtmltopdf_state_patcher.stop()

    def tearDown(self):
        super().tearDown()
        # empty the temp dir
        for f in os.listdir(self.temp_dir):
            full_path = os.path.join(self.temp_dir, f)
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                shutil.rmtree(full_path)

    def test_report_in_non_initialized_folder(self):
        """Test that the report is saved in the folder associated with the record."""
        # Create a record with an uninitialized folder
        record = self.fs_test_model.create(
            {
                "name": "Test Record",
            }
        )

        # Generate the report
        with RecordCapturer(self.env["ir.attachment"], []) as capturer:
            content, _ = self.report._render_qweb_pdf(
                self.report.report_name, res_ids=[record.id]
            )
        # Check that the folder was initialized and the report was saved
        folder = record.fs_folder
        self.assertTrue(folder)
        self.assertTrue(folder.fs.exists("Test Record.pdf"))
        # Check that the attachment was created
        attachment = capturer.records
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.name, "Test Record.pdf")
        # check the attachment content
        attachment_content = attachment.raw
        self.assertEqual(attachment_content, content)

        # check that the attachment is into the expected storage
        # with a storefname that contains the folder path
        expected_store_fname = (
            f"{self.temp_backend.code}://{record.name}/{record.name}.pdf"
        )
        self.assertEqual(attachment.store_fname, expected_store_fname)

    def test_report_in_initialized_folder_with_report_path(self):
        """Test that the report is saved in the folder associated with the record."""
        # Create a record with an initialized folder
        record = self.fs_test_model.create(
            {
                "name": "Test Record",
            }
        )
        self.report.fs_folder_path = "'nested/sub nested'"
        record.fs_folder.initialize()

        # Generate the report
        with RecordCapturer(self.env["ir.attachment"], []) as capturer:
            content, _ = self.report._render_qweb_pdf(
                self.report.report_name, res_ids=[record.id]
            )
        # Check that the folder was initialized and the report was saved
        folder = record.fs_folder
        self.assertTrue(folder)
        self.assertTrue(folder.fs.exists("nested/sub nested/Test Record.pdf"))
        # Check that the attachment was created
        attachment = capturer.records
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.name, "Test Record.pdf")
        # check the attachment content
        attachment_content = attachment.raw
        self.assertEqual(attachment_content, content)

        # check that the attachment is into the expected storage
        # with a storefname that contains the folder path
        expected_store_fname = (
            f"{self.temp_backend.code}://{record.name}"
            f"/nested/sub nested/{record.name}.pdf"
        )
        self.assertEqual(attachment.store_fname, expected_store_fname)

    def test_generate_report_multiple_times(self):
        """Test that generating the report multiple times works correctly."""
        # Create a record with an initialized folder
        record = self.fs_test_model.create(
            {
                "name": "Test Record",
            }
        )
        record.fs_folder.initialize()
        with mock.patch.object(
            self.report.__class__, "retrieve_attachment"
        ) as mocked_retrieve:
            mocked_retrieve.return_value = self.env["ir.attachment"].browse()

            # Generate the report multiple times
            for idx in range(3):
                with RecordCapturer(self.env["ir.attachment"], []) as capturer:
                    content, _ = self.report._render_qweb_pdf(
                        self.report.report_name, res_ids=[record.id]
                    )
                # Check that the folder was initialized and the report was saved
                folder = record.fs_folder
                self.assertTrue(folder)
                self.assertTrue(folder.fs.exists("Test Record.pdf"))
                # Check that the attachment was created
                attachment = capturer.records
                self.assertEqual(len(attachment), 1, f"Failed on iteration {idx}")
                self.assertEqual(attachment.name, "Test Record.pdf")
                # check the attachment content
                attachment_content = attachment.raw
                self.assertEqual(attachment_content, content)

                # check that the attachment is into the expected storage
                count = ""
                if idx > 0:
                    count = f"({idx})"
                expected_store_fname = (
                    f"{self.temp_backend.code}://{record.name}/{record.name}{count}.pdf"
                )
                self.assertEqual(attachment.store_fname, expected_store_fname)
