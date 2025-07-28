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
            url.startswith(
                "/fs_x_accel_redirect/https/s3.amazonaws.com/"
                "test-bucket/dir/sub/fake_s3_file.txt?"
            ),
            "The end of the path should contain the path to the file "
            f"name and query parameters. ({url})",
        )

    def test_get_x_access_url_path(self):
        """Test the X-Accel-Redirect path generation."""
        url = self.fake_attachment_s3._get_x_accel_redirect_path()
        self.assertEqual(
            url,
            "/fs_x_accel_redirect/https/s3.amazonaws.com/dir/sub/fake_s3_file.txt",
            f"The X-Accel-Redirect path should match the expected format. ({url})",
        )

        # if we enclude the directory path in the file url
        # we get the bucket name in the path
        self.s3_backend.is_directory_path_in_url = True
        self.s3_backend.recompute_urls()
        url = self.fake_attachment_s3._get_x_accel_redirect_path()
        self.assertEqual(
            url,
            "/fs_x_accel_redirect/https/s3.amazonaws.com/"
            "test-bucket/dir/sub/fake_s3_file.txt",
            "The X-Accel-Redirect path should include the bucket "
            f"name when directory path is in URL. ({url})",
        )
