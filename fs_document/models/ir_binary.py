# Copyright (c) 2024 ERP|OPEN <https://www.erpopen.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.fs_attachment.fs_stream import FsStream


class IrBinary(models.AbstractModel):
    _inherit = "ir.binary"

    def _record_to_stream(self, record, field_name):
        # Extend base implementation to support attachment stored into a
        # filesystem storage
        if (
            record._name == "documents.document"
            and field_name in ("raw", "datas", "db_datas")
            and record.attachment_id.fs_filename
        ):
            return FsStream.from_fs_attachment(record.attachment_id.sudo())
        return super()._record_to_stream(record, field_name)
