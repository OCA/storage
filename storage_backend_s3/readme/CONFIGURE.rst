Go to "Technical -> Storage backend -> Storage backend" and create a new backend of type "Amazon S3".


Example of configuration via env
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[storage_backend.name_of_your_backend]
backend_type=amazon_s3
served_by=external
base_url=https://your.cdn.domain.com
directory_path=foo  # if you want to store in this folder
url_include_directory_path=1  # if you want to include the above folder in the URL
aws_bucket=your-bucket-name
aws_file_acl=public-read
aws_access_key_id=$SECRET
aws_secret_access_key=$MORESECRET
aws_region=eu-central-1
