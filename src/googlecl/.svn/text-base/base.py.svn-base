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


"""Basic abilities that all GoogleCL clients have."""
import googlecl
import logging
import re
import urllib
import time

# Renamed here to reduce verbosity in other sections
safe_encode = googlecl.safe_encode
safe_decode = googlecl.safe_decode

LOG = logging.getLogger(__name__)
HTTP_ERROR_CODES_TO_RETRY_ON = [302, 500, 503]


class Error(Exception):
  """Base error for GoogleCL exceptions."""
  pass


# This class CANNOT be used unless an instance also inherits from
# either gdata.client.GDClient or gdata.service.GDataService somehow.
# TODO: pylint bugs out over the missing functions/attributes here,
# but there are no run-time errors. Make pylint happy!
class BaseCL(object):

  """Extension of gdata.GDataService specific to GoogleCL."""
  # Subclass of Exception to catch when there is a request error.
  # Should be one of gdata.service.RequestError or gdata.client.RequestError
  request_error = None

  def __init__(self, section, config, request_error_class):
    """Set some basic attributes common to all instances.

    Args:
      section: Section of the config file that options will be found under.
      config: Configuration parser.
      request_error_class: Exception class raised when a request fails.
    """
    self.request_error = request_error_class
    large_max_results = 10000
    # Because each new xxxServiceCL class should use the more specific
    # superclass's __init__ function, don't define one here.
    self.source = 'GoogleCL'
    self.client_id = 'GoogleCL'
    self.config = config

    # Some new attributes, not inherited.
    self.use_regex = self.config.lazy_get(section,
                                          'regex',
                                          default=True,
                                          option_type=bool)
    self.cap_results = self.config.lazy_get(section,
                                            'cap_results',
                                            default=False,
                                            option_type=bool)
    self.max_results = self.config.lazy_get(section,
                                            'max_results',
                                            default=large_max_results,
                                            option_type=int)
    self.max_retries = self.config.lazy_get(section,
                                            'max_retries',
                                            default=1,
                                            option_type=int)
    self.retry_delay = self.config.lazy_get(section,
                                            'retry_delay',
                                            default=0,
                                            option_type=float)

    try:
      service_name = self.auth_service
    except AttributeError:
      service_name = self.service
    if (service_name != 'youtube' and
        (not self.cap_results and self.max_results < large_max_results)):
      LOG.warning('You are requesting only ' + str(self.max_results) +
                  ' results per query -- this may be slow')

  def delete_entry_list(self, entries, entry_type, prompt,
                        callback=None):
    """Extends Delete to handle a list of entries.

    Keyword arguments:
      entries: List of entries to delete.
      entry_type: String describing the thing being deleted (e.g. album, post).
      prompt: Whether or not the user should be prompted to confirm deletion.
      callback: function which takes entry as an argument and deletes it
    """
    if prompt:
      prompt_message = ('Are you SURE you want to delete %s "%s"? (y/N): ' %
                        (entry_type, '%s'))
    for item in entries:
      if prompt:
        delete_str = raw_input(prompt_message % safe_encode(item.title.text))
        if not delete_str:
          delete = False
        else:
          delete = delete_str.lower() == 'y'
      else:
        delete = True
      if delete:
        try:
          if callback:
            # if callback is provided then deletion is done by calling it
            callback(item)
          else:
            # Later versions are defined with lowercase function names.
            # These versions take GDataEntry objects, older takes the edit link.
            if hasattr(self, 'delete'):
              self.delete(item)
            else:
              self.Delete(item.GetEditLink().href)
        except self.request_error, err:
          LOG.warning('Could not delete ' + entry_type + ': ' + str(err))

  DeleteEntryList = delete_entry_list

