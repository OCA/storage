# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# pylint: disable=method-required-super
import io
import os.path

from odoo.addons.fs_attachment.models.ir_attachment import IrAttachment


class FSFileBytesIO:
    def __init__(
        self,
        attachment: IrAttachment = None,
        name: str = None,
        value: bytes | io.IOBase = None,
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
        self._buffer: io.IOBase = None
        self._attachment: IrAttachment = attachment
        if name and attachment:
            raise ValueError("Cannot set name and attachment at the same time")
        if value:
            if isinstance(value, io.IOBase):
                self._buffer = value
                if not hasattr(value, "name") and name:
                    self._buffer.name = name
                elif not name:
                    raise ValueError(
                        "name must be set when value is an io.IOBase "
                        "and is not provided by the io.IOBase"
                    )
            elif isinstance(value, bytes):
                self._buffer = io.BytesIO(value)
                if not name:
                    raise ValueError("name must be set when value is bytes")
                self._buffer.name = name
            else:
                raise ValueError("value must be bytes or io.BytesIO")

    @property
    def write_buffer(self) -> io.BytesIO:
        if self._buffer is None:
            name = self._attachment.name if self._attachment else None
            self._buffer = io.BytesIO()
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

    def open(
        self,
        mode="rb",
        block_size=None,
        cache_options=None,
        compression=None,
        new_version=True,
        **kwargs
    ) -> io.IOBase:
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
