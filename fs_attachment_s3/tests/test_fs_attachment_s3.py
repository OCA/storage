# Copyright 2025 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from .common import TestFSAttachmentS3Common


class TestFSAttachementS3(TestFSAttachmentS3Common):
    def test_get_x_access_url_path_s3_signed(self):
        """Test the X-Accel-Redirect path generation for S3 storage."""
        self.s3_backend.write(
            {
                "s3_uses_signed_url_for_x_accel_redirect": True,
                "s3_signed_url_expiration": 60,
            }
        )

        url = self.fake_attachment_s3._get_x_accel_redirect_path()
        self.assertTrue(
            url.startswith("/s3tst/"), "The URL should start with the storage code."
        )
        _, storage_code, bucket, file_path = url.split("/", 3)
        self.assertEqual(
            storage_code,
            "s3tst",
            "The x-accel redirect path must be prefixed with the storage code.",
        )
        self.assertEqual(
            bucket,
            "test-bucket",
            "The first part of the path should be the bucket name.",
        )
        self.assertTrue(
            file_path.startswith("dir/sub/fake_s3_file.txt?"),
            "The end of the path should contain the path to thefile name and query parameters.",
        )

    def test_get_x_access_url_path(self):
        """Test the X-Accel-Redirect path generation."""
        url = self.fake_attachment_s3._get_x_accel_redirect_path()
        self.assertEqual(
            url,
            "/s3tst/dir/sub/fake_s3_file.txt",
            "The X-Accel-Redirect path should match the expected format.",
        )

        # if we enclude the directory path in the file url
        # we get the bucket name in the path
        self.s3_backend.is_directory_path_in_url = True
        self.s3_backend.recompute_urls()
        url = self.fake_attachment_s3._get_x_accel_redirect_path()
        self.assertEqual(
            url,
            "/s3tst/test-bucket/dir/sub/fake_s3_file.txt",
            "The X-Accel-Redirect path should include the bucket "
            "name when directory path is in URL.",
        )
