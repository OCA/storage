-- Neutralize S3 credentials on copied databases.
UPDATE storage_backend
SET aws_secret_access_key = NULL
WHERE backend_type = 'amazon_s3';
