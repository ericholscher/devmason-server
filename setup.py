try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='pony_server',
      version='1.0pre-20091019',
      description='A Django implementation of a the pony-build server.',
      author = 'Eric Holscher, Jacob Kaplan-Moss',
      url = 'http://github.com/jacobian/pony_server',
      license = 'BSD',
      packages = ['pony_server'],
)