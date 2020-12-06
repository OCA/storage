import base64
import os
from operator import attrgetter

from odoo.fields import first

from odoo.addons.component.tests.common import TransactionComponentCase

from .models import ModelTest


class TestStorageThumbnail(TransactionComponentCase):
    def setUp(self):
        super().setUp()

        # Register model inheritance
        ModelTest._build_model(self.env.registry, self.env.cr)
        self.env.registry.setup_models(self.env.cr)
        ctx = dict(self.env.context, update_custom_fields=True, module="base")
        self.env.registry.init_models(self.env.cr, [ModelTest._name], ctx)

        # create model
        path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(path, "static/akretion-logo.png"), "rb") as f:
            data = f.read()
        self.filesize = len(data)
        self.filedata = base64.b64encode(data)
        self.filename = "akretion-logo.png"

    def tearDown(self):
        super().tearDown()
        env = self.env
        del env.registry.models[ModelTest._name]
        parents = ModelTest._inherit
        parents = [parents] if isinstance(parents, str) else (parents or [])
        # keep a copy to be sure to not modify the original _inherit
        parents = list(parents)
        parents.extend(ModelTest._inherits.keys())
        parents.append("base")
        funcs = [attrgetter(kind + "_children") for kind in ["_inherits", "_inherit"]]
        for parent in parents:
            for func in funcs:
                children = func(env.registry[parent])
                if ModelTest._name in children:
                    # at this stage our cls is referenced as children of
                    # parent -> must un reference it
                    children.remove(ModelTest._name)

    def _create_thumbnail(self):
        # create thumbnail
        vals = {"name": "TEST THUMB"}
        self.thumbnail = self.env["storage.thumbnail"].create(vals)

    def _create_model(self, resize=False):
        if resize:
            self.env["ir.config_parameter"].sudo().create(
                {"key": "storage.image.resize.format", "value": ".webp"}
            )
        vals = {"name": self.filename, "image_medium_url": self.filedata}
        self.image = self.env["model.test"].create(vals)

    def test_thumbnail(self):
        self._create_thumbnail()
        self.assertTrue(self.thumbnail.url)
        file_id = self.thumbnail.file_id
        self.assertTrue(file_id)

        self.thumbnail.unlink()
        self.assertTrue(file_id.to_delete)

    def test_model(self):
        self._create_model()
        self.assertTrue(self.image.url)
        self.assertEqual(2, len(self.image.thumbnail_ids))
        self.assertEqual(".png", first(self.image.thumbnail_ids).extension)

    def test_model_resize(self):
        self._create_model(resize=True)
        self.assertIn("webp", first(self.image.thumbnail_ids).url)
        self.assertEqual(".webp", first(self.image.thumbnail_ids).extension)
