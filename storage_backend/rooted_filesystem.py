from typing import Callable

import fsspec


# pylint: disable=method-required-super
class RootedFileSystem(fsspec.AbstractFileSystem):
    """Proxy an fsspec filesystem instance to take care of a root path
    to use as a prefix for all operations.
    """

    def __init__(
        self,
        fs,
        root_path=None,
        path_validator: Callable[[fsspec.AbstractFileSystem, str, str], None] = None,
    ):
        """Initialize the proxy filesystem.

        :param fs: the underlying filesystem instance to proxy to
        :param root_path: the root path to use as a prefix for all operations
        :param path_validator: a callable that will be called to validate
            the path before it is used in any operation. It should raise an
            exception if the path is not valid.
            It will be called with 3 arguments:
            - the AbstractFileSystem instance
            - the resolved path to validate
            - the root path that was used to resolve the path

        """
        self.fs = fs
        self.root_path = root_path or ""
        self.path_validator = path_validator
        self.__fs_initial_info = self.fs.info
        self.fs.info = self.info

    def _apply_root_path(self, path):
        if isinstance(path, list):
            return [self._apply_root_path(p) for p in path]
        path = self.fs._strip_protocol(path)
        if not self.root_path or path.startswith(self.root_path):
            return path
        path = f"{self.root_path}{self.sep}{path.lstrip(self.sep)}"
        if self.path_validator:
            self.path_validator(self.fs, path, self.root_path)
        return path

    # from here we implement all the public methods of fsspec.AbstractFileSystem
    # that we want to proxy to the underlying filesystem instance
    def cat(self, path, start=None, end=None, **kwargs):
        return self.fs.cat(self._apply_root_path(path), start=start, end=end, **kwargs)

    def cat_file(self, path, start=None, end=None, **kwargs):
        return self.fs.cat_file(
            self._apply_root_path(path), start=start, end=end, **kwargs
        )

    def cat_ranges(
        self, paths, starts, ends, max_gap=None, on_error="return", **kwargs
    ):
        return self.fs.cat_ranges(
            paths, starts, ends, max_gap=max_gap, on_error=on_error, **kwargs
        )

    def checksum(self, path, **kwargs):
        return self.fs.checksum(self._apply_root_path(path), **kwargs)

    def copy(self, path1, path2, **kwargs):
        return self.fs.copy(
            self._apply_root_path(path1), self._apply_root_path(path2), **kwargs
        )

    def cp(self, path1, path2, **kwargs):
        return self.fs.cp(
            self._apply_root_path(path1), self._apply_root_path(path2), **kwargs
        )

    def cp_file(self, path1, path2, **kwargs):
        return self.fs.cp_file(
            self._apply_root_path(path1), self._apply_root_path(path2), **kwargs
        )

    def create(self, path, **kwargs):
        return self.fs.create(self._apply_root_path(path), **kwargs)

    def delete(self, path, recursive=False, **kwargs):
        return self.fs.delete(
            self._apply_root_path(path), recursive=recursive, **kwargs
        )

    def disk_usage(self, path, total=True, maxdepth=None, **kwargs):
        return self.fs.disk_usage(
            self._apply_root_path(path), total=total, maxdepth=maxdepth, **kwargs
        )

    def download(self, rpath, lpath, recursive=False, **kwargs):
        return self.fs.download(
            self._apply_root_path(rpath), lpath, recursive=recursive, **kwargs
        )

    def du(self, path, total=True, maxdepth=None, **kwargs):
        return self.fs.du(
            self._apply_root_path(path), total=total, maxdepth=maxdepth, **kwargs
        )

    def exists(self, path, **kwargs):
        return self.fs.exists(self._apply_root_path(path), **kwargs)

    def expand_path(self, path, **kwargs):
        return self.fs.expand_path(self._apply_root_path(path), **kwargs)

    def find(self, path, maxdepth=None, withdirs=False, **kwargs):
        return self.fs.find(
            self._apply_root_path(path), maxdepth=maxdepth, withdirs=withdirs, **kwargs
        )

    def get(self, rpath, lpath, recursive=False, **kwargs):
        return self.fs.get(
            self._apply_root_path(rpath), lpath, recursive=recursive, **kwargs
        )

    def glob(self, path, **kwargs):
        return self.fs.glob(self._apply_root_path(path), **kwargs)

    def head(self, path, size=1024, **kwargs):
        return self.fs.head(self._apply_root_path(path), size=size, **kwargs)

    def info(self, path, **kwargs):
        info = self.__fs_initial_info(self._apply_root_path(path), **kwargs)
        if info:
            info["path"] = info["path"].replace(self.root_path, "")
        return info

    def invalidate_cache(self, path=None):
        return self.fs.invalidate_cache(self._apply_root_path(path))

    def isdir(self, path):
        return self.fs.isdir(self._apply_root_path(path))

    def isfile(self, path):
        return self.fs.isfile(self._apply_root_path(path))

    def lexists(self, path, **kwargs):
        return self.fs.lexists(self._apply_root_path(path), **kwargs)

    def listdir(self, path, detail=True, **kwargs):
        return self.fs.listdir(self._apply_root_path(path), detail=detail, **kwargs)

    def ls(self, path, detail=True, **kwargs):
        result = self.fs.ls(self._apply_root_path(path), detail=detail, **kwargs)
        if not detail:
            # remove root path from paths
            root_path = self.root_path.rstrip(self.fs.sep) + self.fs.sep
            result = [p.replace(root_path, "") for p in result]
        return result

    def makedirs(self, path, exist_ok=False):
        return self.fs.makedirs(self._apply_root_path(path), exist_ok=exist_ok)

    def mkdir(self, path, create_parents=True, **kwargs):
        return self.fs.mkdir(
            self._apply_root_path(path), create_parents=create_parents, **kwargs
        )

    def mkdirs(self, path, exist_ok=False):
        return self.fs.mkdirs(self._apply_root_path(path), exist_ok=exist_ok)

    def modified(self, path):
        return self.fs.modified(self._apply_root_path(path))

    def move(self, path1, path2, **kwargs):
        return self.fs.move(
            self._apply_root_path(path1), self._apply_root_path(path2), **kwargs
        )

    def mv(self, path1, path2, recursive=False, maxdepth=None, **kwargs):
        return self.fs.mv(
            self._apply_root_path(path1),
            self._apply_root_path(path2),
            recursive=recursive,
            maxdepth=maxdepth,
            **kwargs,
        )

    def open(self, path, mode="rb", block_size=None, cache_options=None, **kwargs):
        return self.fs.open(
            self._apply_root_path(path),
            mode=mode,
            block_size=block_size,
            cache_options=cache_options,
            **kwargs,
        )

    def pipe(self, path, value=None, **kwargs):
        return self.fs.pipe(self._apply_root_path(path), value=value, **kwargs)

    def pipe_file(self, path, value, **kwargs):
        return self.fs.pipe_file(self._apply_root_path(path), value, **kwargs)

    def put(self, lpath, rpath, recursive=False, **kwargs):
        return self.fs.put(
            lpath, self._apply_root_path(rpath), recursive=recursive, **kwargs
        )

    def put_file(self, lpath, rpath, **kwargs):
        return self.fs.put_file(lpath, self._apply_root_path(rpath), **kwargs)

    def read_block(self, fn, offset, length, delimiter=None):
        return self.fs.read_block(
            self._apply_root_path(fn), offset, length, delimiter=delimiter
        )

    def read_bytes(self, path, start=None, end=None, delimiter=None):
        return self.fs.read_bytes(
            self._apply_root_path(path), start=start, end=end, delimiter=delimiter
        )

    def read_text(self, path, encoding=None, errors=None, newline=None, **kwargs):
        return self.fs.read_text(
            self._apply_root_path(path),
            encoding=encoding,
            errors=errors,
            newline=newline,
            **kwargs,
        )

    def rename(self, path1, path2, **kwargs):
        return self.fs.rename(
            self._apply_root_path(path1), self._apply_root_path(path2), **kwargs
        )

    def rm(self, path, recursive=False, maxdepth=None):
        return self.fs.rm(
            self._apply_root_path(path), recursive=recursive, maxdepth=maxdepth
        )

    def rm_file(self, path):
        return self.fs.rm_file(self._apply_root_path(path))

    def rmdir(self, path):
        return self.fs.rmdir(self._apply_root_path(path))

    def sign(self, path, expiration=100, **kwargs):
        return self.fs.sign(
            self._apply_root_path(path), expiration=expiration, **kwargs
        )

    def size(self, path):
        return self.fs.size(self._apply_root_path(path))

    def sizes(self, paths):
        return self.fs.sizes(self._apply_root_path(paths))

    def stat(self, path, **kwargs):
        return self.fs.stat(self._apply_root_path(path), **kwargs)

    def tail(self, path, size=1024):
        return self.fs.tail(self._apply_root_path(path), size=size)

    def touch(self, path, **kwargs):
        return self.fs.touch(self._apply_root_path(path), **kwargs)

    def ukey(self, path):
        return self.fs.ukey(self._apply_root_path(path))

    def upload(self, lpath, rpath, recursive=False, **kwargs):
        return self.fs.upload(
            lpath, self._apply_root_path(rpath), recursive=recursive, **kwargs
        )

    def walk(self, path, **kwargs):
        return self.fs.walk(self._apply_root_path(path), **kwargs)

    def write_bytes(self, path, value, **kwargs):
        return self.fs.write_bytes(self._apply_root_path(path), value, **kwargs)

    def write_text(
        self, path, value, encoding=None, errors=None, newline=None, **kwargs
    ):
        return self.fs.write_text(
            self._apply_root_path(path),
            value,
            encoding=encoding,
            errors=errors,
            newline=newline,
            **kwargs,
        )
