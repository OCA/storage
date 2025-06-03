# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import logging
import typing

import fsspec

from odoo.addons.fs_storage.rooted_dir_file_system import RootedDirFileSystem

if typing.TYPE_CHECKING:
    from ..fields import FsContentValue, FsFolder

from odoo import models

_logger = logging.getLogger(__name__)


class FsFolderFielValueAdapter(models.AbstractModel):
    """Folder field value adapter

    This class provides utility methods to handle the value of a fs_folder field.
    It's used by the fs_folder field to convert the value of the field to a stored value
    and vice versa. It also provides utility methods to access the content of the
    folder.

    This class has been designed to be inherited by other classes to provide custom
    behavior for the fs_folder field value.
    """

    _name = "fs.folder.field.value.adapter"
    _description = "Folder field value adapter"

    def _created_folder_name_to_stored_value(
        self, path: str, storage_code: str, fs: fsspec.AbstractFileSystem
    ) -> str:
        """
        Convert the folder name to the stored value.
        """
        return f"{storage_code}://{path.lstrip('/')}"

    def _parse_fs_folder_value(
        self, stored_value: str, field: "FsFolder", record: models.BaseModel
    ) -> tuple[str, str]:
        """
        Parse the stored value of a fs_folder field.

        return (ref, storage_code)
        """
        ref, storage_code = None, None
        if stored_value:
            partition = stored_value.partition("://")
            ref, storage_code = partition[2], partition[0]
        return ref, storage_code

    def _get_fs_for_fs_folder_field(
        self, value: "FsContentValue"
    ) -> RootedDirFileSystem:
        """
        Return a RootedDirFileSystem for the given fs_folder field value.

        This ensure that only content of the folder can be accessed.
        """
        if not value.stored_value:
            return None
        fs = value._env["fs.storage"].get_fs_by_code(value.storage_code)
        return self._get_rooted_dir_file_system(value, fs)

    def _get_rooted_dir_file_system(
        self, value: "FsContentValue", fs: fsspec.AbstractFileSystem
    ) -> RootedDirFileSystem:
        return RootedDirFileSystem(path=value.ref, fs=fs)
