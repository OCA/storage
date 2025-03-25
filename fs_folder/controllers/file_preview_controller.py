# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
from odoo.tools import str2bool

_logger = logging.getLogger(__name__)


class CrmController(http.Controller):
    @http.route(
        "/fs_field/get_file/<string:res_model>/<int:res_id>/<string:field_name>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def get_file(self, res_id, res_model, field_name, path, download=False, **kwargs):
        download = str2bool(download)
        response = request.env["fs.folder.field.web.api"]._get_http_stream_response(
            res_id, res_model, field_name, path, download, **kwargs
        )
        if not response:
            raise NotFound()
        return response
