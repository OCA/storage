To configure a WebDAV storage with fs_folder, you need to install `webdav4[fsspec]` library to make the webdav protocol available in the FS Storage configuration.
- The Directory Path depends on your webdav provider. Exemple for Nextcloud : `/remote.php/dav/files/username/path/Directory`.
- Add the login and url informations in the Options:
```
{
    "base_url": "https://cloud.domain.com",
    "auth": ["username", "password"]
}
```
