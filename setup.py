#from distutils.core import setup
from setuptools import setup, find_packages
setup(
  name = 'casambi',
  packages = find_packages('src'),
  package_dir = {'': 'src'},
  version = '0.0137',
  license='MIT',
  description = 'Library to control Casambi light through cloudapi',
  author = 'Olof Hellqvist',
  author_email = 'olof.hellqvist@gmail.com',
  url = 'https://github.com/olofhellqvist/casambi',
  download_url = 'https://github.com/olofhellqvist/casambi/archive/v_01.tar.gz',
  keywords = ['casambi', 'light'],
  python_requires='>=3.6',
  install_requires=[
          'requests',
          'websocket-client',
          'pyyaml'
      ],
  extras_require={
        'tests': [
            'pyyaml',
        ]
    },
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
  ],
)
