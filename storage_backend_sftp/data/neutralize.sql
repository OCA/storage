-- Neutralize SFTP credentials on copied databases.
UPDATE storage_backend
SET sftp_password = NULL,
    sftp_ssh_private_key = NULL
WHERE backend_type = 'sftp';
