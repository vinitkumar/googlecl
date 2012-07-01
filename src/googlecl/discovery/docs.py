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

""" Subclass for the Discovery portion of GoogleCL which
    manages the documentation

In charge of saving/loading the API directory, 
and retrieves and stores the Discovery documents.
"""

import httplib2
import logging

import simplejson as json
import googlecl

LOG = logging.getLogger(googlecl.LOGGER_NAME)
apis_path = googlecl.get_data_path('apis.dat', create_missing_dir=True)
SERVICE_BLACKLIST = ['latitude']
LIST_URL = '%s/discovery/v1/apis?preferred=true&pp=0'
SERVICE_URL = '%s/discovery/v1/apis/%s/%s/rest'

class DocManager():
  def __init__(self, local, base_url):
    self.base_url = base_url
    self.load()
    self.apis = {}
    self.local = local
    if self.local:
      if isinstance(self.local, list): # local comes from the config file
        for filename in self.local:    # Be sure to give the correct path.
          self.loadDoc(filename)
      else:
        self.loadDoc(self.local)

  def load(self, force=False):
    """ Loads the currently saved list of preferred APIs, 
        or downloads the latest version.
        Can be forced with the command 'refresh apis'

    Args:
      force: If true, the will always download a new document
    """
    try:
      if force:
        raise
      f = open(apis_path, 'r')
      self.directory = json.load(f)
    except:
      http = httplib2.Http()
      resp, content = http.request(LIST_URL % self.base_url)
      self.directory = json.loads(content)
      # Removes blacklisted APIs (currently just latitude)
      self.directory['items'] = [a for a in self.directory['items'] 
                                 if a['name'] not in SERVICE_BLACKLIST]
      f = open(apis_path, 'w')
      json.dump(self.directory, f, indent=2)
    if hasattr(self, 'local') and self.local:
      if isinstance(self.local, list): # local comes from the config file
        for filename in self.local:    # Be sure to give the correct path.
          self.loadDoc(filename)
      else:
        self.loadDoc(self.local)

  def loadDoc(self, filename):
    """ Loads a discovery document stored locally

    Args:
      filename: The file being loaded
    """
    try:
      doc = json.loads(file(filename).read())
    except:
      LOG.info('Failed to load ' + filename)
      return
    self.apis[doc['name']+'.'+doc['version']] = doc
    info = {'name': doc['name'], 'version': doc['version']}
    self.directory['items'].append(info)

  def run(self, argv, isHelp, verbose):
    """ Parses through arguments to determine service, version, and gets docs
    Also prints help, if applicable

    Args:
      argv: The arguments which are passed in
      isHelp: If help should be displayed
      verbose: If isHelp, then whether it should be verbose
    Returns:
      If it doesn't display help, then a tuple of the service name,
      version, documentation, and remaining args
    """
    http = httplib2.Http()

    # Parses the service name and version
    # If no version is defined, finds the currently preferred one
    servicename = argv[0]
    if len(argv) > 1:
      version = argv[1]
    else:
      version = None
    args = argv[2:]
    if not version or not version[0] == 'v' or not version[1].isdigit():
      version = None
      for api in self.directory['items']:
        if api['name'] == servicename:
          version = api['version']
          args = argv[1:]
          break
      if not version:
        LOG.error('Did not recognize service.')
        return

    # Fetches documentation for service
    if servicename + '.' + version in self.apis:
      doc = self.apis[servicename + '.' + version]
    else:
      resp, content = http.request(SERVICE_URL % (self.base_url, servicename, version))
      doc = json.loads(content)
      self.apis[servicename + '.' + version] = doc

    if 'error' in doc:
      LOG.error('Did not recognize version.')
      return

    # Displays help, if requested
    if isHelp:
      help(doc, verbose, *args)
      return

    return servicename, version, doc, args

def help(doc, verbose, *path):
  """ Prints the help for an arbitrary service

  Args:
    doc: Discovery document for the service
    verbose: Whether or not all information should be displayed
    path: The path to the desired method, parameter, or other attribute
  """

  # Locates the desired object
  # Will try to follow path implicitly (for resources, methods, parameters)
  # otherwise the path must be fully defined (most likely useful for schemas)
  base = doc
  for p in path:
    if p[:2] == '--':
      p = p[2:]
    if p in base:
      base = base[p]
    elif 'resources' in base and p in base['resources']:
      base = base['resources'][p]
    elif 'methods' in base and p in base['methods']:
      base = base['methods'][p]
    elif 'parameters' in base and p in base['parameters']:
      base = base['parameters'][p]
    else:
      n = ('resources' in base) + ('methods' in base) + ('parameters' in base 
                                                         and not base == doc)
      while (n == 1 or len(base) == 1) and not p in base:
        i = 0
        if 'resources' in base: i = base.keys().index('resources')
        elif 'methods' in base: i = base.keys().index('methods')
        elif 'parameters' in base: i = base.keys().index('parameters')
        base = base[base.keys()[i]]
        n = ('resources' in base) + ('methods' in base) + ('parameters' in base)
      if p in base:
        base = base[p]
      else:
        LOG.error('Error in path: "' + p + '" not found')
        return

  # Displays the attributes of the requested object
  # Formatted if object is base API, method, or resource and not verbose.
  if not verbose:
    if isinstance(base, dict):
      if 'version' in base: #Base API
        print ' ' + base['description']
        print '  Resources: ' + ', '.join(base['resources'])
      elif 'httpMethod' in base: #Method
        print ' ' + base['description']
        if 'parameterOrder' in base:
          print '  Requires: ' + ' AND '.join(base['parameterOrder']) \
          + ' Optional: ' + ', '.join([i for i in base['parameters'] if \
          i not in base['parameterOrder']])
        elif 'parameters' in base:
          print '  Optional: ' + ', '.join(base['parameters'])
        if 'request' in base:
          print '  Request schema: ' + base['request']['$ref']
      elif 'methods' in base or 'resources' in base: #Resource
        if 'methods' in base:
          print '  Methods: ' + ', '.join(base['methods'])
        if 'resources' in base:
          print '  Resources: ' + ', '.join(base['resources'])
      else: #Everything else
        for obj in base:
          if isinstance(base[obj], dict) or isinstance(base[obj], list):
            print '  ' + obj + ": " + ', '.join(base[obj])
          else:
            print '  ' + obj + ": " + str(base[obj])
    else:
      print base
  else:
    if isinstance(base, dict):
      for obj in base:
        if isinstance(base[obj], dict) or isinstance(base[obj], list):
          print '  ' + obj + ": " + ', '.join(base[obj])
        else:
          print '  ' + obj + ": " + str(base[obj])
    else:
      print base
