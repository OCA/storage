# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import os

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
from odoo.tools import str2bool

_logger = logging.getLogger(__name__)


class FsFolderController(http.Controller):
    @http.route(
        "/fs_folder/get_file/<string:res_model>/<int:res_id>/<string:field_name>",
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

    @http.route(
        "/fs_folder/get_children/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def get_children(self, res_id, res_model, field_name, path=""):
        result = request.env["fs.folder.field.web.api"].get_children(
            res_id, res_model, field_name, path
        )
        if not path:
            return result
        return [{**item, "name": item["name"][len(path) + 1 :]} for item in result]

    @http.route(
        "/fs_folder/add_folder/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def add_folder(self, res_id, res_model, field_name, path, name):
        request.env["fs.folder.field.web.api"].create_folder(
            res_id, res_model, field_name, os.path.join(path, name)
        )

    @http.route(
        "/fs_folder/delete/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def delete(self, res_id, res_model, field_name, path, name):
        request.env["fs.folder.field.web.api"].delete(
            res_id, res_model, field_name, os.path.join(path, name), recursive=True
        )

    @http.route(
        "/fs_folder/move/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def move_file(self, res_id, res_model, field_name, path, origin_path, record):
        if path == origin_path:
            return
        return request.env["fs.folder.field.web.api"].rename(
            res_id,
            res_model,
            field_name,
            os.path.join(origin_path, record),
            os.path.join(path, record),
            recursive=True,
        )

    @http.route(
        "/fs_folder/copy/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def copy_file(self, res_id, res_model, field_name, path, origin_path, record):
        if path == origin_path:
            return
        return request.env["fs.folder.field.web.api"].copy_item(
            res_id,
            res_model,
            field_name,
            os.path.join(origin_path, record),
            os.path.join(path, record),
            recursive=True,
        )

    @http.route(
        "/fs_folder/rename/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def rename(self, res_id, res_model, field_name, path, name, new_name):
        request.env["fs.folder.field.web.api"].rename(
            res_id,
            res_model,
            field_name,
            os.path.join(path, name),
            os.path.join(path, new_name),
        )

    @http.route(
        "/fs_folder/upload/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def upload(self, res_id, res_model, field_name, path, name, data):
        request.env["fs.folder.field.web.api"].upload_file(
            res_id,
            res_model,
            field_name,
            path,
            name,
            data,
        )

    @http.route(
        "/fs_folder/initialize/<string:res_model>/<int:res_id>/<string:field_name>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def initialize(self, res_id, res_model, field_name):
        request.env["fs.folder.field.web.api"].initialize_field_value(
            res_id, res_model, field_name
        )
