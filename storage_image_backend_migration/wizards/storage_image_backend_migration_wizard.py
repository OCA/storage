import base64
import logging
import os

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)

try:
    import magic
except (ImportError, IOError) as err:
    _logger.debug(err)


def gen_chunks(iterable, chunksize=10):
    """Chunk generator.

    Take an iterable and yield `chunksize` sized slices.
    "Borrowed" from connector_importer.
    """
    chunk = []
    last_chunk = False
    for i, line in enumerate(iterable):
        if i % chunksize == 0 and i > 0:
            yield chunk, last_chunk
            del chunk[:]
        chunk.append(line)
    last_chunk = True
    yield chunk, last_chunk


class StorageImageBackendMigrationWizard(models.TransientModel):
    _name = "storage.image.backend.migration.wizard"
    _description = "Storage Image Backend Migration Wizard"

    source_storage_backend_id = fields.Many2one(
        "storage.backend", "Storage Backend with images", required=True
    )

    storage_backend_id = fields.Many2one(
        "storage.backend", "Storage Backend", required=True
    )

    chunk_size = fields.Integer(
        default=10,
        help="How many lines will be handled in each job.",
    )

    def _get_storage_files(self):
        files = self.env["storage.file"].search(
            [
                ("backend_id", "=", self.source_storage_backend_id.id),
                ("file_type", "in", ["image", "thumbnail"]),
            ]
        )
        return files

    def action_migrate(self):
        # Generate N chunks to split in several jobs.
        chunks = gen_chunks(self._get_storage_files(), chunksize=self.chunk_size)
        for i, (chunk, is_last_chunk) in enumerate(chunks, 1):
            self.with_delay().do_migrate(lines=chunk)
            _logger.info(
                "Generated job for chunk nr %d. Is last: %s.",
                i,
                "yes" if is_last_chunk else "no",
            )

    def do_migrate(self, lines=None):
        lines = lines or self._get_storage_files()
        self._do_migrate(lines)
        return True

    def _update_file_from_image(self, old_file, new_file):
        image_obj = self.env["storage.image"]
        image = image_obj.search([("file_id", "=", old_file.id)])
        if image:
            image.update({"file_id": new_file.id})

    def _update_file_from_thumbnail(self, old_file, new_file):
        thumbnail_obj = self.env["storage.thumbnail"]
        thumbnail = thumbnail_obj.search([("file_id", "=", old_file.id)])
        if thumbnail:
            thumbnail.update({"file_id": new_file.id})

    def _do_migrate(self, lines):
        file_obj = self.env["storage.file"]
        for old_file in lines:
            file_path = old_file.relative_path
            file_vals = self._prepare_file_values(
                file_path, filetype=old_file.file_type
            )
            new_file = file_obj.create(file_vals)
            if old_file.file_type == "image":
                self._update_file_from_image(old_file, new_file)
            elif old_file.file_type == "thumbnail":
                self._update_file_from_thumbnail(old_file, new_file)
            else:
                pass
            # Unlink old file, cron cleanup storage needed
            old_file.unlink()
        return True

    def _read_from_external_storage(self, file_path):
        if not self.source_storage_backend_id:
            raise exceptions.UserError(_("No storage backend provided!"))
        return self.source_storage_backend_id.get(file_path)

    @api.model
    def _get_base64(self, file_path):
        res = {}
        mimetype = None
        binary = self._read_from_external_storage(file_path)
        if binary:
            mimetype = magic.from_buffer(binary, mime=True)
            res = {"mimetype": mimetype, "b64": base64.encodebytes(binary)}
        return res

    def _prepare_file_values(self, file_path, filetype="image"):
        name = os.path.basename(file_path)
        file_data = self._get_base64(file_path)
        if not file_data:
            return {}
        vals = {
            "data": file_data["b64"],
            "name": name,
            "file_type": filetype,
            "mimetype": file_data["mimetype"],
            "backend_id": self.storage_backend_id.id,
        }
        return vals
