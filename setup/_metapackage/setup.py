import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-storage",
    description="Meta package for oca-storage Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-storage_backend>=15.0dev,<15.1dev',
        'odoo-addon-storage_backend_ftp>=15.0dev,<15.1dev',
        'odoo-addon-storage_backend_s3>=15.0dev,<15.1dev',
        'odoo-addon-storage_backend_sftp>=15.0dev,<15.1dev',
        'odoo-addon-storage_file>=15.0dev,<15.1dev',
        'odoo-addon-storage_image>=15.0dev,<15.1dev',
        'odoo-addon-storage_image_backend_migration>=15.0dev,<15.1dev',
        'odoo-addon-storage_image_product>=15.0dev,<15.1dev',
        'odoo-addon-storage_import_image_advanced>=15.0dev,<15.1dev',
        'odoo-addon-storage_media>=15.0dev,<15.1dev',
        'odoo-addon-storage_thumbnail>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
