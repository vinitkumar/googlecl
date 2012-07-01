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


import gdata.service
import googlecl
import googlecl.base
import logging

LOG = logging.getLogger(__name__)


class BaseServiceCL(googlecl.base.BaseCL):

  """Extension of gdata.GDataService specific to GoogleCL."""

  def __init__(self, section, config,
               request_error_class=gdata.service.RequestError,
               *args, **kwargs):
    super(BaseServiceCL, self).__init__(section,
                                        config,
                                        request_error_class,
                                        *args,
                                        **kwargs)
    # Most services using old gdata API have to disable ssl.
    self.ssl = False

    # Used for automatic retries of Get/Delete requests that fail due to 302
    # errors. See BaseCL.retry_operation.
    self.original_get = self.Get
    self.original_delete = self.Delete
    self.original_post = self.Post
    self.original_put = self.Put
    self.Get = self.retry_get
    self.Delete = self.retry_delete
    self.Post = self.retry_post
    self.Put = self.retry_put

    LOG.debug('Initialized googlecl.service.BaseServiceCL')

  def retry_get(self, *args, **kwargs):
    """Retries the Get method."""
    self.original_operation = self.original_get
    return self.retry_operation(*args, **kwargs)

  def retry_delete(self, *args, **kwargs):
    """Retries the Delete method."""
    self.original_operation = self.original_delete
    return self.retry_operation(*args, **kwargs)

  def retry_post(self, *args, **kwargs):
    """Retries the Post method."""
    self.original_operation = self.original_post
    return self.retry_operation(*args, **kwargs)

  def retry_put(self, *args, **kwargs):
    """Retries the Put method."""
    self.original_operation = self.original_put
    return self.retry_operation(*args, **kwargs)

  def request_access(self, domain, display_name, scopes=None, browser=None):
    """Do all the steps involved with getting an OAuth access token.

    Keyword arguments:
      domain: Domain to request access for.
          (Sets the hd query parameter for the authorization step).
      display_name: Descriptor for the machine doing the requesting.
      scopes: String or list/tuple of strings describing scopes to request
          access to. Default None for default scope of service.
      browser: Browser to use to open authentication request url. Default None
          for no browser launch, and just displaying the url.

    Returns:
      True if access token was succesfully retrieved and set, otherwise False.

    """
    # Installed applications do not have a pre-registration and so follow
    # directions for unregistered applications
    self.SetOAuthInputParameters(gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                 consumer_key='anonymous',
                                 consumer_secret='anonymous')
    fetch_params = {'xoauth_displayname':display_name}
    # First and third if statements taken from
    # gdata.service.GDataService.FetchOAuthRequestToken.
    # Need to do this detection/conversion here so we can add the 'email' API
    if not scopes:
      scopes = gdata.service.lookup_scopes(self.service)
    if isinstance(scopes, tuple):
      scopes = list(scopes)
    if not isinstance(scopes, list):
      scopes = [scopes,]
    scopes.extend(['https://www.googleapis.com/auth/userinfo#email'])
    LOG.debug('Scopes being requested: ' + str(scopes))

    try:
      request_token = self.FetchOAuthRequestToken(scopes=scopes,
                                                  extra_parameters=fetch_params)
    except gdata.service.FetchingOAuthRequestTokenFailed, err:
      LOG.error(err[0]['body'].strip() + '; Request token retrieval failed!')
      if str(err).find('Timestamp') != -1:
        LOG.info('Is your system clock up to date? See the FAQ on our wiki: '
                 'http://code.google.com/p/googlecl/wiki/FAQ'
                 '#Timestamp_too_far_from_current_time')
      return False
    auth_params = {'hd': domain}
    auth_url = self.GenerateOAuthAuthorizationURL(request_token=request_token,
                                                  extra_params=auth_params)
    if browser is not None:
      try:
        browser.open(str(auth_url))
      except Exception, err:
        # Blanket catch of Exception is a bad idea, but don't want to pass in
        # error to look for.
        LOG.error('Failed to launch web browser: ' + unicode(err))
    message = ('Please log in and/or grant access via your browser at: \n%s\n\n'
               'Then, in this terminal, hit enter. ' % auth_url)
    raw_input(message)
    # This upgrades the token, and if successful, sets the access token
    try:
      self.UpgradeToOAuthAccessToken(request_token)
    except gdata.service.TokenUpgradeFailed:
      LOG.error('Token upgrade failed! Could not get OAuth access token.')
      return False
    else:
      return True

  RequestAccess = request_access
