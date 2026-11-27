-- Neutralize FTP credentials on copied databases.
UPDATE storage_backend
SET ftp_password = NULL
WHERE backend_type = 'ftp';