# XXX: This should be shortened. test simpler version with client and service.
  def get_email(self, _uri=None, redirects_remaining=4):
    """Get the email address that has the OAuth access token.

    Uses the "Email address" scope to return the email address the user
    was logged in as when he/she authorized the OAuth request token.

    Keyword arguments:
      uri: Uri to get data from. Should only be used for redirects.

    Returns:
      Full email address ('schmoe@domain.wtf') of the account with access.
    """
    # Use request instead of Get to avoid the attempts to parse from xml.
    server_response = self.request('GET',
                           _uri or 'https://www.googleapis.com/userinfo/email')
    result_body = server_response.read()

    if server_response.status == 200:
      try:
        from urlparse import parse_qs
        parse_func = parse_qs
      except ImportError:
        # parse_qs was moved to urlparse from cgi in python2.6
        import cgi
        parse_func = cgi.parse_qs
      param_dict = parse_func(result_body)
      email = param_dict['email'][0]
    # This block copied (with some modification) from GDataService (2.0.10)
    elif server_response.status == 302:
      if redirects_remaining > 0:
        location = (server_response.getheader('Location') or
                    server_response.getheader('location'))
        if location is not None:
          return BaseServiceCL.get_email(location,
                                      redirects_remaining=redirects_remaining-1)
        else:
          raise self.request_error, {'status': server_response.status,
                'reason': '302 received without Location header',
                'body': result_body}
      else:
        raise self.request_error, {'status': server_response.status,
              'reason': 'Redirect received, but redirects_remaining <= 0',
              'body': result_body}
    else:
      raise self.request_error, {'status': server_response.status,
            'reason': server_response.reason, 'body': result_body}
    return email

  def get_entries(self, uri, titles=None, converter=None, desired_class=None):
    """Get a list of entries from a feed uri.

    Keyword arguments:
      uri: URI to get the feed from.
      titles: string or list What to look for in entry.title.text.
              Default None for all entries from feed.
      converter: Converter to use on the feed. If specified, will be passed
                 into the GetFeed method. If both converter and
                 desired_class are None, GetFeed is called without those
                 arguments.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If converter=None,
                     then the desired_class will be used in calling the
                     atom.core.parse function. If both converter and
                     desired_class are None, GetFeed is called without those
                     arguments.
    Returns:
      List of entries.
    """
    # XXX: Should probably go through all code and make sure title can only be
    # NoneType or list, not also maybe a string.
    if self.max_results is not None:
      uri = set_max_results(uri, self.max_results)
    if isinstance(uri, unicode):
      uri = uri.encode('utf-8')
    feed = None
    try:
      if converter or desired_class:
        # desired_class param not available for GDataService,
        # only GDClient.
        try:
          feed = self.GetFeed(uri, converter=converter,
                              desired_class=desired_class)
        except TypeError:
          if converter:
            feed = self.GetFeed(uri, converter=converter)
      if not feed:
        feed = self.GetFeed(uri)
    except self.request_error, err:
      error_string = str(err)
      LOG.error('Failed to get entries: ' + error_string)

      # Attempt to catch older gdata users and warn them when they try to upload
      # unsupported file types
      if "403.4 SSL required" in error_string:
        print "\n\nIf you are trying upload to Google Docs, your version of "
        print "python-gdata may not support this action. Please see this wiki page "
        print "for more details:" 
        print "http://code.google.com/p/googlecl/wiki/UploadingGoogleDocs\n\n"
      return []
    all_entries = feed.entry
    if feed.GetNextLink():
      if self.cap_results:
        LOG.warning('Leaving data that matches query on server.' +
                    ' Increase max_results or set cap_results to False.')
      else:
        while feed and feed.GetNextLink():
          feed = self.GetNext(feed)
          if feed:
            all_entries.extend(feed.entry)
    # Check if title is NoneType, empty string, empty list, or a single-item
    # list containing any of the prior.
    if not titles or (len(titles) == 1 and not titles[0]):
      LOG.debug('Retrieved ' + str(len(all_entries)) +
                ' entries, returning them all')
      return all_entries

    if self.use_regex:
      # Carefully build title regex.
      if isinstance(titles, basestring):
        title_regex = titles
      else:
        title_regex = safe_decode('|'.join(titles))
      LOG.debug(safe_encode('Using regex: ' + title_regex))
      try:
        entries = [entry for entry in all_entries
                   if entry.title.text and
                   re.match(title_regex, safe_decode(entry.title.text))]
      except re.error, err:
        LOG.error('Regular expression error: ' + str(err) + '!')
        entries = []
    else:
      if isinstance(titles, list):
        title_list = titles
      else:
        title_list = [titles]
      entries = [entry for entry in all_entries
                 if safe_decode(entry.title.text) in title_list]
    LOG.debug('Retrieved ' + str(len(all_entries)) +
              ' entries, returning ' + str(len(entries)) + ' of them')
    return entries

  GetEntries = get_entries

  def get_single_entry(self, uri_or_entry_list, title=None, converter=None,
                       desired_class=None):
    """Return exactly one entry.

    Uses GetEntries to retrieve the entries, then asks the user to select one of
    them by entering a number.

    Keyword arguments:
      uri_or_entry_list: URI to get feed from (See get_entries) or list of
                         entries to select from.
      title: string Title to match on. See get_entries. Default None.
      converter: Conversion function to apply to feed. See get_entries.
      desired_class: class to which a successful response should be converted.
                     See get_entries.

    Returns:
      None if there were no matches, or one entry matching the given title.
    """
    if not uri_or_entry_list:
      return None

    if isinstance(uri_or_entry_list, basestring):
      entries = self.get_entries(uri_or_entry_list, title, converter,
                                 desired_class)
    elif isinstance(uri_or_entry_list, list):
      entries = uri_or_entry_list
    else:
      raise Error('Got unexpected type for uri_or_entry_list!')

    if not entries:
      return None
    if len(entries) == 1:
      return entries[0]
    elif len(entries) > 1:
      print 'More than one match for title ' + (title or '')
      for num, entry in enumerate(entries):
        print '%i) %s' % (num, safe_decode(entry.title.text))
      selection = -1
      while selection < 0 or selection > len(entries)-1:
        selection = int(raw_input('Please select one of the items by number: '))
      return entries[selection]

  GetSingleEntry = get_single_entry

  def is_token_valid(self, test_uri=None):
    """Check that the token being used is valid.

    Keyword arguments:
      test_uri: URI to pass to self.Get(). Default None (raises error).

    Returns:
      True if Get was successful, False if Get raised an exception with the
      string 'Token invalid' in its body, and raises any other exceptions.
    """
    if not test_uri:
      raise Error('No uri to test token with!' +
                  '(was is_token_valid extended?)')
    test_uri = set_max_results(test_uri, 1)
    try:
      # Try to limit the number of results we get.
      self.Get(test_uri)
    except self.request_error, err:
      LOG.debug('Token invalid! ' + str(err))
      return False
    else:
      return True

  IsTokenValid = is_token_valid

  def request_access(self, domain, display_name, scopes=None, browser=None):
    raise NotImplementedError('request_access must be defined!')
  RequestAccess = request_access

  def retry_operation(self, *args, **kwargs):
    """Retries an operation if certain status codes are returned.

    Wraps self.original_operation in a try block for catching request errors.
    self.original_operation should be an alias to the original method being
    attempted. See BaseServiceCL.retry_(get/post/delete).

    Args:
      *args: The *args passed to the operation being attempted.
      **kwargs: The **kwargs passed to the operation being attempted.

    Returns:
      Results from original operation being attempted.

    Raises:
      Exception: On exception from original operation. Certain RequestErrors
      will be caught, and the original operation attempted again, if enough
      retries remain (set by self.max_retries)
    """
    try_forever = self.max_retries <= 0
    attempts_remaining = self.max_retries
    err = None
    while try_forever or attempts_remaining:
      try:
        return self.original_operation(*args, **kwargs)
      except self.request_error, err:
        try:
          # RequestError defined in gdata.client
          status_code = err.status
        except AttributeError:
          # RequestError defined in gdata.service (and raised by GDataService)
          status_code = err.args[0]['status']
        if status_code in HTTP_ERROR_CODES_TO_RETRY_ON:
          attempts_remaining -= 1
          LOG.debug('Retrying when you would have failed otherwise!')
          LOG.debug('Arguments: %s' % str(args))
          LOG.debug('Keyword arguments: %s' % kwargs)
          LOG.debug('Error: %s' % err)
          if try_forever or attempts_remaining:
            time.sleep(self.retry_delay)
        else:
          raise err
      except Exception, unexpected:
        LOG.debug('unexpected exception: %s' % unexpected)
        LOG.debug('Arguments: %s' % str(args))
        LOG.debug('Keyword arguments: %s' % kwargs)
        raise unexpected
    # Can only leave above loop if err is set at least once.
    raise err


