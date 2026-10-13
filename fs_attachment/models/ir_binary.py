# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from mimetypes import guess_extension

from odoo import models
from odoo.tools.mimetypes import get_extension

_logger = logging.getLogger(__name__)


class IrBinary(models.AbstractModel):
    _inherit = "ir.binary"

    # The streams of the attachments stored into a filesystem storage are
    # provided by ir.attachment._to_http_stream (see FsStream). This method is
    # called by ir.binary._record_to_stream for the attachments and the binary
    # fields stored as attachment.

    def _get_stream_from(
        self,
        record,
        field_name="raw",
        filename=None,
        filename_field="name",
        mimetype=None,
        default_mimetype="application/octet-stream",
    ):
        stream = super()._get_stream_from(
            record,
            field_name=field_name,
            filename=filename,
            filename_field=filename_field,
            mimetype=mimetype,
            default_mimetype=default_mimetype,
        )
        if stream.type == "fs":
            # same as the base implementation for 'data' and 'path' streams
            if mimetype:
                stream.mimetype = mimetype
            elif not stream.mimetype:
                stream.mimetype = default_mimetype

            if filename:
                stream.download_name = filename
            elif filename_field in record:
                field = record._fields[filename_field]
                if record.sudo(False).has_field_access(field, "read"):
                    stream.download_name = record[filename_field]
            if not stream.download_name:
                stream.download_name = f"{record._table}-{record.id}-{field_name}"

            stream.download_name = stream.download_name.replace("\n", "_").replace(
                "\r", "_"
            )
            ext = get_extension(stream.download_name)
            stream.download_name = stream.download_name.removesuffix(ext)[:100] + (
                ext or guess_extension(stream.mimetype) or ""
            )
        return stream

    def _get_image_stream_from(
        self,
        record,
        field_name="raw",
        filename=None,
        filename_field="name",
        mimetype=None,
        default_mimetype="image/png",
        placeholder=None,
        width=0,
        height=0,
        crop=False,
        quality=0,
    ):
        # Fields provided by the module fs_file / fs_image are not binary
        # fields. Their content is served from the related attachment.
        if record._name != "ir.attachment" and field_name:
            field_def = record._fields.get(field_name)
            if field_def and field_def.type in ("fs_image", "fs_file"):
                value = record[field_name]
                if value:
                    record = value.attachment
                    field_name = "raw"
        return super()._get_image_stream_from(
            record,
            field_name=field_name,
            filename=filename,
            filename_field=filename_field,
            mimetype=mimetype,
            default_mimetype=default_mimetype,
            placeholder=placeholder,
            width=width,
            height=height,
            crop=crop,
            quality=quality,
        )
