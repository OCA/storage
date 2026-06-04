import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon=True,
    # The dependency are not strictly required for the module 
    # to be installed, but they are required to ensure
    # compatibility with the initial implemenation of the module
    # where the server_environment was a direct dependency of
    # the module even if not used by the user.
    install_requires=['odoo-addon-fs-storage-environment'],
)
