# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import with_statement

try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup
import os
import shutil
packages =['googlecl',
           'googlecl.blogger',
           'googlecl.calendar',
           'googlecl.config',
           'googlecl.contacts',
           'googlecl.docs',
           'googlecl.picasa',
           'googlecl.youtube',
           'googlecl.finance',
           'googlecl.discovery']

SCRIPT_TO_INSTALL = 'src/google'
SCRIPT_TO_RENAME = 'src/google.py'

# Safely move src/google.py to src/google
if os.path.exists(SCRIPT_TO_INSTALL):
  # Read size is 128*20 for no good reason.
  # Just want to avoid reading in the whole file, and read in a multiple of 128.
  # Shamelessly stole this function from googlecl/docs/base.py
  def _md5_hash_file(path, read_size=2560):
    """Return a binary md5 checksum of file at path."""
    import hashlib
    hash_function = hashlib.md5()
    with open(path, 'r') as my_file:
      data = my_file.read(read_size)
      while data:
        hash_function.update(data)
        data = my_file.read(read_size)
    return hash_function.digest()
  # If running from trunk, SCRIPT_TO_RENAME should exist.
  # For the distributed tarball, they should not.
  if os.path.exists(SCRIPT_TO_RENAME) and\
     not _md5_hash_file(SCRIPT_TO_INSTALL) == _md5_hash_file(SCRIPT_TO_RENAME):
    print SCRIPT_TO_INSTALL + ' exists and is not the same as ' +\
          SCRIPT_TO_RENAME
    print 'Not trusting ' + SCRIPT_TO_INSTALL
    print 'Please update it or remove it.'
    exit(-1)
else:
  shutil.copy(SCRIPT_TO_RENAME, SCRIPT_TO_INSTALL)

long_desc = """The Google Data APIs allow programmatic access to
various Google services.  This package wraps a subset of those APIs into a
command-line tool that makes it easy to do things like posting to a Blogger
blog, uploading files to Picasa, or editing a Google Docs file."""

setup(name="google_cl",
      version="0.9.15",
      description="Use (some) Google services from the command line",
      author=['Tom H. Miller', 'Vinit Kumar'],
      author_email=['tom.h.miller@gmail.com', 'vinit.kumar@changer.nl'],
      url="http://github.com/vinitkumar/googlecl",
      license="Apache Software License",
      packages=packages,
      package_dir={'googlecl':'src/googlecl'},
      scripts=[SCRIPT_TO_INSTALL],
      install_requires=['gdata ==2.0.18'],
      long_description=long_desc,
      classifiers=[
          'Topic :: Internet :: WWW/HTTP',
          'Environment :: Console',
          'Development Status :: 4 - Beta',
          'Operating System :: POSIX',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop'
      ]
     )
