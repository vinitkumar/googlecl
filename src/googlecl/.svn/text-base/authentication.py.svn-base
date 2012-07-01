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

TOKENS_FILENAME_FORMAT = 'access_tok_%s'
LOGGER_NAME = __name__
LOG = logging.getLogger(LOGGER_NAME)

#XXX: Public-facing functions are confusing, clean up.
class AuthenticationManager(object):
  """Handles OAuth token for a given service."""

  def __init__(self, service_name, client, tokens_path=None):
    """Initializes instance.

    Args:
      service_name: Name of the service.
      client: Client accessing the service that requires authentication.
      tokens_path: Path to tokens file. Default None to use result from
          get_data_path()
    """
    self.service = service_name
    self.client = client
    if tokens_path:
      self.tokens_path = tokens_path
    else:
      self.tokens_path = googlecl.get_data_path(TOKENS_FILENAME_FORMAT %
                                                client.email,
                                                create_missing_dir=True)

  def check_access_token(self):
    """Checks that the client's access token is valid, remove it if not.

    Returns:
      True if the token is valid, False otherwise. False will be returned
      whether or not the token was successfully removed.
    """
    try:
      token_valid = self.client.IsTokenValid()
    except AttributeError, err:
      # Attribute errors crop up when using different gdata libraries
      # but the same token.
      token_valid = False
      LOG.debug('Caught AttributeError: ' + str(err))
    if token_valid:
      LOG.debug('Token valid!')
      return True
    else:
      removed = self.remove_access_token()
      if removed:
        LOG.debug('Removed invalid token')
      else:
        LOG.debug('Failed to remove invalid token')
      return False

  def get_display_name(self, hostid):
    """Gets standard display name for access request.

    Args:
      hostid: Working machine's host id, e.g. "username@hostname"

    Returns:
      Value to use for xoauth display name parameter to avoid worrying users
      with vague requests for access.
    """
    return 'GoogleCL %s' % hostid

  def _move_failed_token_file(self):
    """Backs up failed tokens file."""
    new_path = self.tokens_path + '.failed'
    LOG.debug('Moving ' + self.tokens_path + ' to ' + new_path)
    if os.path.isfile(new_path):
      LOG.debug(new_path + ' already exists. Deleting it.')
      try:
        os.remove(new_path)
      except EnvironmentError, err:
        LOG.debug('Cannot remove old failed token file: ' + str(err))
    try:
      os.rename(self.tokens_path, new_path)
    except EnvironmentError, err:
      LOG.debug('Cannot rename token file to ' + new_path + ': ' + str(err))

  def read_access_token(self):
    """Tries to read an authorization token from a file.

    Returns:
      The access token, if it exists. If the access token cannot be read,
      returns None.
    """
    if os.path.exists(self.tokens_path):
      with open(self.tokens_path, 'rb') as tokens_file:
        try:
          tokens_dict = pickle.load(tokens_file)
        except ImportError:
          return None
      try:
        token = tokens_dict[self.service]
      except KeyError:
        return None
      else:
        return token
    else:
      return None

  def remove_access_token(self):
    """Removes an auth token.

    Returns:
      True if the token was removed from the tokens file, False otherwise.
    """
    success = False
    file_invalid = False
    if os.path.exists(self.tokens_path):
      with open(self.tokens_path, 'r+') as tokens_file:
        try:
          tokens_dict = pickle.load(tokens_file)
        except ImportError, err:
          LOG.error(err)
          LOG.info('You probably have been using different versions of gdata.')
          self._move_failed_token_file()
          return False
        except IndexError, err:
          LOG.error(err)
          self._move_failed_token_file()
          return False

        try:
          del tokens_dict[self.service]
        except KeyError:
          LOG.debug('No token for ' + self.service)
        else:
          try:
            pickle.dump(tokens_dict, tokens_file)
          except EnvironmentError, err:
            # IOError (extends enverror) shouldn't happen, but I've seen
            # IOError Errno 0 pop up on Windows XP with Python 2.5.
            LOG.error(err)
            if err.errno == 0:
              _move_failed_token_file()
          else:
            success = True
    return success

  def retrieve_access_token(self, display_name, browser_object):
    """Requests a new access token from Google, writes it upon retrieval.

    The token will not be written to file if it was granted for an account
    other than the one specified by client.email. Instead, a False value will
    be returned.

    Returns:
      True if the token was retrieved and written to file. False otherwise.
    """
    domain = get_hd_domain(self.client.email)
    if self.client.RequestAccess(domain, display_name, None, browser_object):
      authorized_account = self.client.get_email()
      # Only write the token if it's for the right user.
      if self.verify_email(self.client.email, authorized_account):
        # token is saved in client.auth_token for GDClient,
        # client.current_token for GDataService.
        self.write_access_token(self.client.auth_token or
                                self.client.current_token)
        return True
      else:
        LOG.error('You specified account ' + self.client.email +
                  ' but granted access for ' + authorized_account + '.' +
                  ' Please log out of ' + authorized_account +
                  ' and grant access with ' + self.client.email + '.')
    else:
      LOG.error('Failed to get valid access token!')
    return False

  def set_access_token(self):
    """Reads an access token from file and set it to be used by the client.

    Returns:
      True if the token was read and set, False otherwise.
    """
    try:
      token = self.read_access_token()
    except (KeyError, IndexError):
      LOG.warning('Token file appears to be corrupted. Not using.')
    else:
      if token:
        LOG.debug('Loaded token from file')
        self.client.SetOAuthToken(token)
        return True
      else:
        LOG.debug('read_access_token evaluated to False')
    return False

  def verify_email(self, given_account, authorized_account):
    """Makes sure user didn't clickfest his/her way into a mistake.

    Args:
      given_account: String of account specified by the user to GoogleCL,
          probably by options.user. If domain is not included,
          assumed to be 'gmail.com'
      authorized_account: Account returned by client.get_email(). Must
          include domain!

    Returns:
      True if given_account and authorized_account match, False otherwise.
    """
    if authorized_account.find('@') == -1:
      raise Exception('authorized_account must include domain!')
    if given_account.find('@') == -1:
      given_account += '@gmail.com'
    return given_account == authorized_account

  def write_access_token(self, token):
    """Writes an authorization token to a file.

    Args:
      token: Token object to store.
    """
    if os.path.exists(self.tokens_path):
      with open(self.tokens_path, 'rb') as tokens_file:
        try:
          tokens_dict = pickle.load(tokens_file)
        except (KeyError, IndexError), err:
          LOG.error(err)
          LOG.error('Failed to load token file (may be corrupted?)')
          file_invalid = True
        except ImportError, err:
          LOG.error(err)
          LOG.info('You probably have been using different versions of gdata.')
          file_invalid = True
        else:
          file_invalid = False
      if file_invalid:
        self._move_failed_token_file()
        tokens_dict = {}
    else:
      tokens_dict = {}
    tokens_dict[self.service] = token
    with open(self.tokens_path, 'wb') as tokens_file:
      # Ensure only the owner of the file has read/write permission
      os.chmod(self.tokens_path, stat.S_IRUSR | stat.S_IWUSR)
      pickle.dump(tokens_dict, tokens_file)


def get_hd_domain(username, default_domain='default'):
  """Returns the domain associated with an email address.

  Intended for use with the OAuth hd parameter for Google.

  Args:
    username: Username to parse.
    default_domain: Domain to set if '@suchandsuch.huh' is not part of the
        username. Defaults to 'default' to specify a regular Google account.

  Returns:
    String of the domain associated with username.
  """
  name, at_sign, domain = username.partition('@')
  # If user specifies gmail.com, it confuses the hd parameter
  # (thanks, bartosh!)
  if domain == 'gmail.com' or domain == 'googlemail.com':
    return 'default'
  return domain or default_domain
