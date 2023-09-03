# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from __future__ import annotations

from odoo.http import STATIC_CACHE_LONG, Response, Stream, request
from odoo.tools import config

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
        return cls(
            mimetype=attachment.mimetype,
            download_name=attachment.name,
            conditional=True,
            etag=attachment.checksum,
            type="fs",
            size=attachment.file_size,
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
        use_x_sendfile = self._fs_use_x_sendfile
        # The file will be closed by werkzeug...
        send_file_kwargs["use_x_sendfile"] = use_x_sendfile
        if not use_x_sendfile:
            f = self.fs_attachment.open("rb")
            res = _send_file(f, **send_file_kwargs)
        else:
            x_accel_redirect = (
                f"/{self.fs_attachment.fs_storage_code}{self.fs_attachment.fs_url_path}"
            )
            send_file_kwargs["use_x_sendfile"] = True
            res = _send_file("", **send_file_kwargs)
            # nginx specific headers
            res.headers["X-Accel-Redirect"] = x_accel_redirect
            # apache specific headers
            res.headers["X-Sendfile"] = x_accel_redirect
            res.headers["Content-Length"] = 0

        if immutable and res.cache_control:
            res.cache_control["immutable"] = None
        return res

    @classmethod
    def _check_use_x_sendfile(cls, attachment: IrAttachment) -> bool:
        return (
            config["x_sendfile"]
            and attachment.fs_url
            and attachment.fs_storage_id.use_x_sendfile_to_serve_internal_url
        )

    @property
    def _fs_use_x_sendfile(self) -> bool:
        """Return True if x-sendfile should be used to serve the file"""
        return self._check_use_x_sendfile(self.fs_attachment)
