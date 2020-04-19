from distutils.core import setup
setup(
  name = 'Casambi',
  packages = ['casambi'],
  version = '0.01',
  license='MIT',
  description = 'Library to control Casambi light through cloudapi',
  author = 'Olof Hellqvist',
  author_email = 'your.email@domain.com',
  url = 'https://github.com/olofhellqvist/casambi',
  download_url = 'https://github.com/olofhellqvist/casambi/archive/v_01.tar.gz',
  keywords = ['casambi', 'light'],
  install_requires=[
          'requests',
          'websocket',
          'pyyaml'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
  ],
)
