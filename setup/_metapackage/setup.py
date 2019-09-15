import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-storage",
    description="Meta package for oca-storage Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-storage_backend',
        'odoo10-addon-storage_backend_s3',
        'odoo10-addon-storage_backend_sftp',
        'odoo10-addon-storage_file',
        'odoo10-addon-storage_image',
        'odoo10-addon-storage_image_category_pos',
        'odoo10-addon-storage_image_product',
        'odoo10-addon-storage_image_product_pos',
        'odoo10-addon-storage_media',
        'odoo10-addon-storage_media_product',
        'odoo10-addon-storage_thumbnail',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
