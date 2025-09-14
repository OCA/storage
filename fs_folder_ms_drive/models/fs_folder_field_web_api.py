# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class FsFolderFieldWebApi(models.AbstractModel):
    _inherit = "fs.folder.field.web.api"

    def _is_ms_drive(self, fs):
        """
        Check if the field is a Microsoft Drive field.
        """
        if not fs:
            return False
        protocol = self.env["fs.storage"].sudo()._get_root_filesystem(fs).protocol
        if isinstance(protocol, tuple | list):
            protocol = protocol[0]
        return protocol == "msgd"

    def get_root_fs_and_path(self, res_id, res_model, field_name):
        """
        Get the root filesystem and path to for a given record and field.
        """
        fs = self._get_fs(res_id, res_model, field_name)
        if not self._is_ms_drive(fs):
            return None, None
        parent_paths = [fs.path] if fs.path else []
        root_fs = fs
        while fs := getattr(fs, "fs", None):
            if hasattr(fs, "path") and fs.path:
                parent_paths.insert(0, fs.path)
            root_fs = fs
        return root_fs, root_fs.sep.join(parent_paths)

    @api.model
    def get_ms_drive_url(self, res_id, res_model, field_name, path=None):
        """
        Get the MS Drive URL for a given record and field.
        """
        self._check_field_access(res_id, res_model, field_name, "read")
        path = path or ""
        fs = self._get_fs(res_id, res_model, field_name)
        if not self._is_ms_drive(fs):
            return None
        info = fs.info(path, details=True)
        item_info = info.get("item_info")
        return item_info.get("webUrl")

    @api.model
    def get_ms_drive_download_url(self, res_id, res_model, field_name, path=None):
        """
        Get the MS Drive download URL for a given record and field.
        """
        self._check_field_access(res_id, res_model, field_name, "read")
        path = path or ""
        fs = self._get_fs(res_id, res_model, field_name)
        if not self._is_ms_drive(fs):
            return None
        info = fs.info(path, details=True)
        item_info = info.get("item_info")
        return item_info.get("@microsoft.graph.downloadUrl")

    @api.model
    def get_ms_drive_preview_url(self, res_id, res_model, field_name, path=None):
        """
        Get the MS Drive preview URL for a given record and field.
        """
        self._check_field_access(res_id, res_model, field_name, "read")
        path = path or ""
        fs = self._get_fs(res_id, res_model, field_name)
        if not self._is_ms_drive(fs):
            return None
        root_fs, parent_path = self.get_root_fs_and_path(res_id, res_model, field_name)
        info = fs.info(path, details=True)
        item_info = info.get("item_info")
        rooted_file_path = fs.sep.join((parent_path, path))
        return root_fs.preview(rooted_file_path, item_id=item_info.get("id"))

    @api.model
    def is_ms_drive(self, res_id, res_model, field_name):
        """
        Check if the field is a Microsoft Drive field.
        """
        self._check_field_access(res_id, res_model, field_name, "read")
        field, record = self._get_field_and_record(res_id, res_model, field_name)
        fs = None
        if field.type == "fs_folder":
            value = record[field_name]
            if value:
                fs = value.fs
            else:
                fs = field.get_fs(record)
        return fs and self._is_ms_drive(fs)
