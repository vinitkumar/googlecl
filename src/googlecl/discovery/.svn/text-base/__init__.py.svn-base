# Copyright (C) 2011 Google Inc.
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

"""Subprogram for GoogleCL which handles all requests 
   using the Discovery service

This program uses the Discovery API to take interact with other APIs.
It is called when GoogleCL cannot identify a requested service as using gdata.
Syntax is generally similar to using gdata services.

General usage (omitting initial 'google'):
  > <service> <method path> <parameters>
  > help <service> <path>
  > format <service> <method path>

Examples:
  # Creating a new shortened goo.gl URL
  urlshortener insert --body {"longUrl":"<longUrl>"}

  # Getting data for a shortened goo.gl URL
  urlshortener url get <shortUrl>
"""

import httplib2
import logging

import googlecl

from apiclient.discovery import build_from_document
from googlecl.discovery import authentication
from googlecl.discovery import output
from googlecl.discovery import data
from googlecl.discovery import docs
import simplejson as json

LOG = logging.getLogger(googlecl.LOGGER_NAME)
DISCOVERY_URI = '%s/discovery/v1/apis/{api}/{apiVersion}/rest'

class DiscoveryManager():

  def __init__(self, email):
    self.dataManager = data.DefaultManager(email)
    self.docManager = docs.DocManager(self.dataManager.local_apis, self.dataManager.base_url)

  def run(self, argv):
   try:
    """Primary function for the program
    Executes methods, displays help, and organizes formatting for services 
    using Discovery

    Args:
      cache: A cache, which may already contain objects to be used
      argv: The arguments, parsed into a list as from the command line
    """
    # Determines if the help, format, or default is being called
    LOG.debug('Running Discovery...')
    isHelp = argv[0]=='help'
    verbose = False
    if isHelp:
      argv = argv[1:]
      if argv[-1] == '--verbose' or argv[-1] == '-v':
        verbose = True
        argv = argv[:-1]

    http = httplib2.Http()
    
    LOG.debug('Parsing service...')
    # Fetches service, version, docs, etc. 
    try:
      servicename, version, doc, args = self.docManager.run(argv, isHelp,
                                                            verbose)
    except TypeError:
      return

    LOG.debug('Managing auth...')
    # Checks if credentials are needed and, if so, whether they are possessed.
    # If not, gets appropriate credentials.
    if 'auth' in doc:
      if '--force-auth' in args:
        args.remove('--force-auth')
        force_auth = True
      else:
        force_auth = False
      http = authentication.authenticate(self.dataManager.email, servicename, doc, http,
        self.dataManager.client_id, self.dataManager.client_secret, force_auth)

      # Builds the service and finds the method
      service = build_from_document(json.dumps(doc), DISCOVERY_URI % self.dataManager.base_url, http=http)
    else:
      service = build_from_document(json.dumps(doc), DISCOVERY_URI % self.dataManager.base_url,
                      developerKey=self.dataManager.devkey2, http=http)
    LOG.debug('Determining task...')
    try:
      metinfo, method, args = getMethod(service, doc, args)
    except:
      #LOG.error('Did not recognize task.')
      return

    LOG.debug('Parsing parameters...')
    try:
      kwargs = self.dataManager.fill_out_options(metinfo, doc, args)
    except TypeError, err:
      raise
      return

    LOG.debug('Executing method...')
    try:
      resp = method(**kwargs).execute()
    except Exception, err:
      LOG.error(err)
      return

    LOG.debug('Displaying output...')
    # Displays formatted output
    output.output(resp, self.dataManager.formatting)
   except Exception, err:
    print 'Uncaught error'
    raise

  def apis_list(self):
    # Returns a list of the APIs that may be used
    return [str(d['name']) for d in self.docManager.directory['items']]

def getMethod(service, doc, args):
  """ Locates the method to be executed 
  Capable of finding some methods implicitly
  Displays assistance if method isn't identified

  Args:
    service: The service object being used
    doc: Documentation describing the service
    args: List containing the method path to be followed

  Returns:
    A tuple of the meta-info describing the method, 
    the method itself, and the parameters for the method
  """
  obj = doc
  attr = service
  i = 0
  while 'resources' in obj or 'methods' in obj:
    if i < len(args) and 'resources' in obj and args[i] in obj['resources']:
      attr = getattr(attr, args[i])
      obj = obj['resources'][args[i]]
      i=i+1
    elif i < len(args) and 'methods' in obj and args[i] in obj['methods']:
      attr = getattr(attr, args[i])
      obj = obj['methods'][args[i]]
      i=i+1
    elif ('resources' in obj and not 'methods' in obj and
        len(obj['resources'])==1):
      attr = getattr(attr, obj['resources'].keys()[0])
      obj = obj['resources'][obj['resources'].keys()[0]]
    elif 'methods' in obj and not 'resources' in obj and len(obj['methods'])==1:
      attr = getattr(attr, obj['methods'].keys()[0])
      obj = obj['methods'][obj['methods'].keys()[0]]
    else:
      print 'Did not recognize task.'
      if 'methods' in obj:
        LOG.error('Possible methods: ' + ', '.join(obj['methods']))
      if 'resources' in obj:
        LOG.error('Possible resources: ' + ', '.join(obj['resources']))
      return
    if not 'id' in obj:
      attr = attr()
  return obj, attr, args[i:]
