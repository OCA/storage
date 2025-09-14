# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import fsspec

from odoo import models

from odoo.addons.fs_folder.fields import FsFolder


class FsFolderFieldValueAdapter(models.AbstractModel):
    _inherit = "fs.folder.field.value.adapter"

    def _is_msgraph_folder(self, fs: fsspec.AbstractFileSystem) -> bool:
        """
        Check if the filesystem is a Microsoft Graph folder.
        """
        protocols = self.env["fs.storage"].sudo()._get_root_filesystem(fs).protocol
        if not isinstance(protocols, tuple | list):
            protocols = [protocols]
        return "msgd" in protocols

    def _created_folder_name_to_stored_value(
        self, path: str, storage_code: str, fs: fsspec.AbstractFileSystem
    ) -> str:
        """
        Convert the folder name to the stored value.
        """
        if self._is_msgraph_folder(fs):
            info = fs.info(path, details=False)
            return f"{storage_code}://{info['id']}"
        return super()._created_folder_name_to_stored_value(path, storage_code, fs)

    def _parse_fs_folder_value(
        self, stored_value: str, field: FsFolder, record: models.BaseModel
    ) -> tuple[str, str]:
        """
        Parse the stored value of a fs_folder field.

        return (ref, storage_code)
        """
        ref, storage_code = super()._parse_fs_folder_value(stored_value, field, record)
        if ref:
            fs = record.env["fs.storage"].sudo().get_fs_by_code(storage_code)
            if (
                self._is_msgraph_folder(fs)
                and self.env.user.microsoft_drive_status == "connected"
            ):
                fs_info = fs.info(path=ref, item_id=ref, details=False)
                ref = fs_info.get("name")
        return ref, storage_code
