# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import base64
import logging
import urllib

import fsspec
from werkzeug import Response

from odoo import _, api, models
from odoo.exceptions import AccessError

from ..fs_stream import FsStream

_logger = logging.getLogger(__name__)


class FsFolderFieldWebApi(models.AbstractModel):
    _name = "fs.folder.field.web.api"
    _description = "Abstract model providing the required api for the FsFolser "
    "field widget"

    @api.model
    def _check_field_access(self, res_id, res_model, field_name, access):
        """
        Check the access rights on the given field.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param access: the access rights to check
        """
        if res_model not in self.env:
            raise AccessError(_("Unknown model"))
        record = self.env[res_model].browse(res_id)
        if field_name not in record._fields:
            raise AccessError(_("Unknown field"))
        record.check_access(access)

    @api.model
    def _get_field_and_record(self, res_id, res_model, field_name, **kwargs):
        """
        Return the field and the record containing the field.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :return: the field
        """
        try:
            record = self.env[res_model].browse(res_id)
            field = record._fields[field_name]
        except KeyError as err:
            _logger.exception(
                "Enable to find the field %s on the model %s",
                field_name,
                res_model,
            )
            raise ValueError("The field is not an external filesystem field.") from err
        return field, record

    @api.model
    def _get_fs(
        self, res_id, res_model, field_name, **kwargs
    ) -> fsspec.AbstractFileSystem:
        """
        Return the filesystem of the given item.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :return: the filesystem
        """
        field, record = self._get_field_and_record(res_id, res_model, field_name)
        fs = None
        if field.type == "fs_folder":
            fs = record[field_name].fs
        if not fs:
            raise ValueError(_("The field is not an external filesystem field."))
        return fs

    @api.model
    def initialize_field_value(self, res_id, res_model, field_name, **kwargs) -> None:
        """
        Initialize the value of the field.
        """
        _field, record = self._get_field_and_record(res_id, res_model, field_name)
        record[field_name].initialize()

    @api.model
    def get_children(self, res_id, res_model, field_name, path, **kwargs) -> list[dict]:
        """
        Return the children of the given item.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param path: the path of the item
        :return: a list of children items
        """
        self._check_field_access(res_id, res_model, field_name, "read")
        fs = self._get_fs(res_id, res_model, field_name)
        return fs.ls(path, detail=True)

    @api.model
    def get_root(self, res_id, res_model, field_name, **kwargs) -> dict:
        """
        Return the root of the filesystem.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :return: the root of the filesystem
        """
        self._check_field_access(res_id, res_model, field_name, "read")
        fs = self._get_fs(res_id, res_model, field_name)
        return fs.info("/")

    @api.model
    def rename(self, res_id, res_model, field_name, path, new_path, **kwargs) -> None:
        """
        Rename the given item.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param name: the name of the item to rename
        :return: the new reference
        """
        self._check_field_access(res_id, res_model, field_name, "write")
        fs = self._get_fs(res_id, res_model, field_name)
        fs.rename(path, new_path)

    @api.model
    def create_folder(self, res_id, res_model, field_name, path, **kwargs) -> None:
        """
        Create a folder at the given path.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param path: the path of the folder to create
        """
        self._check_field_access(res_id, res_model, field_name, "write")
        fs = self._get_fs(res_id, res_model, field_name)
        fs.mkdir(path)

    @api.model
    def upload_file(
        self,
        res_id,
        res_model,
        field_name,
        path,
        file_name,
        file_data,
        mimetype=None,
        **kwargs,
    ) -> None:
        """
        Upload a file to the given item.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param parent_path: the path of the parent item
        :param name: the name of the file
        :param content: the content of the file (b64 encoded)
        :param mimetype: the mimetype of the file
        :return: the reference of the uploaded file
        """
        self._check_field_access(res_id, res_model, field_name, "write")
        file_data = base64.b64decode(file_data)
        fs = self._get_fs(res_id, res_model, field_name)
        full_path = f"{path}{fs.sep or '/'}{file_name}"
        fs.touch(full_path)
        fs.pipe_file(full_path, file_data)

    @api.model
    def update_content(
        self, res_id, res_model, field_name, path, file_data, **kwargs
    ) -> None:
        """
        Update the content of the given item.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param path: the path of the item
        :param new_content: the new content of the item (b64 encoded)
        """
        self._check_field_access(res_id, res_model, field_name, "write")
        file_data = base64.b64decode(file_data)
        fs = self._get_fs(res_id, res_model, field_name)
        fs.pipe_file(path, file_data)

    @api.model
    def copy_item(
        self,
        res_id,
        res_model,
        field_name,
        path,
        new_path,
        recursive=False,
        **kwargs,
    ) -> None:
        """
        Copy the fs item

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param path: the path of the item
        :param new_path: the new path of the item
        """
        self._check_field_access(res_id, res_model, field_name, "write")
        fs = self._get_fs(res_id, res_model, field_name)
        fs.copy(path, new_path, recursive=recursive)

    @api.model
    def delete(
        self, res_id, res_model, field_name, path, recursive=False, **kwargs
    ) -> None:
        """
        Delete the given item.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param path: the path of the item
        """
        self._check_field_access(res_id, res_model, field_name, "write")
        fs = self._get_fs(res_id, res_model, field_name)
        fs.rm(path, recursive=recursive)

    @api.model
    def get_url_for_preview(self, res_id, res_model, field_name, path, **kwargs) -> str:
        """
        Return the preview url of the given item.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param path: the path of the item
        :return: the preview url
        """
        self._check_field_access(res_id, res_model, field_name, "read")
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        query_params = urllib.parse.urlencode({"path": path})
        return (
            f"{base_url}/fs_folder/get_file/{res_model}/{res_id}/{field_name}?"
            f"{query_params}"
        )

    @api.model
    def get_url_for_download(
        self, res_id, res_model, field_name, path, **kwargs
    ) -> str:
        """
        Return the preview url of the given item.

        :param res_id: the id of the record containing the field
        :param res_model: the model of the record containing the field
        :param field_name: the name of the field
        :param path: the path of the item
        :return: the preview url
        """
        url = self.get_url_for_preview(res_id, res_model, field_name, path, **kwargs)
        return f"{url}&download=1"

    @api.model
    def _get_http_stream_response(
        self, res_id, res_model, field_name, path, download=False, **kwargs
    ) -> Response:
        """ """
        self._check_field_access(res_id, res_model, field_name, "read")
        try:
            fs = self._get_fs(res_id, res_model, field_name)
            return FsStream.from_fs_path(fs=fs, path=path).get_response(
                as_attachment=download
            )
        except Exception:
            _logger.exception(
                "Enable to return a file stream for the requested field and path ,"
                "(%s(%s).%s/%s)",
                res_model,
                field_name,
                res_id,
                path,
            )
