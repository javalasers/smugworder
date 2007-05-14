#!/usr/bin/env python

from distutils.core import setup

setup(name='smugworder',
      version='1.0',
      description='Bulk keyword renaming for smugmug.com.',
      author='Will Robinson',
      author_email='willrobinson@gmail.com',
      license='GNU GPL 2.0',
      url='http://code.google.com/p/smugworder/',
      py_modules=['smugworder', 'xmltramp'],
      data_files=[('.', ['./LICENSE'])],
      )
