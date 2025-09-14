# Copyright 2024 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import threading
import time
import typing
from functools import partial

import fsspec

from odoo import SUPERUSER_ID, api, fields, models, registry
from odoo.tools.misc import SENTINEL, Sentinel
from odoo.tools.sql import pg_varchar

from odoo.addons.fs_storage.rooted_dir_file_system import RootedDirFileSystem

from .models.fs_storage import FsStorage


class FsContentValue:
    def __init__(
        self, stored_value: str | None, field: fields.Field, record: models.BaseModel
    ):
        self._stored_value: str = stored_value
        self._field: fields.Field = field
        self._record: models.BaseModel = record
        self._fs: fsspec.AbstractFileSystem | Sentinel = SENTINEL
        self._env = record.env
        self._value_adapter = record.env["fs.folder.field.value.adapter"]
        self._ref, self._storage_code = self._value_adapter._parse_fs_folder_value(
            self._stored_value, self._field, self._record
        )

    @property
    def stored_value(self):
        """
        The value stored in the database.
        """
        return self._stored_value

    @property
    def ref(self):
        """
        The reference of the folder in the filesystem.

        Bu default this is the full path of the folder in the filesystem.
        Nevertheless this can be customized by the value adapter to store
        an immutable reference if the fileystem used does not support
        immutable references. (In such a case, the fs.folder.field.value.adapter
        would be overriden to ensure a proper mapping between the reference
        and the full path if needed).
        """
        return self._ref

    @property
    def storage_code(self):
        """
        The storage code of the folder in the filesystem.
        """
        return self._storage_code

    @property
    def fs(self) -> RootedDirFileSystem | None:
        """
        The RootedDirFileSystem instance for the folder.

        This is an instance of RootedDirFileSystem for the folder.
        This ensure that only content of the folder can be accessed. (e.g.
        if the folder is stored in a subdirectory of a s3 bucket only the
        content of the folder can be accessed and any attempt to access
        the parent directory will raise an error).

        All the content of the folder can be accessed through this filesystem
        and the path of the items in the folder start from the root of the
        folder. (e.g. A folder is stored into a directory
        "/my_odoo/my_model/my_folder" of a filesystem. The fs instance
        will be created with the path "/my_odoo/my_model/my_folder" and
        the path of the items in the folder will start from "/item1", "/item2", ...
        instead of "/my_odoo/my_model/my_folder/item1",
        "/my_odoo/my_model/my_folder/item2", ...).
        """
        if self._fs is SENTINEL:
            self._fs = self._value_adapter._get_fs_for_fs_folder_field(self)
        return self._fs or None

    @property
    def protocol(self):
        """
        The root protocol of the filesystem. (e.g. file, s3, ...).

        This is the protocol of the root filesystem of the filesystem
        where the folder is stored even if the filesystem is a sub filesystem
        of a root filesystem. (e.g. if the folder is stored in a subdirectory
        of a s3 bucket the protocol is still s3).
        """
        return self._record.env["fs.storage"]._get_root_filesystem(self.fs).protocol

    @property
    def storage(self) -> FsStorage:
        """
        The FsStorage instance for the folder.

        This is the FsStorage instance for the folder. It can be used to
        access the properties of the storage.
        """
        return self._record.env["fs.storage"].get_by_code(self.storage_code)

    def initialize(self):
        """This method is called to initialize the field value if it is not already set.

        raise ValueError if the field is already set.
        """
        if self._stored_value:
            raise ValueError(f"Value already set: {self}")
        return self._field.create_value(self._record)[0]

    def __repr__(self) -> str:
        return (
            f"{self._record}.{self._field._name} -> {self.__class__.__name__}"
            f"({self._stored_value})"
        )

    def __bool__(self):
        return bool(self._stored_value)

    def __eq__(self, other):
        if other in (None, False):
            return not bool(self._stored_value)
        if isinstance(other, FsContentValue):
            return self._stored_value == other._stored_value
        return self._stored_value == other

    def __ne__(self, other):
        return not self.__eq__(other)


class FsFolderValue(FsContentValue):
    """
    Value for a fs_folder field.

    This class is used to represent the value of a fs_folder field.
    """

    pass


