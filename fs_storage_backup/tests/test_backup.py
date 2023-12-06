from odoo.tests.common import TransactionCase


class TestBackup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fs_storage = cls.env.ref("fs_storage.default_fs_storage")
        cls.fs_storage.use_for_backup = True
        cls.fs_storage.backup_dir = "backups"
        cls.fs_storage.backup_filename_format = "backup-%(db)s-%(dt)s.%(ext)s"
        cls.fs_storage.backup_keep_time = 7

    def test_with_filestore(self):
        self.fs_storage.backup_include_filestore = True
        old_counts = {}
        for fs_storage in self.env["fs.storage"].search(
            [("use_for_backup", "=", True)]
        ):
            fs_storage.fs.makedirs(fs_storage.backup_dir, exist_ok=True)
            old_counts[fs_storage.id] = len(
                fs_storage.fs.ls(fs_storage.backup_dir, detail=False)
            )
        self.env["fs.storage"].cron_backup_db()  # Backup all locations
        for fs_storage in self.env["fs.storage"].search(
            [("use_for_backup", "=", True)]
        ):
            new_count = len(fs_storage.fs.ls(fs_storage.backup_dir, detail=False))
            self.assertEqual(old_counts[fs_storage.id] + 1, new_count)

    def test_without_filestore(self):
        self.fs_storage.fs.makedirs(self.fs_storage.backup_dir, exist_ok=True)
        files = self.fs_storage.fs.ls(self.fs_storage.backup_dir, detail=False)
        old_count = len(list(filter(lambda f: f.endswith(".dump"), files)))
        self.fs_storage.backup_include_filestore = False
        self.fs_storage.backup_db()
        files = self.fs_storage.fs.ls(self.fs_storage.backup_dir, detail=False)
        new_count = len(list(filter(lambda f: f.endswith(".dump"), files)))
        self.assertEqual(old_count + 1, new_count)

    def test_cleanup_no_dir(self):
        self.fs_storage.backup_dir = "backups123"
        with self.assertLogs(level="ERROR"):
            self.fs_storage.cleanup_old_backups()

    def test_no_connection(self):
        fs_storage = self.env["fs.storage"].create(
            {
                "name": "FTP",
                "code": "ftp",
                "protocol": "ftp",
                "directory_path": ".",
                "options": '{"host": "host", "port": 21}',  # Non existent host
                "use_for_backup": True,
            }
        )
        with self.assertLogs(level="ERROR"):
            fs_storage.backup_db()
