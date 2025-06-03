The module is a technical module providing a new field type to Odoo. It is not intended to be used directly by end-users. It is intended to be used by developers to create new modules that need to manage files in an external filesystem.

The **FsFolder** field type is a specialized field type that can be used in any Odoo model. When an Odoo developer declares a field of this type on a model and the related form view, the field will display a specialized widget that allows the user to interact with a folder in an external filesystem.

The field is linked to a filesystem backend that must be configured in Odoo. The backend configuration is available in the 'Settings' -> 'Technical' -> 'FS Storage' menu. It is possible to define a default backend for all the fields of this type in the Odoo configuration or to define a specific backend for each model or field.

In the following documentation, we will see:

* how to declare a field of this type in a model
* how the security is managed
* how you can interact with the filesystem
* how you can customize the field behavior

## Field declaration

To declare a field of this type in a model, you need to import the field type and declare it in the model definition. By default, the field declaration requires no
parampeters.

```python
from odoo import models
from odoo.addons.fs_folder import fields as fs_fields

class MyModel(models.Model):
    _name = 'my.model'

    fs_folder_field = fs_fields.FsFolder()

```

The new field type comes with a specific way to initialize the field. Even if the field is not yet initialized, the value of the field will be an instance of the `FsFolderValue` class. But as for empty recordsets in Odoo, the value will be considered as `False` in a boolean context or `None` in a null context.

```python

from odoo.addons.fs_folder.fields import FsFolderValue

record = self.env['my.model'].create({})
assert isinstance(record.fs_folder_field, FsFolderValue)
assert not record.fs_folder_field
assert record.fs_folder_field is None

```

To initialize the field, you can call the `initialize` method on the field value. This method will create the folder in the filesystem if it does not exist yet.

```python

record.fs_folder_field.initialize()

```

The creation of the folder in the filesystem requires 2 informations:

* The path where the folder will be created
* The name of the folder

By default, the path is the root folder of the filesystem. In some cases you may want to create the folder in a specific subfolder of the filesystem depending on the record data (or not). In this case, you can define into the field definition a method that will be called to get the path where the folder will be created. 

```python
import fsspec

class MyModel(models.Model):
    _name = 'my.model'

    fs_folder_field = fs_fields.FsFolder(
        create_parent_get='get_folder_path',
    )

    def get_folder_path(self, fs: fsspec.AbstractFileSystem) -> dict[int, list[str]]:
        result = {}
        for record in self:
            result[record.id] = ['my', 'subfolder']
        return result

```

In this example, the `get_folder_path` method will be called to get the path where the folder will be created. The method must return a dictionary where the key is the record id and the value is a list of strings representing the path where the folder will be created. (The list of strings will be joined with the approprisate separator defined by the specific filesystem used to create the folder).

In the same way, you can define a method to get the folder name (by default the folder name is the record display name).

```python

class MyModel(models.Model):
    _name = 'my.model'

    reference = fields.Char(required=True)

    fs_folder_field = fs_fields.FsFolder(
        create_name_get='get_folder_name',
    )

    def get_folder_name(self, fs: fsspec.AbstractFileSystem) -> dict[int, str]:
        result = {}
        for record in self:
            result[record.id] = record.reference
        return result

```

In this example, the `get_folder_name` method will be called to get the folder name. The method must return a dictionary where the key is the record id and the value is the folder name.

For advanced use cases, you can also define the method that will ensure the creation of the folder in the filesystem and assign the value to the field. This method must return a list of `FsFolderValue`.

```python

class MyModel(models.Model):
    _name = 'my.model'

    reference = fields.Char(required=True)

    fs_folder_field = fs_fields.FsFolder(
        create_get='create_folder',
    )

    def create_folder(self, fs: fsspec.AbstractFileSystem) -> list[FsFolderValue]:
        result = []
        value_adapter = self.env["fs.folder.field.value.adapter"]
        storage_code = self.env[
                "fs.storage"
            ].get_default_storage_code_for_fs_content(self._name, 'fs_folder_field')
        for record in self:
            path = f'my/subfolder/{record.reference}'
            fs.mkdir(path)
            record.fs_folder_field = value_adapter._created_folder_name_to_stored_value(
                path, storage_code, fs
            )
            result.append(record.fs_folder_field)
        return result

```

Last but not least, 2 additional method hooks are available to customize the behavior of the field:

* create_additional_kwargs_get: This method will be called to get additional keyword arguments to pass to the `fs.mkdir` method when creating the folder.
* create_post_process: This method will be called after the folder creation to do some additional processing.


## Security

> **Important:** The security of the field should be managed by the filesystem backend.

### In the python code

The initialization of the field value is only allowed if the user has write access to the record. From the field value, the user can get access to the filesystem client and interact with the filesystem. The filesystem is rooted in the folder itself. The user can only interact with the folder and its children without being able to go up in the filesystem.

### In the form view through widget

The addon comes with a specific widget that will be used to display the field in the form view. The widget will display the folder content and allow the user to interact with it. The user can create, delete, rename, download and upload files and folders. The user can also navigate into the filesystem. All theses operations are made available by
methods provided by the abstract model 'fs.folder.field.web.api'. A first level of security is provided by this API. Any operation modifying the filesystem will allowed only if the user has write access to the record and any operation reading the filesystem will be allowed only if the user has read access to the record.

## Interacting with the filesystem

To interact with the filesystem you can simply use the filesystem client provided by the field value.

```python

record.fs_folder_field.fs.mkdir('my/subfolder')
with record.fs_folder_field.fs.open('my/subfolder/myfile.txt', 'w') as f:
    f.write('Hello, world!')

```

The api also provides higl-level methods to interact with the filesystem and ease the access to the files. For example, if you need to provide a download link to a file, you can use the `get_url_for_download` method from the abstract model 'fs.folder.field.web.api'.

```python
api = self.env['fs.folder.field.web.api']
url = api.get_url_for_download(record.id,  record._name, "fs_folder_field", 'my/subfolder/myfile.txt')
```


## Customizing the field behavior

As specified above, you can define some methods to customize the field behavior. During the process of creating a directory in a filesystem, 1 additional mechanism comes into play to guarantee the conformity of the directory created.

### Folder name conformity

When it comes to creating a folder in the filesystem, we must prevent the use of special characters that could cause problems. This is done by default by the field when creating the folder by replacing the characters that are not allowed by the filesystem by an underscore. You can control this behavior on the
'fs.storage' form view. A field is available to disable this behavior and another one to define the character to use as a replacement. If the behavior is disabled, the field will raise an error if the folder name is not conform. (This applies to the full path of the folder).

### Other customizations

In addition you can:

* override the adapter that will be used to convert the field value to a stored value and vice versa. The adapter is a model that must extend the 'fs.folder.field.value.adapter' abstract model.
* extend/override the api model used by the widget to interact with the filesystem. The api model must extend the 'fs.folder.field.web.api' abstract model.
* extend/override the widget itself