class AbstractFsContentField(fields.Field):
    _column_type = ("varchar", pg_varchar())
    _value_type: FsContentValue | None = None
    create_method: typing.Callable | str | None = None
    create_post_process: typing.Callable | str | None = None
    copy = False

    def __call__(
        self,
        string: str | Sentinel = SENTINEL,
        create_method: typing.Callable | str | Sentinel = SENTINEL,
        create_post_process: typing.Callable | str | Sentinel = SENTINEL,
    ) -> FsContentValue:
        return super().__call__(
            string=string,
            create_method=create_method,
            create_post_process=create_post_process,
        )

    def convert_to_cache(self, value, record, validate=True):
        if value is None or value is False:
            return None
        if isinstance(value, self._value_type):
            return value.stored_value
        return super().convert_to_cache(value, record, validate)

    def convert_to_record(self, value, record):
        return self._value_type(value, self, record)

    def convert_to_write(self, value, record):
        return super().convert_to_cache(value, record)

    def convert_to_read(self, value, record, use_display_name=True):
        if not value:
            return None
        if isinstance(value, self._value_type):
            return {
                "ref": value.ref,
                "storage_code": value.storage_code,
                "protocol": value.protocol,
            }
        raise ValueError(
            f"Invalid value for {self.name}: {repr(value)}\n"
            f"Should be a {self._value_type.__name__} object"
        )

    def get_fs(self, record: models.BaseModel) -> fsspec.AbstractFileSystem:
        storage_code = record.env["fs.storage"].get_default_storage_code_for_fs_content(
            record._name, self.name
        )
        return record.env["fs.storage"].get_fs_by_code(storage_code)

    def create_value(self, records: models.BaseModel) -> list[FsContentValue]:
        if self.related:
            vals = self._create_value_related(records)
        else:
            vals = self._create_value(records)
        return vals

    def _create_value(self, records: models.BaseModel) -> list[FsContentValue]:
        if self.create_method:
            fct = self.create_method
            if not callable(fct):
                fct = getattr(records, fct)
            vals = fct(self, self.get_fs(records))
        else:
            vals = self.create_value_in_fs(records)
        if self.create_post_process:
            fct = self.create_post_process
            if not callable(fct):
                fct = getattr(records, fct)
            vals = fct(self, vals)
        return vals

    def _create_value_related(self, records: models.BaseModel) -> list[FsContentValue]:
        others = records.sudo() if self.compute_sudo else records
        vals = []
        for record, other in zip(records, others, strict=False):
            other, field = self.traverse_related(other)
            vals.append(field.create_value(other))
            record[self.name] = other[field.name]
        return vals

    def create_value_in_fs(self, records: models.BaseModel) -> list[FsContentValue]:
        raise NotImplementedError()


