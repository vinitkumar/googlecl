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
"""Handling authentication to Google for all services."""

from __future__ import with_statement

import logging
import os
import pickle
import stat
import googlecl
import oauth2client import client

CONF_FILE_NAME = '.googlecl.conf'
CLIENT_SECRET_FILE = os.env.get('CLIENT_SECRET_FILE')
LOGGER_NAME = __name__
LOG = logging.getLogger(LOGGER_NAME)


# Make Auth Oauth2 compatible.
def authenticate():
  filename = os.path.join(os.path.expanduser('~'), CONF_FILE_NAME)

  storage = Storage(filename)
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    if CLIENT_SECRET_FILE is None:
      print 'Please save and download the client secret file from your app console and try again!'
      return
    else:
     client_file = os.path.join(os.path.expanduser('~'), CLIENT_SECRET_FILE)
     flow = client.flow_from_clientsecrets(
             client_file,
             # add all the scopes below in comma separated strings
             # following scopes are tested and they work. Find out the cause of 
             # invalid scopes and other issues
             scope='https://www.google.com/m8/feeds/, https://picasaweb.google.com/data/, https://www.googleapis.com/auth/youtube', https://www.googleapis.com/auth/youtube'
             redirect_uri='urn:ietf:wg:oauth:2.0:oob')

     auth_uri = flow.step1_get_authorize_url()
     auth_code = raw_input('Enter the auth code: ')
     credentials = flow.step2_exchange(auth_code)
     storage.put(credentials)
  if credentials.access_token_expired:
    credentials.refresh(httplib2.Http())





