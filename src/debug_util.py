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

"""Utilities that should not be distributed with source."""

__author__ = 'thmiller@google.com (Tom Miller)'


import atom
import inspect


dull_types = [str, unicode, dict, list, type(None)]
def walk_attributes(myobject, object_name, tabitem='=', step=True, tablevel=0):
  """Walk through attributes of an instance.

  Just flat out prints varying values of dir() for instances and their
  attributes.

  Args:
    myobject: instance to walk through
    object_name: Name of the instance being walked through
    tabitem: String to show depth into myobject. Set to '' to disable.
    step: bool Use raw_input('') after printing each attribute
    tablevel: Depth into myobject (starts at 0)

  Returns:
    NATHING!

  """
  print tabitem*tablevel + 'Object: ' + object_name
  print tabitem*tablevel + 'Type: ' + str(type(myobject))
  attr_list = [attr for attr in dir(myobject)
               if not attr.startswith('_') and
               not inspect.ismethod(getattr(myobject, attr))]
  print tabitem*tablevel + 'Attributes: '
  print tabitem*tablevel + str(attr_list)
  dull_attr = [attr for attr in attr_list
               if type(getattr(myobject, attr)) in dull_types]
  if dull_attr:
    print tabitem*tablevel + '(basic attributes: ' + str(dull_attr) + ')'

  loopable_attr = [attr for attr in attr_list
                   if not type(getattr(myobject, attr)) in dull_types]
  for attr_name in loopable_attr:
    new_object = getattr(myobject, attr_name)
    if step:
      raw_input('')
    walk_attributes(new_object, attr_name, tablevel=tablevel+1)
