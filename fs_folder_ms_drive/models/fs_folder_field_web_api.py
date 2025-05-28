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
        root_fs = self.env["fs.storage"].sudo()._get_root_filesystem(fs)
        info = fs.info(path, details=True)
        item_info = info.get("item_info")
        rooted_file_path = fs.sep.join((fs.path, path))
        return root_fs.preview(rooted_file_path, item_id=item_info.get("id"))
