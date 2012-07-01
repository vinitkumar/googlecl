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


"""Subfunction for the Google command line tool, GoogleCL.

This function handles the authentication and storage of
credentials for the services which use OAuth2
"""

import httplib2
import logging
import pickle
import os
import googlecl
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

LOG = logging.getLogger(googlecl.LOGGER_NAME)

TOKENS_FILENAME_FORMAT = 'dca_%s_%s'

def authenticate(email, servicename, doc, http, client_id,
                 client_secret, force_auth=False):
  """ Authenticates an provided http object,
  Prompts for user confirmation if necessary, and stores the credentials

  Args:
    email: The email address of the user
    servicename: The service which requires authentication
    doc: Documentation for the service (for determining scopes)
    http: The object being authenticated

  Returns:
    The authorized object
  """
  tokens_path = googlecl.get_data_path(TOKENS_FILENAME_FORMAT %
                                     (email, servicename),
                                     create_missing_dir=True)
  storage = Storage(tokens_path)
  credentials = storage.get()
  if credentials is None or credentials.invalid or force_auth:
    # Works with google-api-python-client-1.0beta2, but not with
    # beta4.  They're working on a way to allow deleting credentials.
    #storage.put(None)
    desiredcred = ""
    for arg in doc['auth']['oauth2']['scopes']:
      desiredcred = desiredcred + arg + ' '
    FLOW = OAuth2WebServerFlow(client_id, client_secret,
      scope=desiredcred, user_agent='discoverycl')
    credentials = run(FLOW, storage)
  return credentials.authorize(http)
