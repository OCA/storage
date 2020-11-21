# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
from contextlib import contextmanager
import os
from odoo import api
from odoo.addons.component.tests.common import TransactionComponentCase
from odoo import models


# Use TransientModel to avoid message about access rules
class CustomThumbnail(models.TransientModel):
    _name = 'custom.thumbnail'
    _inherit = [
        'thumbnail.mixin',
        'storage.file'
    ]


class TestThumbnailMixin(TransactionComponentCase):
    """
    Tests for thumbnail.mixin
    """

    def _init_test_model(self, model_cls):
        """
        It builds a model from model_cls in order to test abstract models.
        Note that this does not actually create a table in the database, so
        there may be some unidentified edge cases.
        :param model_cls: Class of model to initialize
        :return: Instance
        """
        registry = self.env.registry
        cr = self.env.cr
        inst = model_cls._build_model(registry, cr)
        model = self.env[model_cls._name].with_context(todo=[])
        model._prepare_setup()
        model._setup_base(partial=False)
        model._setup_fields(partial=False)
        model._setup_complete()
        model._auto_init()
        model.init()
        model._auto_end()
        self.test_model_record = self.env['ir.model'].search([
            ('name', '=', model._name),
        ])
        return inst

    def setUp(self):
        super(TestThumbnailMixin, self).setUp()
        self.env.registry.enter_test_mode()
        self._init_test_model(CustomThumbnail)
        self.test_obj = self.env[CustomThumbnail._name]
        self.storage_backend = self.env.ref(
            "storage_backend.default_storage_backend")
        self.stor_thumb_obj = self.env['storage.thumbnail']
        self.file_obj = self.env['storage.file']
        self._init_file()

    def tearDown(self):
        self.env.registry.leave_test_mode()
        super(TestThumbnailMixin, self).tearDown()

    def _init_file(self):
        path = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(path, "static/akretion-logo.png")
        with open(self.file_path) as f:
            data = f.read()
        self.filesize = len(data)
        self.filedata = base64.b64encode(data)
        self.filename = "akretion-logo.png"

    def _create_thumbnail(self):
        """
        Create a test.thumbnail
        :return:
        """
        values = {
            "name": self.filename,
            "backend_id": self.storage_backend.id,
            "file_size": self.filesize,
            "image_medium_url": self.filedata,
            "data": self.filedata,
        }
        return self.test_obj.create(values)

    @contextmanager
    def _custom_mock_thumbnail(self):
        self.count_prepare = self.count_get = self.count_compute = 0
        self_test = self

        @api.multi
        def _prepare_thumbnail(self, image, size_x, size_y, url_key):
            self_test.count_prepare += 1
            this = getattr(self, '_prepare_thumbnail')
            origin = getattr(this, 'origin')
            return origin(self, image, size_x, size_y, url_key)

        @api.model
        def get_or_create_thumbnail(self, size_x, size_y, url_key=None):
            self_test.count_get += 1
            this = getattr(self, 'get_or_create_thumbnail')
            origin = getattr(this, 'origin')
            return origin(self, size_x, size_y, url_key=url_key)

        @api.multi
        def _compute_data(self):
            self_test.count_compute += 1
            this = getattr(self, '_compute_data')
            origin = getattr(this, 'origin')
            return origin(self)

        self.stor_thumb_obj._patch_method(
            "_prepare_thumbnail", _prepare_thumbnail)
        self.test_obj._patch_method(
            "get_or_create_thumbnail", get_or_create_thumbnail)
        self.file_obj._patch_method("_compute_data", _compute_data)
        self.addCleanup(
            self.stor_thumb_obj._revert_method, "_prepare_thumbnail")
        self.addCleanup(
            self.test_obj._revert_method, "get_or_create_thumbnail")
        self.addCleanup(self.file_obj._revert_method, "_compute_data")
        yield

    def test_get_or_create_thumbnail(self):
        """
        Test the creation of the get_or_create_thumbnail.
        Ensure this function doesn't pass into get_or_create_thumbnail when
        it's not necessary.
        :return:
        """
        thumbnail = self._create_thumbnail()
        with self._custom_mock_thumbnail():
            # As we ask a thumbnail with size who doesn't exist yet, it should
            # create it.
            thumbnail.get_or_create_thumbnail(10, 10)
            self.assertEqual(1, self.count_prepare)
            self.assertEqual(0, self.count_compute)
            self.assertEqual(2, self.count_get)
            # Same here => Should pass into function.
            thumbnail.get_or_create_thumbnail(20, 20)
            self.assertEqual(2, self.count_prepare)
            self.assertEqual(0, self.count_compute)
            self.assertEqual(4, self.count_get)
            # But now it shouldn't!
            thumbnail.get_or_create_thumbnail(10, 10)
            self.assertEqual(2, self.count_prepare)
            self.assertEqual(0, self.count_compute)
            self.assertEqual(5, self.count_get)
        return
