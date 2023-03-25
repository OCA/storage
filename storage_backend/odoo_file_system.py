# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from fsspec.registry import register_implementation

from .rooted_dir_file_system import RootedDirFileSystem


class OdooFileSystem(RootedDirFileSystem):
    """A directory-based filesystem for Odoo.

    This filesystem is mounted from a specific subdirectory of the Odoo
    filestore directory.

    It extends the RootedDirFileSystem to avoid going outside the
    specific subdirectory nor the Odoo filestore directory.
    """


register_implementation("odoofs", OdooFileSystem)
