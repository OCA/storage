# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

import werkzeug.utils
import werkzeug.wrappers

from odoo import http
from odoo.http import request


class StorageFileController(http.Controller):
    @http.route(
        ["/storage.file/<string:slug_name_with_id>"], type="http", auth="public"
    )
    def content_common(self, slug_name_with_id, token=None, download=None, **kw):
        storage_file = request.env["storage.file"].get_from_slug_name_with_id(
            slug_name_with_id
        )
        status, headers, content = request.env["ir.http"].binary_content(
            model=storage_file._name,
            id=storage_file.id,
            field="data",
            filename_field="name",
            download=download,
        )
        if status == 304:
            response = werkzeug.wrappers.Response(status=status, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200:
            response = request.not_found()
        else:
            content_base64 = base64.b64decode(content)
            headers.append(("Content-Length", len(content_base64)))
            response = request.make_response(content_base64, headers)
        if token:
            response.set_cookie("fileToken", token)
        return response
