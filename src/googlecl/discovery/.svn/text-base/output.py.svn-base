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


"""Subfunctions for GoogleCL.

Manages the formatting and output of generated responses
"""
import pprint

def output(resp, mode = 'pprint'):
  """Outputs the generated response according to defined formatting

  Args:
    resp: The actual response to be formatted and displayed
    mode: What type of formatting is used
  """
  if mode == 'none':
    print resp
  elif mode == 'pprint':
    pprint.pprint(resp)
  elif mode == 'clean':
    cprint(resp)

def cprint(resp, st=1):
  """ Displays a json object, dict, or list
  More readable that pprint, but interchangeable.
  Recursively calls itself to display nested subfields

  Args:
    resp: The object to be displayed
    st: A counter for the current indentation
  """
  for arg in resp:
    if isinstance(resp, dict):
      if isinstance(resp[arg], dict) or isinstance(resp[arg], list):  
        print (' '*st) + arg + ":"
        cprint(resp[arg], st+2)
      else:
       try:
        print (' '*st) + arg + ": " + str(resp[arg])
       except UnicodeEncodeError:
        print (' '*st) + arg + ": " + resp[arg]
    else:
      if isinstance(arg, dict) or isinstance(arg, list):
        cprint(arg, st)
      else:
        print (' '*st) + arg
