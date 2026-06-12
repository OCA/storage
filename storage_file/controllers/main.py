# Part of Odoo. See LICENSE file for full copyright and licensing details.

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class StorageFileController(http.Controller):
    @http.route(
        ["/storage.file/<string:slug_name_with_id>"], type="http", auth="public"
    )
    def content_common(self, slug_name_with_id, token=None, download=None, **kw):
        storage_file = request.env["storage.file"].get_from_slug_name_with_id(
            slug_name_with_id
        )
        if not storage_file.exists():
            raise NotFound()
        try:
            storage_file.check_access("read")
        except AccessError as err:
            # If you don't have access you should not know
            # that the file exists (as anon user).
            # You can inspect the traceback to see it's coming from an access error.
            raise NotFound() from err
        stream = request.env["ir.binary"]._get_stream_from(
            storage_file, field_name="data"
        )
        return stream.get_response()
