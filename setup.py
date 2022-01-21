
from setuptools import setup, find_namespace_packages

packages = find_namespace_packages('src', include=['craftr.*'])
setup(
  name='craftr-dsl',
  version='0.1.0',
  packages=packages,
  package_dir = {'': 'src'},
)