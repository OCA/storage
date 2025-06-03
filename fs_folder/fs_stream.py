# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from __future__ import annotations

import mimetypes

import fsspec

from odoo import fields
from odoo.http import STATIC_CACHE_LONG, Response, Stream, request

try:
    from werkzeug.utils import send_file as _send_file
except ImportError:
    from odoo.tools._vendor.send_file import send_file as _send_file


class FsStream(Stream):
    fs: fsspec.AbstractFileSystem = None
    path: str = None

    @classmethod
    def from_fs_path(cls, fs: fsspec.AbstractFileSystem, path: str) -> FsStream:
        fs_entry = fs.info(path)
        if fs_entry["type"] != "file":
            raise ValueError("Content is not a file")
        mimetype = fs_entry.get("mimetype")
        filename = path.split(fs.sep)[-1]
        if not mimetype:
            mimetype = mimetypes.guess_type(filename)
            mimetype = mimetype[0] if mimetype else None
        checksum = fs.checksum(path)
        size = fs.size(path)

        return cls(
            mimetype=mimetype,
            download_name=filename,
            conditional=True,
            etag=checksum,
            type="/fs_folder_content",
            size=size,
            last_modified=fields.Datetime.now(),  # TODO should comes from fs
            fs=fs,
            path=path,
        )

    def read(self):
        if self.type == "/fs_folder_content":
            with self.fs.open(self.path, "rb") as f:
                return f.read()
        return super().read()

    def get_response(
        self,
        as_attachment=None,
        immutable=None,
        content_security_policy="default-src 'none'",
        **send_file_kwargs,
    ):
        if self.type != "/fs_folder_content":
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
        }
        # The file will be closed by werkzeug...
        send_file_kwargs["use_x_sendfile"] = False
        f = self.fs.open(self.path, "rb")
        res = _send_file(f, **send_file_kwargs)
        if immutable and res.cache_control:
            res.cache_control["immutable"] = None

        res.headers["X-Content-Type-Options"] = "nosniff"

        if content_security_policy:
            res.headers["Content-Security-Policy"] = content_security_policy

        return res
