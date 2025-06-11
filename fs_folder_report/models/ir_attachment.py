# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from pathlib import Path

from odoo import api, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model_create_multi
    def create(self, vals_list):
        # If the context has a report_id, we assume that the attachment
        # is being created as part of a report generation process.
        # IF the report has the save_in_fs_folder option enabled,
        # we will save the attachment in the folder associated with the record.
        report_sudo = self.env["ir.actions.report"].sudo()
        if "report_id" in self.env.context:
            report_sudo = report_sudo.browse(self.env.context["report_id"])
        if report_sudo.save_in_fs_folder and report_sudo.fs_folder_field_id:
            return self._create_in_fs_folder(vals_list, report_sudo)
        return super().create(vals_list)

    def _create_in_fs_folder(self, vals_list, report_sudo):
        attachments = self.browse()
        for vals in vals_list:
            # Get the record associated with the report
            record = self.env[report_sudo.model].browse(vals.get("res_id"))
            if not record:
                continue

            # Get the folder field from the report
            field_name = report_sudo.fs_folder_field_id.name

            # Create the folder if it does not exist
            folder = record[field_name]
            if not folder:
                folder = folder.initialize()
            fs_storage_sudo = folder.storage.sudo()
            fs_folder_path = report_sudo._get_fs_folder_path(record)
            folder_path_parts = fs_folder_path.split("/") if fs_folder_path else []
            if folder_path_parts:
                folder_path_parts = fs_storage_sudo.sanitize_fs_item_names(
                    folder_path_parts
                )
                folder.fs.makedirs("/".join(folder_path_parts), exist_ok=True)
            # FS folder are rooted folder where the path is the path of the forlder
            # into the original storage registered as fs_storage. We must store the
            # attachment with a path that starts with the folder's path since it will
            # be browsed from this storage when used as attachment.
            path_parts = [folder.fs.path]
            path_parts.extend(folder_path_parts)
            # the filename will be renamed later but will
            # still into the specified folder
            sanitized_name = fs_storage_sudo.sanitize_fs_item_name(vals["name"])
            vals["name"] = sanitized_name
            path_parts.append(f"{sanitized_name}.tmp")
            full_filename = "/".join(path_parts)
            attachment = super(
                IrAttachment,
                self.with_context(
                    storage_location=folder.storage_code,
                    force_storage_key=full_filename,
                    # Keep the original filename for later renaming
                    keep_original_filename=True,
                ),
            ).create(vals)
            record = self.env[attachment.res_model].browse(attachment.res_id)
            self.env["bus.bus"]._notify_fs_folder_modified(record, field_name)
            attachments |= attachment
        return attachments

    def _enforce_meaningful_storage_filename(self) -> None:  # pylint: disable=missing-return
        # In the context of report generation, we want to keep the original filename
        # but we must avoid conflicts if the same report is generated multiple times.
        if self.env.context.get("keep_original_filename") and self.env.context.get(
            "report_id"
        ):
            self._enforce_report_filename()
        else:
            super()._enforce_meaningful_storage_filename()

    def _enforce_report_filename(self) -> None:
        if not self.env.context.get(
            "keep_original_filename"
        ) or not self.env.context.get("report_id"):
            return
        for attachment in self:
            if not self._is_file_from_a_storage(attachment.store_fname):
                continue
            fs, storage, filename = attachment._get_fs_parts()

            if self.env["fs.storage"]._must_use_filename_obfuscation(storage):
                attachment.fs_filename = filename
                continue
            report_name = attachment.name
            report_path = Path(filename).parent
            new_filename = self._get_unique_report_filename(
                fs, report_path, report_name
            )
            fs.rename(filename, new_filename)
            attachment.fs_filename = new_filename
            attachment._force_write_store_fname(f"{storage}://{new_filename}")
            self._fs_mark_for_gc(attachment.store_fname)

    def _get_unique_report_filename(
        self, fs, report_path: Path, report_name: str
    ) -> str:
        """Generate a unique filename for the report to avoid conflicts."""
        new_filename = report_path / report_name
        if not fs.exists(str(new_filename)):
            return str(new_filename)
        # If the file already exists, we need to generate a unique name
        name, extension = new_filename.stem, new_filename.suffix
        counter = 1
        while True:
            new_filename = str(report_path / f"{name}({counter}){extension}")
            if not fs.exists(new_filename):
                return new_filename
            counter += 1