def set_max_results(uri, max):
  """Set max-results parameter if it is not set already."""
  max_str = str(max)
  if uri.find('?') == -1:
    return uri + '?max-results=' + max_str
  else:
    if uri.find('max-results') == -1:
      return uri + '&max-results=' + max_str
    else:
      return uri


# The use of login_required has been deprecated - all tasks now require
# logging in, and google.py does not check whether or not a task
# says otherwise.
class Task(object):
  """A container of requirements.

  Each requirement matches up with one of the attributes of the option parser
  used to parse command line arguments. Requirements are given as lists.
  For example, if a task needs to have attr1 and attr2 and either attr3 or 4,
  the list would look like ['attr1', 'attr2', ['attr3', 'attr4']]
  """

  def __init__(self, description, callback=None, required=[], optional=[],
               login_required=True, args_desc=''):
    """Constructor.

    Keyword arguments:
      description: Description of what the task does.
      callback: Function to use to execute task.
                (Default None, prints a message instead of running)
      required: Required options for the task. (Default None)
      optional: Optional options for the task. (Default None)
      login_required: If logging in with a username is required to do this task.
                If True, can typically ignore 'user' as a required attribute.
                (Default True)
      args_desc: Description of what the arguments should be.
                 (Default '', for no arguments necessary for this task)
    """
    if isinstance(required, basestring):
      required = [required]
    if isinstance(optional, basestring):
      optional = [optional]
    self.description = description
    self.run = callback or self._not_impl
    self.required = required
    self.optional = optional
    self.login_required = login_required
    # Take the "required" list, join all the terms by the following rules:
    # 1) if the term is a string, leave it.
    # 2) if the term is a list, join it with the ' OR ' string.
    # Then join the resulting list with ' AND '.
    if self.required:
      req_str = ' AND '.join(['('+' OR '.join(a)+')' if isinstance(a, list) \
                              else a for a in self.required])
    else:
      req_str = 'none'
    if self.optional:
      opt_str = ' Optional: ' + str(self.optional)[1:-1].replace("'", '')
    else:
      opt_str = ''
    if args_desc:
      args_desc = ' Arguments: ' + args_desc
    self.usage = 'Requires: ' + req_str + opt_str + args_desc

  def get_outstanding_requirements(self, options):
    """Return a list of required options that are missing.

    The requirements that have been specified in <options> are removed
    from self.required, and any sublists in self.required have been replaced
    by the first item in that sublist if none of the requirements in the
    sublist were given.

    Args:
      options: instance Has attributes with names corresponding to the
               requirements specified by self.required and self.optional

    Returns:
      A subset of self.required containing only strings representing unmet
      requirements.
    """
    missing_options_set = set(attr for attr in dir(options)
                              if not attr.startswith('_') and
                              getattr(options, attr) is None)
    missing_requirements = []
    for requirement in self.required:
      if isinstance(requirement, list):
        sub_req_set = set(requirement)
        # If every element in sub_req_set is in missing_options_set,
        # add the first element of the requirements list to the missing
        # requirements.
        if sub_req_set <= missing_options_set:
          missing_requirements.append(requirement[0])
        # Otherwise, the user specified one of the elements of the list, so
        # we can use that one.
      elif requirement in missing_options_set:
        missing_requirements.append(requirement)
    return missing_requirements

  def is_optional(self, attribute):
    """See if an attribute is optional"""
    # No list of lists in the optional fields
    if attribute in self.optional:
      return True
    return False

  def _not_impl(self, *args):
    """Just use this as a place-holder for Task callbacks."""
    LOG.error('Sorry, this task is not yet implemented!')


