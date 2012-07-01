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

""" Subclass which manages data for Discovery

Manages defaults, config values, parsing the arguments,
and prompting for missing parameters
Defaults may be viewed/edited by calling 'edit defaults'
TODO: Integrate ConfigParser
"""

import logging

import simplejson as json
import googlecl
import googlecl.config
import optparse

LOG = logging.getLogger(googlecl.LOGGER_NAME)
DEFAULT_FILENAME_FORMAT = 'dcd_%s'
# Args governing prompting
META_ARGS = ['prompt', 'editor', 'editmode']
# Args that aren't in method parameters
EXTRA_ARGS = ['fields']

class DefaultManager:

  def __init__(self, email):
    self.email = email
    # Loads config options
    config = googlecl.config.load_configuration(None)
    self.client_id = config.lazy_get(None, 'client_id',
         default='20958643459.apps.googleusercontent.com', option_type=str)
    self.client_secret = config.lazy_get(None, 'client_secret',
         default='3D1TrF0sgq52J7zH80jdfbit', option_type=str)
    self.devkey2 = config.lazy_get(None, 'devkey2',
         default='AIzaSyAmK-fJLcJ0jS2mMIX5EXgU6M6UPT39e50', option_type=str)
    # Should make ^ required
    self.prompt = config.lazy_get(None, 'prompt', 
         default='required', option_type=str)
    self.editmode = config.lazy_get(None, 'editmode',
         default='cl', option_type=str)
    self.formatting = config.lazy_get(None, 'formatting',
         default='pprint', option_type=str)
    self.local_apis = config.lazy_get(None, 'local_apis', default='', option_type=str)
    if '[' in self.local_apis or '(' in self.local_apis:
      self.local_apis = json.loads(self.local_apis)
    self.base_url = config.lazy_get(None, 'base_url', default='https://www.googleapis.com', option_type=str)
    editor = config.safe_get('DOCS', 'document_editor')
    if not editor:
      editor = config.safe_get(None, 'editor')
    if not editor:
      import os
      editor = os.getenv('EDITOR')
    if not editor:
      editor = 'vim'
    self.editor = editor

  def fill_out_options(self, metinfo, doc, args):
    """ Turns a list of arguments into a map of keys/values
    Starts by doing basic parse, then loads defaults, 
    and finally prompts for missing values

    Args:
      metinfo: The meta-info for the method, 
        such as the required/optional parameters
      args: The arguments which are passed in
    """
    parser = optparse.OptionParser()
    # Set up options
    for arg in META_ARGS:
      parser.add_option('--'+arg, default=getattr(self, arg))
    for arg in EXTRA_ARGS:
      parser.add_option('--'+arg)
    if 'parameters' in metinfo:
      for arg in metinfo['parameters']:
        parser.add_option("--"+arg)
    if 'request' in metinfo:
      parser.add_option("--body")
      for arg in doc['schemas'][metinfo['request']['$ref']]['properties']:
        try:
          parser.add_option('--'+arg)
        except optparse.OptionConflictError:
          pass

    # Parse args
    (options, args) = parser.parse_args(args)
    kwargs = vars(options)
    for arg in kwargs.keys():
      if kwargs[arg] == None or kwargs[arg] == '':
        del kwargs[arg]

    # Loads defaults
    config = googlecl.config.load_configuration()
    if config.parser.has_section(metinfo['id']):
      for arg in config.parser.options(metinfo['id']):
        if arg not in kwargs:
          kwargs[arg] = config.get(metinfo['id'], arg)

    # Attaches unmatched values to appropriate keys
    if args:
      if not 'parameterOrder' in metinfo:
        LOG.error('Received unexpected parameter.')
        return
      args = dict(zip([i for i in metinfo['parameterOrder']
               if i not in kwargs.keys() or kwargs[i] == None],args))
      kwargs = dict(kwargs.items() + args.items())

    # Prompts for missing values
    if not kwargs['prompt'] == 'none' and 'parameterOrder' in metinfo:
      for a in metinfo['parameterOrder']: # Required parameters
        if a not in kwargs:
          value = raw_input('Please specify ' + a + ': ')
          if not value:
            return
          kwargs[a] = value
    if kwargs['prompt'] == 'all' and 'parameters' in metinfo:
      for a in metinfo['parameters']: # Optional parameters
        if a not in kwargs:
          value = raw_input('Please specify ' + a + ': ')
          if value:
            kwargs[a] = value
    if kwargs:
      for arg in kwargs.keys():
        if '{' == kwargs[arg][0] or '[' == kwargs[arg][0] or '(' == kwargs[arg][0]:
          kwargs[arg] = json.loads(kwargs[arg])

    if 'parameters' in metinfo:
      pars = set(metinfo['parameters'])
    else:
      pars = {}
    # Assumes that unknown keys are part of body
    if 'body' not in kwargs and 'request' in metinfo and not set(kwargs.keys()) - set(META_ARGS) - set(EXTRA_ARGS) <= set(pars):
      body = {}
      for a in set(kwargs.keys()) - set(pars) - set(META_ARGS) - set(EXTRA_ARGS):
        body[a] = kwargs[a]
        del kwargs[a]
      kwargs['body'] = body
      
    # Prompts for missing body
    if not kwargs['prompt'] == 'none' and 'body' not in kwargs and 'request' in metinfo:
      schemaname = metinfo['request']['$ref']
      schema = doc['schemas'][schemaname]
      if kwargs['editmode'] == 'editor':
        import subprocess
        import tempfile
        import os

        fd, filename = tempfile.mkstemp(text=True)
        f = open(filename, 'w')
        body = {}
        # Assembles the outline of the body
        # Will modify to use required/mutable args if/when it is available
        for p in schema['properties']:
          if 'default' in schema['properties'][p]:
            body[p] = schema['properties'][p]['default']
          elif 'type' in schema['properties'][p]:
            body[p] = "<"+schema['properties'][p]['type']+">"
        json.dump(body, f, indent=2)
        f.close()
        cmd = '%s %s' % (kwargs['editor'], filename)
        raw_input('Missing body...')
        subprocess.call(cmd, shell=True)
        f = open(filename)
        value = json.load(f)
        f.close()
        os.remove(filename)
      else:
        print 'Missing body - Schema: ' + schemaname
        sargs = ', '.join(schema['properties'])
        print '  Args: ' + sargs
        bodyparser = optparse.OptionParser() 
        for arg in doc['schemas'][metinfo['request']['$ref']]['properties']:
          bodyparser.add_option('--'+arg)
        (options, args) = bodyparser.parse_args(raw_input('Please specify body: ').split())
        value = vars(options)
        for arg in value.keys():
          if value[arg] == None or value[arg] == '':
            del value[arg]
        if not value:
          return
      kwargs['body'] = value
    # Get rid of meta-args
    for arg in META_ARGS:
      del kwargs[arg]
    # Can't have '-'s in keys
    for k in kwargs:
      if '-' in k:
        kwargs[k.replace('-','_')] = kwargs[k]
        del kwargs[k]

    return kwargs
