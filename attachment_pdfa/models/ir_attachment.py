# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import io
import logging
import re
import subprocess
import tempfile
from pathlib import Path

from odoo import _, api, fields, models, modules, tools
from odoo.exceptions import UserError
from odoo.tools.pdf import OdooPdfFileReader, OdooPdfFileWriter

_logger = logging.getLogger(__name__)

TIMEOUT_CONVERSION = 60

_PDFA_TARGET_PART = "3"
_PDFA_PART_RE = re.compile(rb'pdfaid:part\s*(?:=\s*["\x27]|>)\s*(\d+)')

DATA_DIR = (Path(__file__).parent.parent / "data").resolve()
ICC_PROFILE_PS = DATA_DIR / "pdfa_def.ps"
RGB_PROFILE = DATA_DIR / "iccprofiles_default_rgb.icc"

_MISSING_PROFILE_MSG = "Ghostscript ICC Profile or PDF/A definition file not found."

_PDFA_ABORT_MARKERS = (
    "PDF/A processing aborted",
    "Failed to open the supplied ICCProfile",
)

if not ICC_PROFILE_PS.is_file() or not RGB_PROFILE.is_file():
    _logger.error(_MISSING_PROFILE_MSG)
    _PROFILES_AVAILABLE = False
else:
    _PROFILES_AVAILABLE = True


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    is_pdfa_needed = fields.Boolean(
        string="Needs PDF/A Conversion",
        compute="_compute_is_pdfa_needed",
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends("mimetype", "name", "res_model", "res_id")
    def _compute_is_pdfa_needed(self):
        for attachment in self:
            attachment.is_pdfa_needed = attachment._check_should_be_pdfa()

    def _is_already_pdfa3(self, raw_data=None):
        """Return True only if the content already declares PDF/A-3 conformance.

        Content already tagged PDF/A-1 or PDF/A-2 must still be (re-)converted,
        since this module's conversion target is specifically PDF/A-3 -- the
        presence of *a* pdfaid marker isn't enough to skip it.
        """
        if raw_data is None:
            raw_data = self._get_clean_raw_pdf()
        match = _PDFA_PART_RE.search(raw_data)
        if not match:
            return False
        return match.group(1).decode() == _PDFA_TARGET_PART

    def _get_clean_raw_pdf(self):
        """Retrieve raw binary bytes, un-encoding base64 data if necessary."""
        self.ensure_one()
        raw_data = self.raw
        if not raw_data and self.datas:
            try:
                raw_data = base64.b64decode(self.datas)
            except Exception:
                raw_data = b""
        if raw_data and not raw_data.startswith(b"%PDF"):
            try:
                decoded = base64.b64decode(raw_data)
                if decoded.startswith(b"%PDF"):
                    raw_data = decoded
            except Exception as e:
                _logger.debug("Failed to base64-decode attachment PDF raw data: %s", e)
        return raw_data or b""

    def _get_target_record(self):
        """Retrieve the target record linked to this attachment."""
        self.ensure_one()
        if not (self.res_model and self.res_id):
            return False
        res_model = self.res_model
        res_id = self.res_id
        # Target record may be linked to a mail.message (soft dependency: only
        # resolved if the "mail" module happens to be installed)
        message_model = self.env.get("mail.message")
        if res_model == "mail.message" and message_model is not None:
            message = message_model.browse(res_id)
            if message.exists() and message.model and message.res_id:
                res_model = message.model
                res_id = message.res_id
        model_obj = self.env.get(res_model)
        if model_obj is None:
            return False
        record = model_obj.browse(res_id)
        return record if record.exists() else False

    def _check_should_be_pdfa(self):
        self.ensure_one()
        is_pdf_mimetype = self.mimetype == "application/pdf"
        is_pdf_extension = (self.name or "").lower().endswith(".pdf")
        if not (is_pdf_mimetype or is_pdf_extension):
            return False
        raw_data = self._get_clean_raw_pdf()
        if not raw_data.startswith(b"%PDF") or self._is_already_pdfa3(raw_data):
            return False
        record = self._get_target_record()
        if not record or not hasattr(record, "_attachment_must_be_pdfa"):
            return False
        return record._attachment_must_be_pdfa(self)

    @api.model
    def _gs_convert_pdf_to_pdfa(self, raw_content):
        """Convert PDF raw bytes using Ghostscript."""
        if not _PROFILES_AVAILABLE:
            return raw_content, False, _MISSING_PROFILE_MSG
        temp_in = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        try:
            temp_in.write(raw_content)
            temp_in.close()
            temp_out.close()
            args = [
                "gs",
                f"--permit-file-read={RGB_PROFILE}",
                "-dPDFACompatibilityPolicy=1",
                "-sDEVICE=pdfwrite",
                "-dPDFA=3",
                "-sColorConversionStrategy=RGB",
                "-o",
                temp_out.name,
                "-c",
                f"/ICCProfile ({RGB_PROFILE}) def",
                "-f",
                str(ICC_PROFILE_PS),
                str(temp_in.name),
            ]
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=TIMEOUT_CONVERSION,
                check=False,
            )
            log_output = (result.stdout or "") + "\n" + (result.stderr or "")
            content = Path(temp_out.name).read_bytes()
            pdfa_aborted = any(marker in log_output for marker in _PDFA_ABORT_MARKERS)
            if result.returncode == 0 and content and not pdfa_aborted:
                return content, True, log_output
            if pdfa_aborted:
                log_output = (
                    "Ghostscript reported PDF/A processing was aborted "
                    "(output would not be PDF/A compliant):\n" + log_output
                )
            return raw_content, False, log_output
        except Exception as e:
            msg = f"Ghostscript conversion exception: {e}"
            _logger.exception(msg)
            return raw_content, False, msg
        finally:
            Path(temp_in.name).unlink(missing_ok=True)
            Path(temp_out.name).unlink(missing_ok=True)

    @api.model
    def _odoo_convert_pdf_to_pdfa(self, raw_content, title):
        """Convert PDF raw bytes using Odoo native PyPDF writer."""
        try:
            reader = OdooPdfFileReader(io.BytesIO(raw_content), strict=False)
            writer = OdooPdfFileWriter()
            writer.cloneReaderDocumentRoot(reader)
            writer.convert_to_pdfa()
            metadata_template = self.env.ref(
                "attachment_pdfa.pdfa3_metadata", raise_if_not_found=False
            )
            if metadata_template:
                content = self.env["ir.qweb"]._render(
                    "attachment_pdfa.pdfa3_metadata",
                    {
                        "title": title or "Document",
                        "date": fields.Date.context_today(self),
                    },
                )
                writer.add_file_metadata(content.encode("utf-8"))
            new_pdf_stream = io.BytesIO()
            writer.write(new_pdf_stream)
            return new_pdf_stream.getvalue(), True, "Odoo conversion successful."
        except Exception as e:
            msg = f"Odoo PDF/A conversion failed: {str(e)}"
            _logger.exception(msg)
            return raw_content, False, msg

    def _process_one_pdfa_conversion(self, method):
        """Process PDF/A conversion for a single attachment."""
        self.ensure_one()
        raw_data = self._get_clean_raw_pdf()
        if not raw_data or not raw_data.startswith(b"%PDF"):
            self.write({"is_pdfa_needed": False})
            return
        filename = self.name or "Document.pdf"

        if method == "odoo":
            new_raw, success, log_msg = self._odoo_convert_pdf_to_pdfa(
                raw_data, filename
            )
        elif method == "ghostscript":
            new_raw, success, log_msg = self._gs_convert_pdf_to_pdfa(raw_data)
        else:
            self.write({"is_pdfa_needed": False})
            return
        if success:
            mode = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("attachment_pdfa.mode", "replace")
            )
            if mode == "beside":
                self.write({"is_pdfa_needed": False})
                base_name = Path(filename).stem
                new_name = f"{base_name}_PDFA.pdf"
                self.create(
                    {
                        "name": new_name,
                        "raw": new_raw,
                        "mimetype": "application/pdf",
                        "res_model": self.res_model,
                        "res_id": self.res_id,
                        "is_pdfa_needed": False,
                    }
                )
            else:
                self.write(
                    {
                        "raw": new_raw,
                        "mimetype": "application/pdf",
                        "is_pdfa_needed": False,
                    }
                )
        else:
            raise UserError(
                _("PDF/A conversion failed for attachment %(name)s: %(msg)s")
                % {"name": filename, "msg": log_msg}
            )

    @staticmethod
    def _can_commit():
        """Helper to know if we can commit the current transaction or not.

        :returns: True if commit is acceptable, False otherwise.
        """
        return not tools.config["test_enable"] and not modules.module.current_test

    @api.model
    def _cron_convert_pdfa(self, batch_size=100):
        """Cron entrypoint to convert attachments."""
        method = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("attachment_pdfa.method", "ghostscript")
        )
        if method == "disable":
            return
        # Use skip_res_field_check=True to include field-backed attachments
        attachments = (
            self.sudo()
            .with_context(skip_res_field_check=True)
            .search([("is_pdfa_needed", "=", True)], limit=batch_size)
        )
        if not attachments:
            return
        errors = []
        for attachment in attachments:
            try:
                with self.env.cr.savepoint():
                    attachment._process_one_pdfa_conversion(method)
            except Exception as e:
                attachment.write({"is_pdfa_needed": False})
                errors.append(str(e))
            # Persist changes per attachment
            if self._can_commit():
                self.env.cr.commit()  # pylint: disable=invalid-commit
        remaining_count = (
            self.sudo()
            .with_context(skip_res_field_check=True)
            .search_count([("is_pdfa_needed", "=", True)])
        )
        if len(attachments) == batch_size and remaining_count:
            cron = self.env.ref(
                "attachment_pdfa.ir_cron_convert_pdfa", raise_if_not_found=False
            )
            if cron:
                cron._trigger()
        # If any conversions failed, raise the combined errors after treating all
        # attachments
        if errors:
            raise UserError(
                _(
                    "PDF/A conversion failed for %(count)s attachment(s):\n\n"
                    "%(errors)s"
                )
                % {"count": len(errors), "errors": "\n\n".join(errors)}
            )
