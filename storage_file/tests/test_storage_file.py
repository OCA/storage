# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from urllib import parse

import mock

from odoo.exceptions import AccessError, UserError

from odoo.addons.component.tests.common import TransactionComponentCase


class StorageFileCase(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.backend = self.env.ref("storage_backend.default_storage_backend")
        data = b"This is a simple file"
        self.filesize = len(data)
        self.filedata = base64.b64encode(data)
        self.filename = "test of my_file.txt"

    def _create_storage_file(self):
        return self.env["storage.file"].create(
            {
                "name": self.filename,
                "backend_id": self.backend.id,
                "data": self.filedata,
            }
        )

    def test_create_and_read_served_by_odoo(self):
        stfile = self._create_storage_file()
        self.assertEqual(stfile.data, self.filedata)
        self.assertEqual(stfile.mimetype, u"text/plain")
        self.assertEqual(stfile.extension, u".txt")
        self.assertEqual(stfile.filename, u"test of my_file")
        self.assertEqual(stfile.relative_path, u"test-of-my_file-%s.txt" % stfile.id)
        url = parse.urlparse(stfile.url)
        self.assertEqual(url.path, "/storage.file/test-of-my_file-%s.txt" % stfile.id)
        self.assertEqual(stfile.file_size, self.filesize)

    def test_get_from_slug_name_with_id(self):
        stfile = self._create_storage_file()
        stfile2 = self.env["storage.file"].get_from_slug_name_with_id(
            "test-of-my_file-%s.txt" % stfile.id
        )
        self.assertEqual(stfile, stfile2)
        # the method parse the given string to find the id. The id is the
        # last sequence of digit starting with '-'
        stfile2 = self.env["storage.file"].get_from_slug_name_with_id(
            "test-999-%s.txt2" % stfile.id
        )
        self.assertEqual(stfile, stfile2)
        stfile2 = self.env["storage.file"].get_from_slug_name_with_id(
            "test-999-%s" % stfile.id
        )
        self.assertEqual(stfile, stfile2)

    def test_url(self):
        stfile = self._create_storage_file()
        params = self.env["ir.config_parameter"].sudo()
        base_url = params.get_param("web.base.url")
        # served by odoo
        self.assertEqual(
            stfile.url,
            "{}/storage.file/test-of-my_file-{}.txt".format(base_url, stfile.id),
        )
        # served by external
        stfile.backend_id.update(
            {
                "served_by": "external",
                "base_url": "https://foo.com",
                "directory_path": "baz",
            }
        )
        # path not included
        self.assertEqual(
            stfile.url, "https://foo.com/test-of-my_file-{}.txt".format(stfile.id)
        )
        # path included
        stfile.backend_id.url_include_directory_path = True
        self.assertEqual(
            stfile.url, "https://foo.com/baz/test-of-my_file-{}.txt".format(stfile.id)
        )

    def test_create_store_with_hash(self):
        self.backend.filename_strategy = "hash"
        stfile = self._create_storage_file()
        self.assertEqual(stfile.data, self.filedata)
        self.assertEqual(stfile.mimetype, u"text/plain")
        self.assertEqual(stfile.extension, u".txt")
        self.assertEqual(stfile.filename, u"test of my_file")
        self.assertEqual(
            stfile.relative_path, u"13/1322d9ccb3d257095185b205eadc9307aae5dc84"
        )

    def test_missing_name_strategy(self):
        self.backend.filename_strategy = None
        with self.assertRaises(UserError):
            self._create_storage_file()

    def test_create_and_read_served_by_external(self):
        self.backend.write(
            {"served_by": "external", "base_url": "https://cdn.example.com"}
        )
        stfile = self._create_storage_file()
        self.assertEqual(stfile.data, self.filedata)
        self.assertEqual(
            stfile.url, "https://cdn.example.com/test-of-my_file-%s.txt" % stfile.id
        )
        self.assertEqual(stfile.file_size, self.filesize)

    def test_read_bin_size(self):
        stfile = self._create_storage_file()
        self.assertEqual(stfile.with_context(bin_size=True).data, b"21.00 bytes")

    def test_cannot_update_data(self):
        stfile = self._create_storage_file()
        data = base64.b64encode(b"This is different data")
        with self.assertRaises(UserError):
            stfile.write({"data": data})

        # check that the file have been not modified
        self.assertEqual(stfile.read()[0]["data"], self.filedata)

    def test_unlink(self):
        # Do not commit during the test
        self.cr.commit = lambda: True
        stfile = self._create_storage_file()

        backend = stfile.backend_id
        relative_path = stfile.relative_path
        stfile.unlink()

        # Check the the storage file is set to delete
        # and the file still exist on the storage
        self.assertEqual(stfile.to_delete, True)
        self.assertIn(relative_path, backend.list_files())

        # Run the method to clean the storage.file
        self.env["storage.file"]._clean_storage_file()

        # Check that the file is deleted
        files = (
            self.env["storage.file"]
            .with_context(active_test=False)
            .search([("id", "=", stfile.id)])
        )
        self.assertEqual(len(files), 0)
        self.assertNotIn(relative_path, backend.list_files())

    def test_public_access1(self):
        """
        Test the public access (when is_public on the backend).
        When checked, the public user should have access to every content
        (storage.file).
        For this case, we use this public user and try to read a field on
        no-public storage.file.
        An exception should be raised because the backend is not public
        :return: bool
        """
        storage_file = self._create_storage_file()
        # Ensure it's False (we shouldn't specify a is_public = False on the
        # storage.backend creation because False must be the default value)
        self.assertFalse(storage_file.backend_id.is_public)
        # Public user used on the controller when authentication is 'public'
        public_user = self.env.ref("base.public_user")
        with self.assertRaises(AccessError):
            # BUG OR NOT with_user doesn't invalidate the cache...
            # force cache invalidation
            self.env.cache.invalidate()
            self.env[storage_file._name].with_user(public_user).browse(
                storage_file.ids
            ).name
        return True

    def test_public_access2(self):
        """
        Test the public access (when is_public on the backend).
        When checked, the public user should have access to every content
        (storage.file).
        For this case, we use this public user and try to read a field on
        no-public storage.file.
        This public user should have access because the backend is public
        :return: bool
        """
        storage_file = self._create_storage_file()
        storage_file.backend_id.write({"is_public": True})
        self.assertTrue(storage_file.backend_id.is_public)
        # Public user used on the controller when authentication is 'public'
        public_user = self.env.ref("base.public_user")
        env = self.env(user=public_user)
        storage_file_public = env[storage_file._name].browse(storage_file.ids)
        self.assertTrue(storage_file_public.name)
        return True

    def test_public_access3(self):
        """
        Test the public access (when is_public on the backend).
        When checked, the public user should have access to every content
        (storage.file).
        For this case, we use the demo user and try to read a field on
        no-public storage.file (no exception should be raised)
        :return: bool
        """
        storage_file = self._create_storage_file()
        # Ensure it's False (we shouldn't specify a is_public = False on the
        # storage.backend creation because False must be the default value)
        self.assertFalse(storage_file.backend_id.is_public)
        demo_user = self.env.ref("base.user_demo")
        env = self.env(user=demo_user)
        storage_file_public = env[storage_file._name].browse(storage_file.ids)
        self.assertTrue(storage_file_public.name)
        return True

    def test_get_backend_from_param(self):
        storage_file = self._create_storage_file()
        with mock.patch.object(
            type(self.env["ir.config_parameter"]), "get_param"
        ) as mocked:
            mocked.return_value = str(storage_file.backend_id.id)
            self.assertEqual(
                self.env["storage.backend"]._get_backend_id_from_param(
                    self.env, "foo.baz"
                ),
                storage_file.backend_id.id,
            )
        with mock.patch.object(
            type(self.env["ir.config_parameter"]), "get_param"
        ) as mocked:
            mocked.return_value = "storage_backend.default_storage_backend"
            self.assertEqual(
                self.env["storage.backend"]._get_backend_id_from_param(
                    self.env, "foo.baz"
                ),
                storage_file.backend_id.id,
            )

    def test_empty(self):
        # get_url is called on new records
        empty = self.env["storage.file"].new({})._get_url()
        self.assertEqual(empty, "/")
