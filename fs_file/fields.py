# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# pylint: disable=method-required-super
import base64
import itertools
from io import IOBase

from odoo import fields

from .io import FSFileBytesIO


class FSFile(fields.Binary):
    """
    This field is a binary field that stores the file content in an external
    filesystem storage referenced by a storage code.

    A major difference with the standard Odoo binary field is that the value
    is not encoded in base64 but is a bytes object.

    Moreover, the field is designed to always return an instance of
    :class:`FSFileBytesIO` when reading the value. This class is a file-like
    object that can be used to read the file content and to get information
    about the file (filename, mimetype, url, ...).

    To update the value of the field, the following values are accepted:

    - a bytes object (e.g. ``b"..."``)
    - a dict with the following keys:
      - ``filename``: the filename of the file
      - ``content``: the content of the file encoded in base64
    - a FSFileBytesIO instance
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
    storage_code: str = None

    def __init__(self, storage_code: str = None, **kwargs):
        self.storage_code = storage_code
        kwargs["attachment"] = True
        super().__init__(**kwargs)

    def read(self, records):
        domain = [
            ("res_model", "=", records._name),
            ("res_field", "=", self.name),
            ("res_id", "in", records.ids),
        ]
        data = {
            att.res_id: FSFileBytesIO(attachment=att)
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
                    storage_code=self.storage_code,
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
                        [FSFileBytesIO(attachment=attachment)],
                        dirty=False,
                    )

    def write(self, records, value):
        # the code is copied from the standard Odoo Binary field
        # with the following changes:
        # - the value is not encoded in base64 and we therefore write on
        #  ir.attachment.raw instead of ir.attachment.datas
        # - we use the storage_code to store the attachment in the right
        #  filesystem storage

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
                    storage_code=self.storage_code,
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
                            record, self, [FSFileBytesIO(attachment=att)], dirty=False
                        )
            else:
                atts.unlink()

        return records

    def _get_filename(self, record):
        return record.env.context.get("fs_filename", self.name)

    def convert_to_cache(self, value, record, validate=True):
        if value is None or value is False:
            return None
        if isinstance(value, FSFileBytesIO):
            return value
        if isinstance(value, dict):
            return FSFileBytesIO(
                name=value["filename"], value=base64.b64decode(value["content"])
            )
        if isinstance(value, IOBase):
            name = getattr(value, "name", None)
            if name is None:
                name = self._get_filename(record)
            return FSFileBytesIO(name=name, value=value)
        if isinstance(value, bytes):
            return FSFileBytesIO(
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
            return FSFileBytesIO(value=value)
        raise ValueError(
            "Invalid value for %s: %r\n"
            "Should be base64 encoded bytes or a file-like object" % (self, value)
        )

    def convert_to_read(self, value, record, use_name_get=True):
        if value is None or value is False:
            return None
        if isinstance(value, FSFileBytesIO):
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
