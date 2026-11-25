This module extends Odoo's attachment system to support background conversion of PDF files to the **PDF/A-3** format.

This module provides a flexible framework to automate PDF to PDF/A-3 conversion via an asynchronous background cron:

* **Opt-in via Mixin**: Rather than blindly converting all system PDFs, models must opt-in by inheriting `attachment.pdfa.mixin` and implementing conditional rules via `_attachment_must_be_pdfa(attachment)`.
* **Cron**: Attachments requiring conversion are flagged via the `is_pdfa_needed` field on `ir.attachment` and processed by a background cron.
* **Flexible Storage Strategy**: Configurable options allow converted PDF/A files to either replace the original attachments or be saved alongside them as new attachments.
* **Pluggable Engine**: Offers conversion via **Ghostscript** or native **Odoo** PDF writer.
