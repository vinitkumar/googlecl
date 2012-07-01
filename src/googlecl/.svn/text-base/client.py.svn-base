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


"""Basic service extensions for the gdata python client library for use on
  the command line."""


import gdata.client
import googlecl
import googlecl.base
import logging

LOG = logging.getLogger(__name__)

# This class CANNOT be used unless an instance also inherits from
# gdata.client.GDClient somehow.
# TODO: pylint bugs out over the missing functions/attributes here,
# but there are no run-time errors. Make pylint happy!
class BaseClientCL(googlecl.base.BaseCL):

  """Extension of gdata.GDataService specific to GoogleCL."""

  def __init__(self, section, config,
               request_error_class=gdata.client.RequestError,
               *args, **kwargs):
    super(BaseClientCL, self).__init__(section, config, request_error_class,
                                       *args, **kwargs)
    # Used for automatic retries of requests that fail due to 302 errors.
    # See BaseCL.retry_operation.
    self.original_request = self.request
    self.request = self.retry_request

    LOG.debug('Initialized googlecl.client.BaseClientCL')

  def is_token_valid(self, test_uri):
    try:
      return super(BaseClientCL, self).is_token_valid(test_uri)
    # If access has been revoked through account settings, get weird
    # Unauthorized error complaining about AuthSub.
    except gdata.client.Unauthorized:
      return False

  IsTokenValid = is_token_valid

  def retry_request(self, *args, **kwargs):
    """Retries a request."""
    self.original_operation = self.original_request
    return self.retry_operation(*args, **kwargs)

  def request_access(self, domain, display_name, scopes=None, browser=None):
    """Do all the steps involved with getting an OAuth access token.

    Keyword arguments:
      domain: Domain to request access for.
              (Sets the hd query parameter for the authorization step).
      display_name: Descriptor for the machine doing the requesting.
      scopes: String or list of strings describing scopes to request
              access to. If None, tries to access self.auth_scopes
      browser: Browser object for opening a URL, or None to just print the url.

    Returns:
      True if access token was succesfully retrieved and set, otherwise False.

    """
    import urllib
    import time
    # XXX: Not sure if get_oauth_token() will accept a list of mixed strings and
    # atom.http_core.Uri objects...
    if not scopes:
      scopes = self.auth_scopes
    if not isinstance(scopes, list):
      scopes = [scopes,]
    # Some scopes are packaged as tuples, which is a no-no for
    # gauth.generate_request_for_request_token() (called by get_oauth_token)
    for i, scope in enumerate(scopes):
      if isinstance(scope, tuple):
        scopes[i:i+1] = list(scope)
    scopes.extend(['https://www.googleapis.com/auth/userinfo#email'])
    LOG.debug('Scopes being requested: ' + str(scopes))

    url = gdata.gauth.REQUEST_TOKEN_URL + '?xoauth_displayname=' +\
          urllib.quote(display_name)
    try:
      # Installed applications do not have a pre-registration and so follow
      # directions for unregistered applications
      request_token = self.get_oauth_token(scopes, next='oob',
                                           consumer_key='anonymous',
                                           consumer_secret='anonymous',
                                           url=url)
    except self.request_error, err:
      LOG.error(err)
      if str(err).find('Timestamp') != -1:
        LOG.info('Is your system clock up to date? See the FAQ on our wiki: '
                 'http://code.google.com/p/googlecl/wiki/FAQ'
                 '#Timestamp_too_far_from_current_time')
      return False
    auth_url = request_token.generate_authorization_url(
                                                      google_apps_domain=domain)
    if browser is not None:
      try:
        browser.open(str(auth_url))
      except Exception, err:
        # Blanket catch of Exception is a bad idea, but don't want to pass in
        # error to look for.
        LOG.error('Failed to launch web browser: ' + unicode(err))
    print 'Please log in and/or grant access at %s' % auth_url
    # Try to keep that damn "Created new window in existing browser session."
    # message away from raw_input call.
    time.sleep(2)
    print ''
    request_token.verifier = raw_input('Please enter the verification code on'
                                       ' the success page: ').strip()
    # This upgrades the token, and if successful, sets the access token
    try:
      access_token = self.get_access_token(request_token)
    except gdata.client.RequestError, err:
      LOG.error(err)
      LOG.error('Token upgrade failed! Could not get OAuth access token.')
      return False
    else:
      self.auth_token = access_token
      return True

  RequestAccess = request_access

  def SetOAuthToken(self, token):
    self.auth_token = token
