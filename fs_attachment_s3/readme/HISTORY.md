## 16.0.2.1.1 (2026-05-27)

### Bugfixes

- Allow to use a prefix path and bucket in the directory_path on fs.storage
  When the directory_path parameter is configured as <bucketname>/<someprefix>
  the presigned url generation failed with a botocore error: "Invalid bucket name". ([#b17de9](https://github.com/OCA/storage/issues/b17de9))


## 16.0.2.1.0 (2026-05-26)

### Features

- Adapt to handle {db_name} in directory_path. ([#db_name](https://github.com/OCA/storage/issues/db_name))
