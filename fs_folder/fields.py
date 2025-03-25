# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import typing

import fsspec

from odoo import fields, models
from odoo.tools.misc import SENTINEL, Sentinel
from odoo.tools.sql import pg_varchar


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
            self._stored_value, self, self._record
        )

    @property
    def stored_value(self):
        return self._stored_value

    @property
    def ref(self):
        return self._ref

    @property
    def storage_code(self):
        return self._storage_code

    @property
    def fs(self) -> fsspec.AbstractFileSystem:
        if self._fs is SENTINEL:
            self._fs = self._value_adapter._get_fs_for_fs_folder_field(self)
        return self._fs

    @property
    def protocol(self):
        return self._record.env["fs.storage"]._get_root_filesystem(self.fs).protocol

    def initialize(self):
        """This method is called to initialize the field value if it is not already set.

        raise ValueError if the field is already set.
        """
        if self._stored_value:
            raise ValueError(f"Value already set: {self}")
        return self._field.create_value(self._record)

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
    pass


class AbstractFsContentField(fields.Field):
    _column_type = ("varchar", pg_varchar())
    _value_type: FsContentValue | None = None
    create_method: typing.Callable | str | None = None
    copy = False

    def __call__(
        self,
        string: str | Sentinel = SENTINEL,
        create_method: typing.Callable | str | Sentinel = SENTINEL,
    ) -> FsContentValue:
        return super().__call__(string=string, create_method=create_method)

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
            return fct(self, self.get_fs(records))
        return self.create_value_in_fs(records)

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
            name = names[record.id]
            parent = parents[record.id]
            kwargs = additional_kwargs[record.id]
            path = fs.sep.join([parent.lstrip("/"), name.lstrip("/")])
            fs.mkdir(path, **kwargs)
            record[self.name] = value_adapter._created_folder_name_to_stored_value(
                path, storage_code, fs
            )
        return [record[self.name] for record in records]

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

            {record.id: 'cmis:objectId'}

        """
        if self.create_parent_get:
            fct = self.create_parent_get
            if not callable(fct):
                fct = getattr(records, fct)
            return fct(self, fs)
        return dict.fromkeys(records.ids, "/")

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
