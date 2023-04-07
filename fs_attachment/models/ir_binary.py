# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import models

from ..fs_stream import FsStream

_logger = logging.getLogger(__name__)


class IrBinary(models.AbstractModel):

    _inherit = "ir.binary"

    def _record_to_stream(self, record, field_name):
        # Extend base implementation to support attachment stored into a
        # filesystem storage
        fs_attachment = None
        if record._name == "ir.attachment" and record.fs_filename:
            fs_attachment = record
        record.check_field_access_rights("read", [field_name])
        field_def = record._fields[field_name]
        if field_def.attachment and not field_def.compute and not field_def.related:
            field_attachment = (
                self.env["ir.attachment"]
                .sudo()
                .search(
                    domain=[
                        ("res_model", "=", record._name),
                        ("res_id", "=", record.id),
                        ("res_field", "=", field_name),
                    ],
                    limit=1,
                )
            )
            if field_attachment.fs_filename:
                fs_attachment = field_attachment
        if fs_attachment:
            return FsStream.from_fs_attachment(fs_attachment)
        return super()._record_to_stream(record, field_name)
