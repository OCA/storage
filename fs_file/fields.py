# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# pylint: disable=method-required-super
import base64
import itertools
import os.path
from io import BytesIO, IOBase

from odoo import fields

from odoo.addons.fs_attachment.models.ir_attachment import IrAttachment


class FSFileValue:
    def __init__(
        self,
        attachment: IrAttachment = None,
        name: str = None,
        value: bytes | IOBase = None,
    ) -> None:
        """
        This class holds the information related to FSFile field. It can be
        used to assign a value to a FSFile field. In such a case, you can pass
        the name and the file content as parameters.

        When

        :param attachment: the attachment to use to store the file.
        :param name: the name of the file. If not provided, the name will be
            taken from the attachment or the io.IOBase.
        :param value: the content of the file. It can be bytes or an io.IOBase.
        """
        self._is_new: bool = attachment is None
        self._buffer: IOBase = None
        self._attachment: IrAttachment = attachment
        if name and attachment:
            raise ValueError("Cannot set name and attachment at the same time")
        if value:
            if isinstance(value, IOBase):
                self._buffer = value
                if not hasattr(value, "name") and name:
                    self._buffer.name = name
                elif not name:
                    raise ValueError(
                        "name must be set when value is an io.IOBase "
                        "and is not provided by the io.IOBase"
                    )
            elif isinstance(value, bytes):
                self._buffer = BytesIO(value)
                if not name:
                    raise ValueError("name must be set when value is bytes")
                self._buffer.name = name
            else:
                raise ValueError("value must be bytes or io.BytesIO")

    @property
    def write_buffer(self) -> BytesIO:
        if self._buffer is None:
            name = self._attachment.name if self._attachment else None
            self._buffer = BytesIO()
            self._buffer.name = name
        return self._buffer

    @property
    def name(self) -> str | None:
        name = (
            self._attachment.name
            if self._attachment
            else self._buffer.name
            if self._buffer
            else None
        )
        if name:
            return os.path.basename(name)
        return None

    @name.setter
    def name(self, value: str) -> None:
        # the name should only be updatable while the file is not yet stored
        # TODO, we could also allow to update the name of the file and rename
        # the file in the external file system
        if self._is_new:
            self.write_buffer.name = value
        else:
            raise ValueError(
                "The name of the file can only be updated while the file is not "
                "yet stored"
            )

    @property
    def mimetype(self) -> str | None:
        return self._attachment.mimetype if self._attachment else None

    @property
    def size(self) -> int:
        return self._attachment.file_size if self._attachment else len(self._buffer)

    @property
    def url(self) -> str | None:
        return self._attachment.url if self._attachment else None

    @property
    def internal_url(self) -> str | None:
        return self._attachment.internal_url if self._attachment else None

    @property
    def attachment(self) -> IrAttachment | None:
        return self._attachment

    @attachment.setter
    def attachment(self, value: IrAttachment) -> None:
        self._attachment = value
        self._buffer = None

    @property
    def read_buffer(self) -> BytesIO:
        if self._buffer is None:
            content = b""
            name = None
            if self._attachment:
                content = self._attachment.raw
                name = self._attachment.name
            self._buffer = BytesIO(content)
            self._buffer.name = name
        return self._buffer

    def getvalue(self) -> bytes:
        buffer = self.read_buffer
        current_pos = buffer.tell()
        buffer.seek(0)
        value = buffer.read()
        buffer.seek(current_pos)
        return value

    def open(
        self,
        mode="rb",
        block_size=None,
        cache_options=None,
        compression=None,
        new_version=True,
        **kwargs
    ) -> IOBase:
        """
        Return a file-like object that can be used to read and write the file content.
        See the documentation of open() into the ir.attachment model from the
        fs_attachment module for more information.
        """
        if not self._attachment:
            raise ValueError("Cannot open a file that is not stored")
        return self._attachment.open(
            mode=mode,
            block_size=block_size,
            cache_options=cache_options,
            compression=compression,
            new_version=new_version,
            **kwargs,
        )


