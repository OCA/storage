16.0.1.0.1 (2023-09-29)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Add a *url_path* property on the *FSFileValue* object. This property
  allows you to easily get access to the relative path of the file on
  the filesystem. This value is only available if the filesystem storage
  is configured with a *Base URL* value. (`#281 <https://github.com/OCA/storage/issues/281>`_)


**Bugfixes**

- The *url_path*, *url* and *internal_url* properties on the *FSFileValue*
  object return *None* if the information is not available (instead of *False*).

  The *url* property on the *FSFileValue* object returns the filesystem url nor
  the url field of the attachment. (`#281 <https://github.com/OCA/storage/issues/281>`_)
