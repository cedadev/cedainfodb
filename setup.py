from setuptools import setup, find_packages

setup(
    name='cedainfodb',
    version='1.0.0',
    author='Andrew Harwood',
    author_email='andrew.harwood@stfc.ac.uk',
    description='CEDA services catalogue',
    package_dir = {'': 'cedainfo'},
    package_data={'': ['templates/*', 'templates/*/*', 'templates/*/*/*', 'static/*']},
    packages=['cedainfoapp', 'cedainfo'],
)