class BaseEntryToStringWrapper(object):
  """Wraps GDataEntries to easily get human-readable data."""
  def __init__(self, gdata_entry,
               intra_property_delimiter='',
               label_delimiter=' ',
               default_url_field='site'):
    """Constructor.

    Keyword arguments:
      gdata_entry: The GDataEntry to extract data from.
      intra_property_delimiter: Delimiter to distinguish between multiple
                   values in a single property (e.g. multiple email addresses).
                   Default '' (there will always be at least one space).
      label_delimiter: String to place in front of a label for intra-property
                       values. For example, for a contact with multiple phone
                       numbers, ':' would yield "Work:<number> Home:<number>"
                       Default ' ' (there is no whitespace between label and
                       value if it is not specified).
                       Set as NoneType to omit labels entirely.
    """
    self.entry = gdata_entry
    self.intra_property_delimiter = intra_property_delimiter
    self.label_delimiter = label_delimiter
    self.default_url_field = default_url_field

  @property
  def debug(self):
    """dir(self.entry)."""
    return str(dir(self.entry))

  @property
  def title(self):
    """Title or name. For Contacts v1, job title."""
    return self.entry.title.text
  name = title

  @property
  def url(self):
    """url_direct or url_site, depending on url_field defined in config."""
    return self._url(self.default_url_field)

  @property
  def url_direct(self):
    """Url that leads directly to content."""
    return self._url('direct')

  @property
  def url_site(self):
    """Url that leads to site hosting content."""
    return self._url('site')

  def _url(self, subfield):
    if not self.entry.GetHtmlLink():
      href = ''
    else:
      href = self.entry.GetHtmlLink().href

    if subfield == 'direct':
      return self.entry.content.src or href
    return href or self.entry.content.src

  @property
  def summary(self):
    """Summary or description."""
    try:
      # Try to access the "default" description
      value = self.entry.media.description.text
    except AttributeError:
      # If it's not there, try the summary attribute
      value = self.entry.summary.text
    else:
      if not value:
        # If the "default" description was there, but it was empty,
        # try the summary attribute.
        value = self.entry.summary.text
    return value
  description = summary

  @property
  def xml(self):
    """Raw XML."""
    return str(self.entry)

  def _extract_label(self, entry_list_item, label_attr=None):
    """Determine the human-readable label of the item."""
    if label_attr and hasattr(entry_list_item, label_attr):
      scheme_or_label = getattr(entry_list_item, label_attr)
    elif hasattr(entry_list_item, 'rel'):
      scheme_or_label = entry_list_item.rel
    elif hasattr(entry_list_item, 'label'):
      scheme_or_label = entry_list_item.label
    else:
      return None

    if scheme_or_label:
      return scheme_or_label[scheme_or_label.find('#')+1:]
    else:
      return None

  def _join(self, entry_list, text_attribute='text',
            text_extractor=None, label_attribute=None):
    """Join a list of entries into a string.

    Keyword arguments:
      entry_list: List of entries to be joined.
      text_attribute: String of the attribute that will give human readable
                      text for each entry in entry_list. Default 'text'.
      text_extractor: Function that can be used to get desired text.
                      Default None. Use this if the readable data is buried
                      deeper than a single attribute.
      label_attribute: If the attribute for the label is not 'rel' or 'label'
                       it can be specified here.

    Returns:
      String from joining the items in entry_list.
    """
    if not text_extractor:
      if not text_attribute:
        raise Error('One of "text_extractor" or ' +
                    '"text_attribute" must be defined!')
      text_extractor = lambda entry: getattr(entry, text_attribute)

    # It should be impossible to get a non-string from text_extractor.
    if len(entry_list) == 1:
      return text_extractor(entry_list[0])

    if self.label_delimiter is None:
      return self.intra_property_delimiter.join([text_extractor(e)
                                                 for e in entry_list
                                                 if text_extractor(e)])
    else:
      separating_string = self.intra_property_delimiter + ' '
      joined_string = ''
      for entry in entry_list:
        if self.label_delimiter is not None:
          label = self._extract_label(entry, label_attr=label_attribute)
          if label:
            joined_string += label + self.label_delimiter
        joined_string += text_extractor(entry) + separating_string
      return joined_string.rstrip(separating_string)


