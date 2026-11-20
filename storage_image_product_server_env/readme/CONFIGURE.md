Image tags can be configured in the server environment files using the
`image_tag` section for global values, and `image_tag.<tech_name>` for
a specific tag.

When upgrading `storage_image_product` from a version depending on
`server_environment`, this module is installed automatically if any of
these sections is found in the configuration.