class FSFile(fields.Binary):
    """
    This field is a binary field that stores the file content in an external
    filesystem storage referenced by a storage code.

    A major difference with the standard Odoo binary field is that the value
    is not encoded in base64 but is a bytes object.

    Moreover, the field is designed to always return an instance of
    :class:`FSFileValue` when reading the value. This class is a file-like
    object that can be used to read the file content and to get information
    about the file (filename, mimetype, url, ...).

    To update the value of the field, the following values are accepted:

    - a bytes object (e.g. ``b"..."``)
    - a dict with the following keys:
      - ``filename``: the filename of the file
      - ``content``: the content of the file encoded in base64
    - a FSFileValue instance
    - a file-like object (e.g. an instance of :class:`io.BytesIO`)

    When the value is provided is a bytes object the filename is set to the
    name of the field. You can override this behavior by providing specifying
    a fs_filename key in the context. For example:

    .. code-block:: python

        record.with_context(fs_filename='my_file.txt').write({
            'field': b'...',
        })

    The same applies when the value is provided as a file-like object but the
    filename is set to the name of the file-like object or not a property of
    the file-like object. (e.g. ``io.BytesIO(b'...')``).


    When the value is converted to the read format, it's always an instance of
    dict with the following keys:

    - ``filename``: the filename of the file
    - ``mimetype``: the mimetype of the file
    - ``size``: the size of the file
    - ``url``: the url to access the file

    """

    type = "fs_file"

    attachment: bool = True

    def __init__(self, **kwargs):
        kwargs["attachment"] = True
        super().__init__(**kwargs)

    def read(self, records):
        domain = [
            ("res_model", "=", records._name),
            ("res_field", "=", self.name),
            ("res_id", "in", records.ids),
        ]
        data = {
            att.res_id: FSFileValue(attachment=att)
            for att in records.env["ir.attachment"].sudo().search(domain)
        }
        records.env.cache.insert_missing(records, self, map(data.get, records._ids))

    def create(self, record_values):
        if not record_values:
            return
        env = record_values[0][0].env
        with env.norecompute():
            ir_attachment = (
                env["ir.attachment"]
                .sudo()
                .with_context(
                    binary_field_real_user=env.user,
                )
            )
            for record, value in record_values:
                if value:
                    cache_value = self.convert_to_cache(value, record)
                    attachment = ir_attachment.create(
                        {
                            "name": cache_value.name,
                            "raw": cache_value.getvalue(),
                            "res_model": record._name,
                            "res_field": self.name,
                            "res_id": record.id,
                            "type": "binary",
                        }
                    )
                    record.env.cache.update(
                        record,
                        self,
                        [FSFileValue(attachment=attachment)],
                        dirty=False,
                    )

    def write(self, records, value):
        # the code is copied from the standard Odoo Binary field
        # with the following changes:
        # - the value is not encoded in base64 and we therefore write on
        #  ir.attachment.raw instead of ir.attachment.datas

        # discard recomputation of self on records
        records.env.remove_to_compute(self, records)
        # update the cache, and discard the records that are not modified
        cache = records.env.cache
        cache_value = self.convert_to_cache(value, records)
        records = cache.get_records_different_from(records, self, cache_value)
        if not records:
            return records
        if self.store:
            # determine records that are known to be not null
            not_null = cache.get_records_different_from(records, self, None)

        cache.update(records, self, itertools.repeat(cache_value))

        # retrieve the attachments that store the values, and adapt them
        if self.store and any(records._ids):
            real_records = records.filtered("id")
            atts = (
                records.env["ir.attachment"]
                .sudo()
                .with_context(
                    binary_field_real_user=records.env.user,
                )
            )
            if not_null:
                atts = atts.search(
                    [
                        ("res_model", "=", self.model_name),
                        ("res_field", "=", self.name),
                        ("res_id", "in", real_records.ids),
                    ]
                )
            if value:
                filename = cache_value.name
                content = cache_value.getvalue()
                # update the existing attachments
                atts.write({"raw": content, "name": filename})
                atts_records = records.browse(atts.mapped("res_id"))
                # create the missing attachments
                missing = real_records - atts_records
                if missing:
                    create_vals = []
                    for record in missing:
                        create_vals.append(
                            {
                                "name": filename,
                                "res_model": record._name,
                                "res_field": self.name,
                                "res_id": record.id,
                                "type": "binary",
                                "raw": content,
                            }
                        )
                    created = atts.create(create_vals)
                    for att in created:
                        record = records.browse(att.res_id)
                        record.env.cache.update(
                            record, self, [FSFileValue(attachment=att)], dirty=False
                        )
            else:
                atts.unlink()

        return records

    def _get_filename(self, record):
        return record.env.context.get("fs_filename", self.name)

    def convert_to_cache(self, value, record, validate=True):
        if value is None or value is False:
            return None
        if isinstance(value, FSFileValue):
            return value
        if isinstance(value, dict):
            return FSFileValue(
                name=value["filename"], value=base64.b64decode(value["content"])
            )
        if isinstance(value, IOBase):
            name = getattr(value, "name", None)
            if name is None:
                name = self._get_filename(record)
            return FSFileValue(name=name, value=value)
        if isinstance(value, bytes):
            return FSFileValue(
                name=self._get_filename(record), value=base64.b64decode(value)
            )
        raise ValueError(
            "Invalid value for %s: %r\n"
            "Should be base64 encoded bytes or a file-like object" % (self, value)
        )

    def convert_to_write(self, value, record):
        return self.convert_to_cache(value, record)

    def __convert_to_column(self, value, record, values=None, validate=True):
        if value is None or value is False:
            return None
        if isinstance(value, IOBase):
            if hasattr(value, "getvalue"):
                value = value.getvalue()
            else:
                v = value.read()
                value.seek(0)
                value = v
            return value
        if isinstance(value, bytes):
            return base64.b64decode(value)
        raise ValueError(
            "Invalid value for %s: %r\n"
            "Should be base64 encoded bytes or a file-like object" % (self, value)
        )

    def __convert_to_record(self, value, record):
        if value is None or value is False:
            return None
        if isinstance(value, IOBase):
            return value
        if isinstance(value, bytes):
            return FSFileValue(value=value)
        raise ValueError(
            "Invalid value for %s: %r\n"
            "Should be base64 encoded bytes or a file-like object" % (self, value)
        )

    def convert_to_read(self, value, record, use_name_get=True):
        if value is None or value is False:
            return None
        if isinstance(value, FSFileValue):
            return {
                "filename": value.name,
                "url": value.internal_url,
                "size": value.size,
                "mimetype": value.mimetype,
            }
        raise ValueError(
            "Invalid value for %s: %r\n"
            "Should be base64 encoded bytes or a file-like object" % (self, value)
        )
