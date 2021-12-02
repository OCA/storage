from odoo import fields, models


class AttachmentContent(models.Model):
    _name = "ir.attachment.content"
    _rec_name = "checksum"
    _description = "Attachment content by hash"

    checksum = fields.Char("Checksum/SHA1", index=True, readonly=True, required=True)
    db_datas = fields.Binary("Database Data")

    _sql_constraints = [
        (
            "checksum_uniq",
            "unique(checksum)",
            "The checksum of the file must be unique !",
        )
    ]
