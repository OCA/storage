# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import posixpath
from pathlib import PurePosixPath

from fsspec.implementations.dirfs import DirFileSystem
from fsspec.registry import register_implementation


class RootedDirFileSystem(DirFileSystem):
    """A directory-based filesystem that uses path as a root.

    The main purpose of this filesystem is to ensure that paths are always
    a sub path of the initial path. IOW, it is not possible to go outside
    the initial path. That's the only difference with the DirFileSystem provided
    by fsspec.

    This one should be provided by fsspec itself. We should propose a PR.
    """

    def _join(self, path):
        joined = super()._join(path)
        # Ensure that the path is a subpath of the root path by resolving
        # any relative paths.

        root = PurePosixPath(self.path).as_posix()
        rnorm = posixpath.normpath(root)

        jnorm = posixpath.normpath(joined or ".")

        if not (jnorm == rnorm or jnorm.startswith(rnorm + "/")):
            raise PermissionError(
                f"Path {path!r} resolves to {jnorm!r} which is outside "
                f"the root path {rnorm!r}"
            )

        return joined


register_implementation("rooted_dir", RootedDirFileSystem)