def compile_entry_string(wrapped_entry, attribute_list, delimiter,
                         missing_field_value=None, newline_replacer=' '):
  """Return a useful string describing a gdata.data.GDEntry.

  Keyword arguments:
    wrapped_entry: BaseEntryToStringWrapper or subclass to display.
    attribute_list: List of attributes to access
    delimiter: String to use as the delimiter between attributes.
    missing_field_value: If any of the fields for any of the entries are
                         invalid or undefined, put this in its place
                         (Default None to use "missing_field_value" config
                         option).
    newline_replacer: String to replace newlines with. Default ' '. Set to
                      NoneType to leave newlines in place.
  """
  return_string = ''
  if not delimiter:
    delimiter = ','
  if delimiter.strip() == ',':
    wrapped_entry.intra_property_delimiter = ';'
  else:
    wrapped_entry.intra_property_delimiter = ','
  for attr in attribute_list:
    try:
      # Get the value, replacing NoneTypes and empty strings
      # with the missing field value.
      val = getattr(wrapped_entry, attr.replace('-','_')) or missing_field_value
    except ValueError, err:
      LOG.debug(err.args[0] + ' (Did not add value for field ' + attr + ')')
    except AttributeError, err:
      LOG.debug(err.args[0] + ' (value for field ' + attr + ')')
      try:
        # Last ditch effort to blindly grab the attribute
        val = getattr(wrapped_entry.entry, attr).text or missing_field_value
      except AttributeError:
        LOG.debug(err.args[0] + ' (value for field ' + attr + ')')
        val = missing_field_value
    # Apparently, atom(?) doesn't always return a Unicode type when there are
    # non-latin characters, so force everything to Unicode.
    val = safe_decode(val)
    # Ensure the delimiter won't appear in a non-delineation role,
    # but let it slide if the raw xml is being dumped
    if attr != 'xml':
      return_string += val.replace(delimiter, ' ') + delimiter
    else:
      return_string = val
    # Don't do processing if attribute is xml
    if attr != 'xml':
      return_string = return_string.replace('\n', newline_replacer)

  return_string = return_string.rstrip(delimiter)
  return_string = return_string.encode(googlecl.TERMINAL_ENCODING,
                                       'backslashreplace')
  return return_string


