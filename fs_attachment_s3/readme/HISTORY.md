## 18.0.1.2.1 (2025-10-20)

### Fixed

- Allow to use a prefix path and bucket in the directory_path on fs.storage
  When the directory_path parameter is configured as <bucketname>/<someprefix>
  the presigned url generation failed with a botocore error: "Invalid bucket name"

## 18.0.1.2.0 (2025-10-20)

### Features

- Adapt to handle {db_name} in directory_path. ([#db_name](https://github.com/OCA/storage/issues/db_name))
