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
"""Enhanced configuration file parser."""

from __future__ import with_statement

import logging
import os.path

LOGGER_NAME = __name__
LOG = logging.getLogger(LOGGER_NAME)


class ConfigParser(object):
  def __init__(self, config_parser_class):
    """Initializes the object.

    Args:
      config_parser: Class that acts as a configuration file parser.
    """
    self.parser = config_parser_class()
    try: # Because default ConfigParser converts to lower case
      self.parser.optionxform = str
    except:
      pass
    self.path = None

  def associate(self, config_file_path):
    """Associates parser with a config file.

    Config file is read from config_file_path as well.
    """
    if os.path.exists(config_file_path):
      LOG.debug('Reading configuration from %s', config_file_path)
      self.parser.read(config_file_path)
    else:
      LOG.debug('Config file does not exist, starting with empty parser')
    self.path = config_file_path

  def ensure_basic_options(self, basic_options):
    """Sets options if they are missing.

    Args:
      basic_options: Nested dictionary in the form of
          {section header: {option: value, option: value},
           section_header: {option: value, option: value}
           ...}
    Returns:
      True if some of the options in basic_options were not set already, False
      otherwise.
    """
    made_changes = False
    for section_name, section_options in basic_options.iteritems():
      if not self.parser.has_section(section_name):
        self.parser.add_section(section_name)
      missing_options = (set(section_options.keys()) -
                         set(self.parser.options(section_name)))
      for option in missing_options:
        self.set(section_name, option, section_options[option])
      if missing_options and not made_changes:
        made_changes = True
    return made_changes

  def get(self, section, option):
    """Returns option in section.

    No backup sections or defaults are returned by this function. If the section
    or option does not exist, the config parser will raise an error.

    Returns:
      String from config file.
    """
    return self.parser.get(section, option)

  def lazy_get(self, section, option, default=None, option_type=None,
               backup_section='GENERAL'):
    """Returns option from config file.

    Tries to retrieve <option> from the given section. If that fails, tries to
    retrieve the same option from the backup section. If that fails,
    returns value of <default> parameter.

    Args:
      section: Name of the section to initially try to retrieve the option from.
      option: Name of the option to retrieve.
      default: Value to return if the option does not exist in a searched
          section.
      option_type: Conversion function to use on the string, or None to leave as
          string. For example, if you want an integer value returned, this
          should be set to int. Not applied to the <default> parameter.
      backup_section: Section to check if option does not exist in given
          section. Default 'GENERAL'.

    Returns:
      Value of the option if it exists in the config file, or value of "default"
      if option does not exist.
    """
    value = self.safe_get(section, option)
    if value is None:
      value = self.safe_get(backup_section, option)
    if value is None:
      return default

    if option_type:
      # bool() function doesn't actually do what we wanted, so intercept it
      # and replace with comparison
      if option_type == bool:
        return value.lower() == 'true'
      else:
        return option_type(value)
    else:
      return value

  def safe_get(self, section, option):
    """Returns option if section and option exist, None if they do not."""
    if (self.parser.has_section(section) and
        self.parser.has_option(section, option)):
      return self.parser.get(section, option)
    else:
      return None

  def set(self, section, option, value):
    """Sets option in a section."""
    return self.parser.set(section, option, value)

  def set_missing_default(self, section, option, value):
    """Sets the option for a section if not defined already.

    If the section does not exist, it is created.

    Args:
      section: Title of the section to set the option in.
      option: Option to set.
      value: Value to give the option.
      config_path: Path to the configuration file.
          Default None to use the default path defined in this module.
    """
    if type(value) not in [unicode, str]:
      value = unicode(value)
    existing_value = self.safe_get(section, option)

    if existing_value is None:
      if not self.parser.has_section(section):
        self.parser.add_section(section)
      self.set(section, option, value)

  def write_out_parser(self, path=None):
    """Writes options in config parser to file.

    Args:
      path: Path to write to. Default None for path associated with instance.

    Raises:
      IOError: No path given and instance is not associated with a path.
    """
    if not path:
      if self.path:
        path = self.path
      else:
        raise IOError('No path given or associated')
    with open(path, 'w') as config_file:
      self.parser.write(config_file)
