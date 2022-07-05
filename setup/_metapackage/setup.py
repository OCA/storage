import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-storage",
    description="Meta package for oca-storage Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-storage_backend',
        'odoo13-addon-storage_backend_ftp',
        'odoo13-addon-storage_backend_s3',
        'odoo13-addon-storage_backend_sftp',
        'odoo13-addon-storage_file',
        'odoo13-addon-storage_image',
        'odoo13-addon-storage_image_backend_migration',
        'odoo13-addon-storage_image_product',
        'odoo13-addon-storage_image_product_brand',
        'odoo13-addon-storage_import_image_advanced',
        'odoo13-addon-storage_media',
        'odoo13-addon-storage_media_product',
        'odoo13-addon-storage_thumbnail',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
