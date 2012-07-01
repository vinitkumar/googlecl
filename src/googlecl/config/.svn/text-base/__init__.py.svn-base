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
import ConfigParser
import googlecl
import parser


def _create_basic_options():
  """Set the most basic options in the config file."""
  import googlecl.docs
  import googlecl.contacts
  import googlecl.calendar
  import googlecl.youtube
  import getpass
  import socket
  # These may be useful to define at the module level, but for now,
  # keep them here.
  # REMEMBER: updating these means you need to update the CONFIG readme.
  default_hostid = getpass.getuser() + '@' +  socket.gethostname()
  _youtube = {'max_results': '50'}
  _contacts = {'fields': 'name,email'}
  _calendar = {'fields': 'title,when'}
  _general = {'max_retries': '2',
              'retry_delay': '0.5',
              'regex': 'True',
              'url_field': 'site',
              'fields': 'title,url-site',
              'missing_field_value': 'N/A',
              'date_print_format': '%b %d %H:%M',
              'cap_results': 'False',
              'hostid': default_hostid}
  _docs = {'document_format': 'txt',
           'spreadsheet_format': 'xls',
           'presentation_format': 'ppt',
           'drawing_format': 'png',
           'format': 'txt',
           'spreadsheet_editor': 'openoffice.org',
           'presentation_editor': 'openoffice.org'}
  return {googlecl.docs.SECTION_HEADER: _docs,
          googlecl.contacts.SECTION_HEADER: _contacts,
          googlecl.calendar.SECTION_HEADER: _calendar,
          googlecl.youtube.SECTION_HEADER: _youtube,
          'GENERAL': _general}


def get_config_path(filename='config',
                    default_directories=None,
                    create_missing_dir=False):
  """Get the full path to the configuration file.

  See googlecl.get_xdg_path()
  """
  return googlecl.get_xdg_path(filename, 'CONFIG', default_directories,
                               create_missing_dir)


def load_configuration(path=None):
  """Loads configuration file.

  Args:
    path: Path to the configuration file. Default None for the default location.

  Returns:
    Configuration parser.
  """
  if not path:
    path = get_config_path(create_missing_dir=True)
    if not path:
      LOG.error('Could not create config directory!')
      return False
  config = parser.ConfigParser(ConfigParser.ConfigParser)
  config.associate(path)
  made_changes = config.ensure_basic_options(_create_basic_options())
  if made_changes:
    config.write_out_parser()
  # Set the encoding again, now that the config file is loaded.
  # (the config file may have a default encoding setting)
  googlecl.TERMINAL_ENCODING = googlecl.determine_terminal_encoding(config)
  return config
