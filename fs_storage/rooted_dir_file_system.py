# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import ntpath
import posixpath

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
        # DirFileSystem joins a list or a dict of paths by calling this method
        # on each of them, so each one is already checked.
        if not isinstance(joined, str):
            return joined
        # Ensure that the path is a subpath of the root path by resolving
        # any relative paths.
        # The paths may belong to a remote filesystem, so they are normalized
        # as strings.
        if self.sep == "/":
            # A backslash is part of a name on most filesystems, but fsspec
            # turns it into a slash in local paths on Windows: the path must
            # stay inside the root under both rules.
            os_paths = (posixpath, ntpath)
        elif self.sep == "\\":
            os_paths = (ntpath,)
        else:
            raise ValueError(f"Unknown path separator: {self.sep!r}")
        for os_path in os_paths:
            rnorm = os_path.normpath(self.path)
            jnorm = os_path.normpath(joined)
            # Compare whole path components, so that a sibling such as
            # "root-backup" is outside "root". A root such as "/" already ends
            # with the separator.
            prefix = rnorm if rnorm.endswith(os_path.sep) else rnorm + os_path.sep
            if not (jnorm == rnorm or jnorm.startswith(prefix)):
                raise PermissionError(
                    f"Path {path!r} resolves to {jnorm!r} which is outside "
                    f"the root path {rnorm!r}"
                )
        return joined


register_implementation("rooted_dir", RootedDirFileSystem)
