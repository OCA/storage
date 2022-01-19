# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast
import base64
import logging
import os
import re
import urllib
from urllib.parse import urlparse

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ImageRelationAbstract(models.AbstractModel):
    _inherit = "image.relation.abstract"

    import_from_url = fields.Char(related="image_id.imported_from_url")

    def _get_filename(self, headers, url):
        # Note it will be better to use rfc6266 lib but it's doesn't support python 3.7
        if headers["Content-Disposition"]:
            fname = re.findall(
                r"filename\*?=([^;]+)",
                headers["Content-Disposition"],
                flags=re.IGNORECASE,
            )
            fname = fname[0].strip().strip('"')
        if fname:
            return fname
        else:
            return os.path.basename(urlparse(url).path)

    def _get_download_header(self):
        headers = self.env["ir.config_parameter"].get_param(
            "storage_image_import.headers", {}
        )
        return ast.literal_eval(headers)

    def _prepare_image_from_url(self, url):
        req = urllib.request.Request(url, headers=self._get_download_header())
        res = urllib.request.urlopen(req)
        data = res.read()
        return {
            "name": self._get_filename(res.headers, url),
            "data": base64.b64encode(data),
            "imported_from_url": url,
        }

    def _create_image_from_url(self, url):
        try:
            return self.env["storage.image"].create(self._prepare_image_from_url(url))
        except Exception as e:
            _logger.error(e)
            raise ValidationError(
                _("Fail to import image {} check if the url is valid").format(url)
            )

    def _get_existing_image_from_url(self, url):
        return self.env["storage.image"].search([("imported_from_url", "=", url)])

    def _process_import_from_url(self, vals):
        if vals.get("import_from_url"):
            url = vals.pop("import_from_url")
            image = self._get_existing_image_from_url(url)
            if not image:
                image = self._create_image_from_url(url)
            vals["image_id"] = image.id

    def _get_domain_for_existing_relation(self, vals):
        return []

    def _get_existing_relation(self, vals):
        domain = self._get_domain_for_existing_relation(vals)
        if domain:
            return self.search(domain)
        else:
            return self

    @api.model_create_multi
    def create(self, vals_list):
        vals_to_create = []
        for vals in vals_list:
            record = None
            if "import_from_url" in vals:
                record = self._get_existing_relation(vals)
            if record:
                vals.pop("import_from_url")
                record.write(vals)
            else:
                vals_to_create.append(vals)
        for vals in vals_to_create:
            self._process_import_from_url(vals)
        return super().create(vals_to_create)

    def write(self, vals):
        self._process_import_from_url(vals)
        return super().write(vals)