class FsFolder(AbstractFsContentField):
    """Field to store a folder in a filesystem.

    This field is used to store a folder in a filesystem. The folder is
    represented by a reference (by default the name) in the filesystem.
    The value stored in the databse is by default the reference of the folder
    and the storage code in the following format::

        {storage_code}://{ref}

    This provides different method hooks to customize the way the folder is
    created in the filesystem.

    :param create_method: a method to call to create the folder in the filesystem.
        This method is called with the recordset and the filesystem as arguments.
        The method should return a list of FsFolderValue. If this method is provided
        the "create_name_get", "create_parent_get" and "create_additional_kwargs_get"
        method hooks are ignored. This method must assign the value to the field
        on the records.
    :param create_parent_get: a method to call to get the list of parents of the folder
        to create. This method is called with the recordset and the filesystem as
        arguments. The method should return a dict with the following structure::

            {record.id: ['path_part1', 'path_part2', ...]}

        The path parts are joined with the separator of the filesystem to create the
        full path of the folder.
        If this method is not provided the default parent is the root of the
        filesystem.
    :param create_name_get: a method to call to get the name of the folder to create.
        This method is called with the recordset and the filesystem as arguments.
        The method should return a dict with the following structure::

            {record.id: folder_name}
        If this method is not provided the default name is the display_name of the
        record.
    :param create_additional_kwargs_get: a method to call to get additional kwargs to
        pass to the mkdir method of the filesystem. This method is called with the
        recordset and the filesystem as arguments. The method should return a dict
        with the following structure::

            {record.id: {kwarg1: val1, ...}}
        If this method is not provided the default is an empty dict.

    :param create_post_process: a method to call after the folder is created in the
        filesystem. This method is called with the list of FsFolderValue created.
        This method can be used to do additional processing on the created folders.


    If you need to customize the value stored in the database you can inherit
    from the abstrate model "fs.folder.field.value.adapter" and override the
    methods as needed. (see the documentation of the model for more details).

    The value returned by the field is an instance of FsFolderValue. You can
    assign a string to the field or an instance of FsFolderValue. If you
    assign a string be careful to ensure that the string is in the correct
    format to be parsed as an FsFolderValue. Even if no value is set the field
    will return an instance of FsFolderValue comparable to None or False. This
    is usefull since this instance provides the "initialize" method to create
    the folder in the filesystem.

    When the field is read the value is returned as a dict with the following
    structure::

        {
            "ref": "folder_name",
            "storage_code": "tmp_dir",
            "protocol": "file"
        }
    """

    type = "fs_folder"
    _value_type = FsFolderValue
    create_parent_get: typing.Callable | str | None = None
    create_name_get: typing.Callable | str | None = None
    create_additional_kwargs_get: typing.Callable | str | None = None

    def __init__(
        self,
        string: str | Sentinel = SENTINEL,
        create_method: typing.Callable | str | Sentinel = SENTINEL,
        create_parent_get: typing.Callable | str | Sentinel = SENTINEL,
        create_name_get: typing.Callable | str | Sentinel = SENTINEL,
        create_additional_kwargs_get: typing.Callable | str | Sentinel = SENTINEL,
        **kwargs,
    ):
        super().__init__(
            string=string,
            create_method=create_method,
            create_name_get=create_name_get,
            create_parent_get=create_parent_get,
            create_additional_kwargs_get=create_additional_kwargs_get,
            **kwargs,
        )

    def create_value_in_fs(self, records: models.BaseModel) -> list[FsFolderValue]:
        records.check_access("write")
        fs = self.get_fs(records)
        names = self.get_create_names(records, fs)
        parents = self.get_create_parents(records, fs)
        additional_kwargs = self.get_create_additional_kwargs(records, fs)
        value_adapter = records.env["fs.folder.field.value.adapter"]
        for record in records:
            storage_code = records.env[
                "fs.storage"
            ].get_default_storage_code_for_fs_content(records._name, self.name)
            storage = records.env["fs.storage"].get_by_code(storage_code)
            path_parts = [names[record.id]]
            parent_path_parts = parents[record.id]
            if parent_path_parts:
                path_parts = parent_path_parts + path_parts
            kwargs = additional_kwargs[record.id]
            # ensure the path is valid
            if storage.sanitize_fs_name:
                path_parts = storage.sanitize_fs_item_names(path_parts)
            else:
                storage.is_fs_names_valid(path_parts, raise_if_invalid=True)

            path = fs.sep.join(path_parts)

            fs.mkdir(path, **kwargs)

            def clean_up_folder(path, storage_code, dbname):
                db_registry = registry(dbname)
                with db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    fs = env["fs.storage"].get_fs_by_code(storage_code)
                    time.sleep(0.5)  # wait creation into the filesystem
                    fs.rm(path, recursive=True)
                # remove created resource in case of rollback

            test_mode = getattr(threading.current_thread(), "testing", False)
            if not test_mode:
                record.env.cr.postrollback.add(
                    partial(
                        clean_up_folder,
                        path,
                        storage_code,
                        record.env.cr.dbname,
                    ),
                )

            record[self.name] = value_adapter._created_folder_name_to_stored_value(
                path, storage_code, fs
            )
        return [record[self.name] for record in records]

    def _sanitize_path(self, path: str, separator: str, storage: FsStorage) -> str:
        parts = path.split(separator)
        sanitized_parts = storage.sanitize_fs_item_names(parts)
        return separator.join(sanitized_parts)

    def get_create_names(
        self, records: models.BaseModel, fs: fsspec.AbstractFileSystem
    ):
        """return the names of the folders to create into the filesystem
        for the given recordset.
        :rtype: dict
        :return: a dictionay with an entry for each record with the following
        structure ::

            {record.id: 'name'}

        """
        if self.create_name_get:
            fct = self.create_name_get
            if not callable(fct):
                fct = getattr(records, fct)
            return fct(self, fs)
        return {record.id: record.display_name for record in records}

    def get_create_parents(self, records, fs: fsspec.AbstractFileSystem):
        """return the path to use as parent of the new folder.
        :rtype: dict
        :return: a dictionay with an entry for each record with the following
        structure ::

            {record.id: ['path_part1', 'path_part2', ...]}

        """
        if self.create_parent_get:
            fct = self.create_parent_get
            if not callable(fct):
                fct = getattr(records, fct)
            return fct(self, fs)
        return dict.fromkeys(records.ids, [""])

    def get_create_properties(self, records, backend):
        """Return the properties to use to created the folder into the CMIS
        container.
        :rtype: dict
        :return: a dictionay with an entry for each record with the following
        structure ::

            {record.id: {'cmis:xxx': 'val1', ...}}

        """
        if self.create_properties_get:
            fct = self.create_properties_get
            if not callable(fct):
                fct = getattr(records, fct)
            return fct(self, backend)
        return dict.fromkeys(records.ids, None)

    def get_create_additional_kwargs(self, records, fs: fsspec.AbstractFileSystem):
        """return the additional kwargs passed to the mkdir method of the
        filesystem.
        :rtype: dict
        """
        if self.create_additional_kwargs_get:
            fct = self.create_additional_kwargs_get
            if not callable(fct):
                fct = getattr(records, fct)
            return fct(self, fs)
        return dict.fromkeys(records.ids, {})
