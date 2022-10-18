import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                'boto3': 'boto3<1.16',
            },
        }
    },)
