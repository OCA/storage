from odoo import fields, models


class AttachmentContent(models.Model):
    _name = "ir.attachment.content"
    _rec_name = "checksum"
    _description = "Attachment content by hash"

    checksum = fields.Char(
        string="Checksum/SHA1",
        help="Checksum in the shape 2a/2a...\n",
        index=True,
        readonly=True,
        required=True,
    )
    db_datas = fields.Binary(
        string="Database Data",
        attachment=False,
    )

    _sql_constraints = [
        (
            "checksum_uniq",
            "unique(checksum)",
            "The checksum of the file must be unique!",
        ),
    ]

    def search_by_checksum(self, fname):
        """Get Attachment content, searching by `fname`.

        Note that `fname` is the relative path of the attachment
        as it would be saved by the core, for example 2a/2a...,
        this is the same value that we store
        in field `ir.attachment.content.checksum`.
        """
        attachment_content = self.env["ir.attachment.content"].search(
            [
                ("checksum", "=", fname),
            ],
            limit=1,
        )
        return attachment_content
