from setuptools import setup

setup(name='devmason_server',
      version='1.0pre-20091019',
      description='A Django implementation of a the pony-build server.',
      author = 'Eric Holscher, Jacob Kaplan-Moss',
      url = 'http://github.com/ericholscher/devmason-server',
      license = 'BSD',
      packages = ['devmason_server'],
      install_requires=['django-tagging>=0.3',
                        'django-piston>=0.2.2',
                        'django',
                        'mimeparse>=0.1.2'],
)
