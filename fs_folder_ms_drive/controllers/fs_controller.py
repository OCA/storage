# Part of Odoo. See LICENSE file for full copyright and licensing details.
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


class FsController(http.Controller):
    @http.route(
        "/fs_folder_ms_drive/get_ms_drive_url/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def get_ms_drive_url(self, res_id, res_model, field_name, path=None):
        response = request.env["fs.folder.field.web.api"].get_ms_drive_url(
            res_id, res_model, field_name, path
        )
        if not response:
            raise NotFound()
        return response

    @http.route(
        "/fs_folder_ms_drive/get_ms_drive_download_url/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def get_ms_drive_download_url(self, res_id, res_model, field_name, path=None):
        response = request.env["fs.folder.field.web.api"].get_ms_drive_download_url(
            res_id, res_model, field_name, path
        )
        if not response:
            raise NotFound()
        return response

    @http.route(
        "/fs_folder_ms_drive/get_ms_drive_preview_url/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def get_ms_drive_preview_url(self, res_id, res_model, field_name, path=None):
        response = request.env["fs.folder.field.web.api"].get_ms_drive_preview_url(
            res_id, res_model, field_name, path
        )
        if not response:
            raise NotFound()
        return response

    @http.route(
        "/fs_folder_ms_drive/is_ms_drive/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def is_ms_drive(self, res_id, res_model, field_name):
        response = request.env["fs.folder.field.web.api"].is_ms_drive(
            res_id, res_model, field_name
        )
        return {"is_ms_drive": response}
