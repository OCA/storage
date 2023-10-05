import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-storage",
    description="Meta package for oca-storage Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-fs_attachment>=16.0dev,<16.1dev',
        'odoo-addon-fs_base_multi_image>=16.0dev,<16.1dev',
        'odoo-addon-fs_base_multi_media>=16.0dev,<16.1dev',
        'odoo-addon-fs_file>=16.0dev,<16.1dev',
        'odoo-addon-fs_file_demo>=16.0dev,<16.1dev',
        'odoo-addon-fs_image>=16.0dev,<16.1dev',
        'odoo-addon-fs_image_thumbnail>=16.0dev,<16.1dev',
        'odoo-addon-fs_product_brand_multi_image>=16.0dev,<16.1dev',
        'odoo-addon-fs_product_multi_image>=16.0dev,<16.1dev',
        'odoo-addon-fs_product_multi_media>=16.0dev,<16.1dev',
        'odoo-addon-fs_storage>=16.0dev,<16.1dev',
        'odoo-addon-image_tag>=16.0dev,<16.1dev',
        'odoo-addon-storage_backend>=16.0dev,<16.1dev',
        'odoo-addon-storage_file>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
