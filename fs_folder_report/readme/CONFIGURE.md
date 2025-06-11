By default, reports are stored in the Odoo database if configured to do so. However, this module allows you to specify on the report definition whether the report should be stored in a folder structure associated to the record.

On the report definition, if a FsFolder field is defined on the model, you can choose to store the report in a folder structure by activating the boolean field "Store in folder structure".
Two additional fields are available to specify the folder structure:
- **"Folder Field"**: This field allows you to select the FsFolder field on the model that will be used to determine the folder where the report will be stored.
- **"Folder Path"**: This field allows you to specify a custom path within the folder structure where the report will be stored. The value of the field will be evaluated in a context where the current record is available as `record` and time is available as `time` (e.g., `record.name`, `time.strftime('%Y-%m-%d')`, etc.) This allows you to create dynamic paths based on the record's attributes.
