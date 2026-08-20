# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import os

from odoo_test_helper import FakeModelLoader

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.attachment_pdfa.models import ir_attachment


class TestIrAttachmentPdfa(TransactionCase):
    def setUp(self):
        super().setUp()
        self.loader = FakeModelLoader(self.env, self.__module__)
        self.loader.backup_registry()
        from .fake_mail_message import FakeMailMessage
        from .pdfa_test_model import PdfaTestModel

        # Load FakeMailMessage if mail module is not installed in the test env
        fake_models = [PdfaTestModel]
        if "mail.message" not in self.env:
            fake_models.append(FakeMailMessage)
        self.loader.update_registry(tuple(fake_models))
        self.test_record = self.env["pdfa.test.model"].create(
            {
                "must_convert": True,
            }
        )
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.dummy_pdf_path = os.path.join(self.dir_path, "dummy.pdf")

    def tearDown(self):
        self.loader.restore_registry()
        super().tearDown()

    def _get_dummy_pdf_bytes(self):
        with open(self.dummy_pdf_path, "rb") as pdf_file:
            return pdf_file.read()

    def _set_conversion_method(self, method):
        self.env["ir.config_parameter"].sudo().set_param(
            "attachment_pdfa.method", method
        )

    def _set_storage_mode(self, mode):
        self.env["ir.config_parameter"].sudo().set_param("attachment_pdfa.mode", mode)

    def test_convert_pdf_ghostscript(self):
        """Test real conversion using Ghostscript engine via cron in replace mode."""
        self._set_conversion_method("ghostscript")
        self._set_storage_mode("replace")
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "dummy_gs.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)
        self.assertEqual(attachment.raw, raw_pdf)
        self.env["ir.attachment"]._cron_convert_pdfa()
        self.assertFalse(attachment.is_pdfa_needed)
        self.assertNotEqual(attachment.raw, raw_pdf)
        self.assertTrue(
            b"pdfaid" in attachment.raw or b"GTS_PDFA" in attachment.raw,
            "Ghostscript output does not contain expected PDF/A metadata",
        )

    def test_mail_message_target_resolution(self):
        """Test attachment linked to a mail.message pointing to a pdfa.test.model."""
        self._set_conversion_method("odoo")
        message = self.env["mail.message"].create(
            {
                "model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "mail_document.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "mail.message",
                "res_id": message.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)

    @mute_logger("odoo.tools.pdf")
    def test_convert_pdf_odoo_native(self):
        """Test real conversion using Odoo native engine via cron in replace mode."""
        self._set_conversion_method("odoo")
        self._set_storage_mode("replace")
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "dummy_odoo.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)
        self.assertEqual(attachment.raw, raw_pdf)
        self.env["ir.attachment"]._cron_convert_pdfa()
        self.assertFalse(attachment.is_pdfa_needed)
        self.assertNotEqual(attachment.raw, raw_pdf)
        self.assertIn(
            b"<pdfaid:part>3</pdfaid:part>",
            attachment.raw,
            "Odoo native output does not contain PDF/A-3 XMP metadata",
        )

    @mute_logger("odoo.tools.pdf")
    def test_storage_mode_beside(self):
        """Test PDF/A conversion creating a new file beside original."""
        self._set_conversion_method("odoo")
        self._set_storage_mode("beside")
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "original_doc.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)
        self.env["ir.attachment"]._cron_convert_pdfa()
        # Original attachment remains unchanged and flag is cleared
        self.assertFalse(attachment.is_pdfa_needed)
        self.assertEqual(attachment.raw, raw_pdf)
        # Verify new PDF/A attachment was created beside original
        new_attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "pdfa.test.model"),
                ("res_id", "=", self.test_record.id),
                ("id", "!=", attachment.id),
            ]
        )
        self.assertEqual(len(new_attachment), 1)
        self.assertEqual(new_attachment.name, "original_doc_PDFA.pdf")
        self.assertNotEqual(new_attachment.raw, raw_pdf)
        self.assertIn(b"<pdfaid:part>3</pdfaid:part>", new_attachment.raw)
        self.assertFalse(new_attachment.is_pdfa_needed)

    @mute_logger("odoo.tools.pdf")
    def test_write_delayed_record_linking(self):
        """Test recomputing is_pdfa_needed and converting when linked late via write."""
        self._set_conversion_method("odoo")
        self._set_storage_mode("replace")
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "unlinked.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
            }
        )
        self.assertFalse(attachment.is_pdfa_needed)
        # Link model and record via write
        attachment.write(
            {
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)
        self.env["ir.attachment"]._cron_convert_pdfa()
        self.assertFalse(attachment.is_pdfa_needed)
        self.assertNotEqual(attachment.raw, raw_pdf)
        self.assertIn(b"<pdfaid:part>3</pdfaid:part>", attachment.raw)

    @mute_logger("odoo.tools.pdf")
    def test_write_update_binary_content(self):
        """Test manually re-flagging is_pdfa_needed on content update."""
        self._set_conversion_method("odoo")
        self._set_storage_mode("replace")
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "initial.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.env["ir.attachment"]._cron_convert_pdfa()
        self.assertFalse(attachment.is_pdfa_needed)
        # Update binary datas and set is_pdfa_needed manually (readonly=False)
        encoded_datas = base64.b64encode(raw_pdf).decode("utf-8")
        attachment.write({"datas": encoded_datas, "is_pdfa_needed": True})
        self.assertTrue(attachment.is_pdfa_needed)
        self.env["ir.attachment"]._cron_convert_pdfa()
        self.assertFalse(attachment.is_pdfa_needed)
        self.assertIn(b"<pdfaid:part>3</pdfaid:part>", attachment.raw)

    @mute_logger("odoo.addons.attachment_pdfa.models.ir_attachment")
    def test_conversion_failure_raises(self):
        """Test that failure raises for a PDF that passes the header check
        but is structurally corrupt (e.g. truncated), so it gets queued for
        conversion and the actual parser fails on it."""
        self._set_conversion_method("odoo")
        corrupt_pdf_raw = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog"
        attachment = self.env["ir.attachment"].create(
            {
                "name": "corrupt_document.pdf",
                "raw": corrupt_pdf_raw,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)
        with self.assertRaises(UserError):
            self.env["ir.attachment"]._cron_convert_pdfa()

    def test_conversion_disabled(self):
        """Test that method 'disable' leaves attachments untreated in cron."""
        self._set_conversion_method("disable")
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "dummy_disabled.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)
        self.env["ir.attachment"]._cron_convert_pdfa()
        self.assertTrue(attachment.is_pdfa_needed)
        self.assertEqual(attachment.raw, raw_pdf)

    def test_mixin_condition_false(self):
        """Test that is_pdfa_needed computes to False when mixin returns False."""
        self._set_conversion_method("ghostscript")
        self.test_record.must_convert = False
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "dummy_skipped.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertFalse(attachment.is_pdfa_needed)

    def test_unsupported_model_ignored(self):
        """Test that models without attachment.pdfa.mixin compute is_pdfa_needed as
        False."""
        self._set_conversion_method("ghostscript")
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "res_partner.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "res.partner",
                "res_id": self.env.user.partner_id.id,
            }
        )
        self.assertFalse(attachment.is_pdfa_needed)

    def test_non_pdf_attachment_ignored(self):
        """Test non-PDF attachments compute is_pdfa_needed as False."""
        self._set_conversion_method("ghostscript")
        image_raw = b"FAKE_PNG_DATA"
        attachment = self.env["ir.attachment"].create(
            {
                "name": "test_image.png",
                "raw": image_raw,
                "mimetype": "image/png",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertFalse(attachment.is_pdfa_needed)

    def test_base_mixin_default_returns_false(self):
        """Test default _attachment_must_be_pdfa implementation on base mixin."""
        attachment = self.env["ir.attachment"].create({"name": "test.pdf"})
        mixin_model = self.env["attachment.pdfa.mixin"]
        self.assertFalse(mixin_model._attachment_must_be_pdfa(attachment))

    def test_res_config_settings_integration(self):
        """Test reading and saving conversion settings via res.config.settings."""
        config = self.env["res.config.settings"].create(
            {
                "attachment_pdfa_method": "odoo",
                "attachment_pdfa_mode": "beside",
            }
        )
        config.execute()
        self.assertEqual(
            self.env["ir.config_parameter"].sudo().get_param("attachment_pdfa.method"),
            "odoo",
        )
        self.assertEqual(
            self.env["ir.config_parameter"].sudo().get_param("attachment_pdfa.mode"),
            "beside",
        )

    def test_already_pdfa3_ignored(self):
        """Test that documents already tagged as PDF/A-3 are skipped."""
        self._set_conversion_method("odoo")
        pdfa3_raw = b"%PDF-1.7\n<pdfaid:part>3</pdfaid:part>"
        attachment = self.env["ir.attachment"].create(
            {
                "name": "already_pdfa3.pdf",
                "raw": pdfa3_raw,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertFalse(attachment.is_pdfa_needed)

    def test_pdfa1_requires_conversion(self):
        """Test that PDF/A-1 tagged files still require conversion to PDF/A-3."""
        self._set_conversion_method("odoo")
        pdfa1_raw = b"%PDF-1.7\n<pdfaid:part>1</pdfaid:part>"
        attachment = self.env["ir.attachment"].create(
            {
                "name": "pdfa1.pdf",
                "raw": pdfa1_raw,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)

    def test_pdf_extension_fallback(self):
        """Test detection when mimetype is generic but filename ends in .pdf."""
        self._set_conversion_method("odoo")
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "document.pdf",
                "raw": raw_pdf,
                "mimetype": "application/octet-stream",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)

    def test_datas_field_fallback_and_decoding(self):
        """Test fallback to 'datas' field and base64 cleaning logic."""
        raw_pdf = self._get_dummy_pdf_bytes()
        encoded_pdf = base64.b64encode(raw_pdf).decode("utf-8")
        attachment = self.env["ir.attachment"].create(
            {
                "name": "datas_fallback.pdf",
                "datas": encoded_pdf,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertTrue(attachment.is_pdfa_needed)
        cleaned_raw = attachment._get_clean_raw_pdf()
        self.assertTrue(cleaned_raw.startswith(b"%PDF"))

    def test_invalid_base64_datas_fallback_graceful(self):
        """Test graceful error handling when raw content contains invalid base64."""
        attachment = self.env["ir.attachment"].create(
            {
                "name": "corrupt_b64.pdf",
                "raw": b"!!!NOT_BASE64!!!",
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        self.assertEqual(attachment._get_clean_raw_pdf(), b"!!!NOT_BASE64!!!")
        self.assertFalse(attachment.is_pdfa_needed)

    def test_missing_target_record_ignored(self):
        """Test attachment with non-existent res_id computes is_pdfa_needed as False."""
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "non_existent_record.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": 999999,
            }
        )
        self.assertFalse(attachment.is_pdfa_needed)

    def test_mail_message_pointing_to_unsupported_model(self):
        """Test mail.message pointing to a model without mixin computes as False."""
        message = self.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": self.env.user.partner_id.id,
            }
        )
        raw_pdf = self._get_dummy_pdf_bytes()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "mail_partner.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "mail.message",
                "res_id": message.id,
            }
        )
        self.assertFalse(attachment.is_pdfa_needed)

    def test_ghostscript_missing_profiles_failure(self):
        """Test Ghostscript engine error handling when ICC profiles are unavailable."""
        self._set_conversion_method("ghostscript")
        raw_pdf = self._get_dummy_pdf_bytes()
        self.env["ir.attachment"].create(
            {
                "name": "dummy_gs_no_profile.pdf",
                "raw": raw_pdf,
                "mimetype": "application/pdf",
                "res_model": "pdfa.test.model",
                "res_id": self.test_record.id,
            }
        )
        orig_val = ir_attachment._PROFILES_AVAILABLE
        try:
            ir_attachment._PROFILES_AVAILABLE = False
            with self.assertRaises(UserError):
                self.env["ir.attachment"]._cron_convert_pdfa()
        finally:
            ir_attachment._PROFILES_AVAILABLE = orig_val

    @mute_logger("odoo.tools.pdf")
    def test_cron_batching_and_retrigger(self):
        """Test that cron schedules a trigger record when batch limit is reached."""
        self._set_conversion_method("odoo")
        raw_pdf = self._get_dummy_pdf_bytes()
        for i in range(2):
            self.env["ir.attachment"].create(
                {
                    "name": f"batch_{i}.pdf",
                    "raw": raw_pdf,
                    "mimetype": "application/pdf",
                    "res_model": "pdfa.test.model",
                    "res_id": self.test_record.id,
                }
            )
        cron = self.env.ref("attachment_pdfa.ir_cron_convert_pdfa")
        triggers_before = self.env["ir.cron.trigger"].search_count(
            [("cron_id", "=", cron.id)]
        )
        self.env["ir.attachment"]._cron_convert_pdfa(batch_size=1)
        triggers_after = self.env["ir.cron.trigger"].search_count(
            [("cron_id", "=", cron.id)]
        )
        self.assertGreater(
            triggers_after,
            triggers_before,
            "Cron trigger record should be created when work remains.",
        )

    def test_can_commit_helper(self):
        """Verify _can_commit returns False in test execution context."""
        self.assertFalse(self.env["ir.attachment"]._can_commit())
