from setuptools import setup

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='chunk_nordic',
      version='0.2.0',
      description='Yet another TCP-over-HTTP(S) tunnel',
      url='https://github.com/Snawoot/chunk-nordic',
      author='Vladislav Yarmak',
      author_email='vladislav-ex-src@vm-0.com',
      license='MIT',
      packages=['chunk_nordic'],
      python_requires='>=3.5.3',
      setup_requires=[
          'wheel',
      ],
      install_requires=[
          'aiohttp>=3.4.4',
          'sdnotify>=0.3.2',
      ],
      extras_require={
          'uvloop': 'uvloop>=0.11.0',
          'dev': [
              'pytest>=3.0.0',
              'pytest-cov',
              'pytest-asyncio',
              'pytest-timeout',
              'pylint',
              'tox',
              'coverage',
              'async_generator',
              'setuptools>=38.6.0',
              'wheel>=0.31.0',
              'twine>=1.11.0',
              'cryptography>=1.6',
          ],
      },
      entry_points={
          'console_scripts': [
              'chunk-server=chunk_nordic.server:main',
              'chunk-client=chunk_nordic.client:main',
          ],
      },
      classifiers=[
          "Programming Language :: Python :: 3.5",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Development Status :: 4 - Beta",
          "Environment :: No Input/Output (Daemon)",
          "Intended Audience :: System Administrators",
          "Natural Language :: English",
          "Topic :: Internet",
          "Topic :: Security",
      ],
      long_description=long_description,
      long_description_content_type='text/markdown',
      zip_safe=True)
