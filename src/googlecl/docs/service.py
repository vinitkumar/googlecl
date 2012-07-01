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


"""Service details and instances for the Docs service.

Some use cases:
Upload a document:
  docs upload --folder "Some folder" path_to_doc

Edit a document in your word editor:
  docs edit --title "Grocery List" --editor vim (editor also set in prefs)

Download docs:
  docs get --folder "Some folder"

"""
from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import gdata.docs.service
import logging
import os
import shutil
import googlecl
import googlecl.base
import googlecl.service
from googlecl.docs import SECTION_HEADER
import googlecl.docs.base

# Renamed here to reduce verbosity in other sections
safe_encode = googlecl.safe_encode
safe_decode = googlecl.safe_decode


LOG = logging.getLogger(googlecl.docs.LOGGER_NAME + '.service')


class DocsServiceCL(gdata.docs.service.DocsService,
                    googlecl.docs.base.DocsBaseCL,
                    googlecl.service.BaseServiceCL):

  """Extends gdata.docs.service.DocsClient for the command line.

  This class adds some features focused on using Google Docs via an installed
  app with a command line interface.

  """
  DOCLIST_FEED_URI = '/feeds/documents/private/full'

  def __init__(self, config):
    """Constructor."""
    gdata.docs.service.DocsService.__init__(self, source='GoogleCL')
    googlecl.service.BaseServiceCL.__init__(self, SECTION_HEADER, config)
    # 302 Moved Temporarily errors began cropping up for new style docs
    # during export. Using https solves the problem, so set ssl True here.
    self.ssl = True

  def _DownloadFile(self, uri, file_path):
    """Downloads a file.

    Overloaded from docs.service.DocsService to optionally decode from UTF.

    Args:
      uri: string The full Export URL to download the file from.
      file_path: string The full path to save the file to.

    Raises:
      RequestError: on error response from server.
    """
    server_response = self.request('GET', uri)
    response_body = server_response.read()
    if server_response.status != 200:
      raise gdata.service.RequestError, {'status': server_response.status,
                                         'reason': server_response.reason,
                                         'body': response_body}
    if googlecl.docs.base.can_export(uri) and\
       self.config.lazy_get(SECTION_HEADER, 'decode_utf_8', False, bool):
      try:
        file_string = response_body.decode('utf-8-sig')
      except UnicodeError, err:
        LOG.debug('Could not decode: ' + str(err))
        file_string = response_body
    else:
      file_string = response_body
    with open(file_path, 'wb') as download_file:
      download_file.write(file_string)
      download_file.flush()

  def _create_folder(self, title, folder_or_uri=None):
    """Stolen from gdata-2.0.10 to make recursive directory upload work."""
    try:
      return gdata.docs.service.DocsService.CreateFolder(self, title,
                                                         folder_or_uri)
    except AttributeError:
      import atom
      if folder_or_uri:
        try:
          uri = folder_or_uri.content.src
        except AttributeError:
          uri = folder_or_uri
      else:
        uri = '/feeds/documents/private/full'

      folder_entry = gdata.docs.DocumentListEntry()
      folder_entry.title = atom.Title(text=title)
      folder_entry.category.append(_make_kind_category(
                                               googlecl.docs.FOLDER_LABEL))
      folder_entry = self.Post(folder_entry, uri,
                               converter=gdata.docs.DocumentListEntryFromString)
      return folder_entry

  def _determine_content_type(self, file_ext):
    from gdata.docs.service import SUPPORTED_FILETYPES
    try:
      return SUPPORTED_FILETYPES[file_ext.upper()]
    except KeyError:
      LOG.info('No supported filetype found for extension %s', file_ext)
      return None

  def export(self, entry_or_id_or_url, file_path, gid=None, extra_params=None):
    """Export old and new version docs.

    Ripped from gdata.docs.DocsService, adds 'format' parameter to make
    new version documents happy.

    """
    ext = googlecl.get_extension_from_path(file_path)
    if ext:
      if extra_params is None:
        extra_params = {}
      # Fix issue with new-style docs always downloading to PDF
      # (gdata-issues Issue 2157)
      extra_params['format'] = ext
    self.Download(entry_or_id_or_url, file_path, ext, gid, extra_params)

  Export = export

  def get_doclist(self, titles=None, folder_entry_list=None):
    """Get a list of document entries from a feed.

    Keyword arguments:
      titles: list or string Title(s) of entries to return. Will be compared
             to entry.title.text, using regular expressions if self.use_regex.
             Default None for all entries from feed.
      folder_entry_list: List of GDataEntry's of folders to get from.
             Only files found in these folders will be returned.
             Default None for all folders.

    Returns:
      List of entries.

    """
    if folder_entry_list:
      entries = []
      for folder in folder_entry_list:
        # folder.content.src is the uri to query for documents in that folder.
        entries.extend(self.GetEntries(folder.content.src,
                                       titles,
                               converter=gdata.docs.DocumentListFeedFromString))
    else:
      query = gdata.docs.service.DocumentQuery()
      entries = self.GetEntries(query.ToUri(),
                                titles,
                                converter=gdata.docs.DocumentListFeedFromString)
    return entries

  def get_single_doc(self, title=None, folder_entry_list=None):
    """Return exactly one doc_entry.

    Keyword arguments:
      title: Title to match on for document. Default None for any title.
      folder_entry_list: GDataEntry of folders to look in.
                         Default None for any folder.

    Returns:
      None if there were no matches, or one entry matching the given title.

    """
    if folder_entry_list:
      if len(folder_entry_list) == 1:
        return self.GetSingleEntry(folder_entry_list[0].content.src,
                                   title,
                                converter=gdata.docs.DocumentListFeedFromString)
      else:
        entries = self.get_doclist(title, folder_entry_list)
        # Technically don't need the converter for this call
        # because we have the entries.
        return self.GetSingleEntry(entries, title)
    else:
      return self.GetSingleEntry(gdata.docs.service.DocumentQuery().ToUri(),
                                 title,
                                converter=gdata.docs.DocumentListFeedFromString)

  GetSingleDoc = get_single_doc

  def get_folder(self, title):
    """Return entries for one or more folders.

    Keyword arguments:
      title: Title of the folder.

    Returns:
      GDataEntry representing a folder, or None of title is None.

    """
    if title:
      query = gdata.docs.service.DocumentQuery(categories=['folder'],
                                               params={'showfolders': 'true'})
      folder_entries = self.GetEntries(query.ToUri(), title)
      if not folder_entries:
        LOG.warning('No folder found that matches ' + title)
      return folder_entries
    else:
      return None

  GetFolder = get_folder

  def is_token_valid(self, test_uri=None):
    """Check that the token being used is valid."""
    if not test_uri:
      docs_uri = gdata.docs.service.DocumentQuery().ToUri()
      sheets_uri = ('https://spreadsheets.google.com/feeds/spreadsheets'
                    '/private/full')
    docs_test = googlecl.service.BaseServiceCL.IsTokenValid(self, docs_uri)
    sheets_test = googlecl.service.BaseServiceCL.IsTokenValid(self, sheets_uri)
    return docs_test and sheets_test

  IsTokenValid = is_token_valid

  def _modify_entry(self, doc_entry, path_to_new_content, file_ext):
    """Replace content of a DocEntry.

    Args:
      doc_entry: DocEntry whose content will be replaced.
      path_to_new_content: str Path to file that has new content.
      file_ext: str Extension to use to determine MIME type of upload
                (e.g. 'txt', 'doc')

    """
    from gdata.docs.service import SUPPORTED_FILETYPES
    try:
      content_type = SUPPORTED_FILETYPES[file_ext.upper()]
    except KeyError:
      print 'Could not find mimetype for ' + file_ext
      while file_ext not in SUPPORTED_FILETYPES.keys():
        file_ext = raw_input('Please enter one of ' +
                                SUPPORTED_FILETYPES.keys() +
                                ' for a content type to upload as.')
      content_type = SUPPORTED_FILETYPES[file_ext.upper()]
    mediasource = gdata.MediaSource(file_path=path_to_new_content,
                                    content_type=content_type)
    return self.Put(mediasource, doc_entry.GetEditMediaLink().href)

  def request_access(self, domain, display_name, scopes=None, browser=None):
    """Request access as in BaseServiceCL, but specify scopes."""
    # When people use docs (writely), they expect access to
    # spreadsheets as well (wise).
    if not scopes:
      scopes = gdata.service.CLIENT_LOGIN_SCOPES['writely'] +\
               gdata.service.CLIENT_LOGIN_SCOPES['wise']
    return googlecl.service.BaseServiceCL.request_access(self, domain,
                                                         display_name,
                                                         scopes=scopes,
                                                         browser=browser)

  RequestAccess = request_access

  def _transmit_doc(self, path, entry_title, post_uri, content_type, file_ext):
    """Upload a document.

    The final step in uploading a document. The process differs between versions
    of the gdata python client library, hence its definition here.

    Args:
      path: Path to the file to upload.
      entry_title: Name of the document.
      post_uri: URI to make request to.
      content_type: MIME type of request.
      file_ext: File extension that determined the content_type.

    Returns:
      Entry representing the document uploaded.
    """
    media = gdata.MediaSource(file_path=path, content_type=content_type)
    try:
      # Upload() wasn't added until later versions of DocsService, so
      # we may not have it.
      return self.Upload(media, entry_title, post_uri)
    except AttributeError:
      import atom
      entry = gdata.docs.DocumentListEntry()
      entry.title = atom.Title(text=entry_title)
      # Cover the supported filetypes in gdata-2.0.10 even though
      # they aren't listed in gdata 1.2.4... see what happens.
      if file_ext.lower() in ['csv', 'tsv', 'tab', 'ods', 'xls', 'xlsx']:
        category = _make_kind_category(googlecl.docs.SPREADSHEET_LABEL)
      elif file_ext.lower() in ['ppt', 'pps']:
        category = _make_kind_category(googlecl.docs.PRESENTATION_LABEL)
      elif file_ext.lower() in ['pdf']:
        category = _make_kind_category(googlecl.docs.PDF_LABEL)
      # Treat everything else as a document
      else:
        category = _make_kind_category(googlecl.docs.DOCUMENT_LABEL)
      entry.category.append(category)
      # To support uploading to folders for earlier
      # versions of the API, expose the lower-level Post
      return self.Post(entry, post_uri, media_source=media,
                       extra_headers={'Slug': media.file_name},
                       converter=gdata.docs.DocumentListEntryFromString)


SERVICE_CLASS = DocsServiceCL


def _make_kind_category(label):
  """Stolen from gdata-2.0.10 docs.service."""
  import atom
  if label is None:
    return None
  documents_namespace = 'http://schemas.google.com/docs/2007'
  return atom.Category(scheme=gdata.docs.service.DATA_KIND_SCHEME,
                       term=documents_namespace + '#' + label, label=label)
