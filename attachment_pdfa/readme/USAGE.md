To use this module:

1. Create or generate a PDF attachment on a record whose model implements `attachment.pdfa.mixin` (and where `_attachment_must_be_pdfa(attachment)` evaluates to `True`).
2. The attachment automatically flags `is_pdfa_needed = True`.
3. The scheduled cron processes pending attachments in the background, updating or creating attachments according to your configured storage strategy.
