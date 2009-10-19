from setuptools import setup

setup(name='pony_server',
      version='1.0pre-20091019',
      description='A Django implementation of a the pony-build server.',
      author = 'Eric Holscher, Jacob Kaplan-Moss',
      url = 'http://github.com/jacobian/pony_server',
      license = 'BSD',
      packages = ['pony_server'],
      install_requires=['Djblets>=0.5.4', 
                        'django-tagging>=0.3',
                        'django-piston>=0.2.2',
                        'mimeparse>=0.1.2'],
)