# Copyright 2023 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64
import hashlib

from odoo import api, fields, models
from odoo.exceptions import UserError


class StorageFileReplace(models.TransientModel):
    _name = "storage.file.replace"
    _description = "Wizard template allowing to replace a storage.file"

    file_id = fields.Many2one("storage.file")
    data = fields.Binary()
    file_name = fields.Char()
    keep_history = fields.Boolean(
        default=True,
        help="Keep an archived copy of the record holding the replaced file.",
    )
    # Support for relations is up to the modules defining them
    keep_relations = fields.Boolean(
        default=True,
        help="Link the archived copy to the same records.",
    )
    keep_relations_visible = fields.Boolean(
        compute="_compute_keep_relations_visible",
    )

    @api.depends("keep_history")
    def _compute_keep_relations_visible(self):
        for rec in self:
            rec.keep_relations_visible = (
                rec.keep_history and rec._has_replaced_relations()
            )

    def _has_replaced_relations(self):
        """Tell if the record owning the replaced file has relations to keep.

        Hook for the modules defining relations to it.
        """
        return False

    def _get_file_from_data(self):
        file_model = self.env["storage.file"].sudo()
        values = self._prepare_file_values()
        stored_file = self._get_stored_file()
        if stored_file:
            return self._reuse_stored_file(stored_file, values)
        return file_model.create(values)

    def _get_stored_file(self):
        """Return the file already storing the wizard data, if any.

        With the 'hash' filename strategy the path depends only on the
        content: the same content can be stored only once per backend.
        """
        file_model = self.env["storage.file"].sudo().with_context(active_test=False)
        backend = self.file_id.sudo().backend_id
        if backend.filename_strategy != "hash" or not self.data:
            return file_model
        checksum = hashlib.sha1(base64.b64decode(self.data)).hexdigest()
        new_file = file_model.new({"backend_id": backend.id})
        relative_path = new_file._build_relative_path(checksum)
        return file_model.search(
            [("backend_id", "=", backend.id), ("relative_path", "=", relative_path)],
            limit=1,
        )

    def _reuse_stored_file(self, stored_file, values):
        """Reuse ``stored_file`` if it is waiting for deletion.

        This is the case of a file replaced without history, then uploaded
        again before the cleanup cron runs.
        """
        if stored_file == self.file_id:
            raise UserError(self.env._("The new file is identical to the current one."))
        if not stored_file.to_delete:
            # TODO: restore the record owning ``stored_file``, if archived
            raise UserError(
                self.env._(
                    "The same content is already stored in file '%(name)s' "
                    "(ID %(id)s).",
                    name=stored_file.name,
                    id=stored_file.id,
                )
            )
        stored_file.write({"to_delete": False, "active": True, "name": values["name"]})
        return stored_file

    def _prepare_file_values(self):
        return {
            "backend_id": self.file_id.backend_id.id,
            "data": self.data,
            "name": self.file_name,
        }

    def confirm(self):
        return

    def _replace_file(self, owner):
        """Make ``owner`` point to a new file built from the wizard data.

        Without ``keep_history``, the replaced file is dropped: nothing
        refers to it anymore.

        :param owner: record delegating to 'storage.file' via ``file_id``
        :return: the archived copy of ``owner`` if ``keep_history`` is set
        """
        old_file = owner.file_id
        archived = self.keep_history and self._copy_replaced(owner)
        # Creating the file with its data already stores it on the backend
        owner.file_id = self._get_file_from_data()
        if archived:
            # 'active' is the one of the file, shared with ``owner``
            # until the replacement: archive it only now.
            archived.active = False
        else:
            self._drop_replaced_file(old_file)
        return archived

    def _drop_replaced_file(self, old_file):
        """Drop the replaced file, not owned by any record anymore.

        The file is only flagged for deletion: the cleanup cron removes it
        from the backend, once the transaction is committed.
        """
        old_file.sudo().unlink()

    def _copy_replaced(self, owner):
        """Copy ``owner``, keeping the file being replaced.

        The copy is returned active: it is archived by ``_replace_file``
        once ``owner`` points to the new file.
        """
        archived = owner.sudo().copy(self._copy_replaced_prepare_values(owner))
        if self.keep_relations:
            self._copy_replaced_relations(owner, archived)
        return archived

    def _copy_replaced_relations(self, owner, archived):
        """Link ``archived`` to the same records as ``owner``.

        Hook for the modules defining relations to ``owner``.
        """
        return

    def _copy_replaced_prepare_values(self, owner):
        old_file = owner.file_id
        return {
            # Reuse the file instead of duplicating it
            "file_id": old_file.id,
            # Otherwise the creation sets the default backend of the owner
            # and writes it on the reused file, which moves it.
            "backend_id": old_file.backend_id.id,
        }
