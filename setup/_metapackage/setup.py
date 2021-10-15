import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-storage",
    description="Meta package for oca-storage Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-storage_backend',
        'odoo14-addon-storage_backend_s3',
        'odoo14-addon-storage_backend_sftp',
        'odoo14-addon-storage_file',
        'odoo14-addon-storage_image',
        'odoo14-addon-storage_image_import',
        'odoo14-addon-storage_image_product',
        'odoo14-addon-storage_image_product_brand',
        'odoo14-addon-storage_image_product_brand_import',
        'odoo14-addon-storage_image_product_import',
        'odoo14-addon-storage_image_product_pos',
        'odoo14-addon-storage_media',
        'odoo14-addon-storage_media_product',
        'odoo14-addon-storage_thumbnail',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