def generate_tag_sets(tags):
  """Generate sets of tags based on a string.

  Keyword arguments:
    tags: Comma-separated list of tags. Tags with a '-' in front will be
          removed from each photo. A tag of '--' will delete all tags.
          A backslash in front of a '-' will keep the '-' in the tag.
          Examples:
            'tag1, tag2, tag3'      Add tag1, tag2, and tag3
            '-tag1, tag4, \-tag5'   Remove tag1, add tag4 and -tag5
            '--, tag6'              Remove all tags, then add tag6
  Returns:
    (remove_set, add_set, replace_tags) where...
      remove_set: set object of the tags to remove
      add_set: set object of the tags to add
      replace_tags: boolean indicating if all the old tags are removed
  """
  tags = tags.replace(', ', ',')
  tagset = set(tags.split(','))
  remove_set = set(tag[1:] for tag in tagset if tag[0] == '-')
  if '-' in remove_set:
    replace_tags = True
  else:
    replace_tags = False
  add_set = set()
  if len(remove_set) != len(tagset):
    # TODO: Can do this more cleanly with regular expressions?
    for tag in tagset:
      # Remove the escape '\' for calculation of 'add' set
      if tag[:1] == '\-':
        add_set.add(tag[1:])
      # Don't add the tags that are being removed
      elif tag[0] != '-':
        add_set.add(tag)
  return (remove_set, add_set, replace_tags)
