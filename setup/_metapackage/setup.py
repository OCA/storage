import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-storage",
    description="Meta package for oca-storage Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-storage_backend',
        'odoo12-addon-storage_backend_s3',
        'odoo12-addon-storage_backend_sftp',
        'odoo12-addon-storage_file',
        'odoo12-addon-storage_image',
        'odoo12-addon-storage_image_product',
        'odoo12-addon-storage_thumbnail',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
