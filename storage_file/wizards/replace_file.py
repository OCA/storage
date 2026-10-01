# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


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
        return file_model.create(self._prepare_file_values())

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
        """Drop the replaced file, not owned by any record anymore."""
        old_file = old_file.sudo()
        # Forcing the deletion skips the cleanup cron, which also removes
        # the file from the backend: do it here.
        if old_file.relative_path:
            old_file.backend_id.delete(old_file.relative_path)
        old_file.with_context(force_delete_storage_file=True).unlink()

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
