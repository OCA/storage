# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from __future__ import annotations

from odoo.http import STATIC_CACHE_LONG, Response, Stream, request

from .models.ir_attachment import IrAttachment

try:
    from werkzeug.utils import send_file as _send_file
except ImportError:
    from odoo.tools._vendor.send_file import send_file as _send_file


class FsStream(Stream):
    fs_attachment = None

    @classmethod
    def from_fs_attachment(cls, attachment: IrAttachment) -> FsStream:
        attachment.ensure_one()
        if not attachment.fs_filename:
            raise ValueError("Attachment is not stored into a filesystem storage")
        fs_info = attachment.fs_storage_id.root_fs.info(attachment.fs_filename)
        return cls(
            mimetype=attachment.mimetype,
            download_name=attachment.name,
            conditional=True,
            etag=attachment.checksum,
            type="fs",
            size=fs_info["size"],
            last_modified=attachment["__last_update"],
            fs_attachment=attachment,
        )

    def read(self):
        if self.type == "fs":
            with self.fs_attachment.open("rb") as f:
                return f.read()
        return super().read()

    def get_response(self, as_attachment=None, immutable=None, **send_file_kwargs):
        if self.type != "fs":
            return super().get_response(
                as_attachment=as_attachment, immutable=immutable, **send_file_kwargs
            )
        if as_attachment is None:
            as_attachment = self.as_attachment
        if immutable is None:
            immutable = self.immutable
        send_file_kwargs = {
            "mimetype": self.mimetype,
            "as_attachment": as_attachment,
            "download_name": self.download_name,
            "conditional": self.conditional,
            "etag": self.etag,
            "last_modified": self.last_modified,
            "max_age": STATIC_CACHE_LONG if immutable else self.max_age,
            "environ": request.httprequest.environ,
            "response_class": Response,
            **send_file_kwargs,
        }
        # The file will be closed by werkzeug...
        f = self.fs_attachment.open("rb")
        res = _send_file(f, **send_file_kwargs)
        if immutable and res.cache_control:
            res.cache_control["immutable"] = None
        return res
