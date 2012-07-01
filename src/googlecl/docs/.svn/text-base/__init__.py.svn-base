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
import googlecl
import googlecl.base
import logging
import os

# gdata 1.2.4 doesn't have these defined, but uses them along with
# a namespace definition.
try:
  from gdata.docs.data import DOCUMENT_LABEL, SPREADSHEET_LABEL, \
                              PRESENTATION_LABEL, FOLDER_LABEL, PDF_LABEL
except ImportError:
  DOCUMENT_LABEL = 'document'
  SPREADSHEET_LABEL = 'spreadsheet'
  PRESENTATION_LABEL = 'presentation'
  FOLDER_LABEL = 'folder'
  PDF_LABEL = 'pdf'

# Drawing label isn't defined even in more recent gdata
DRAWING_LABEL = 'drawing'


service_name = __name__.split('.')[-1]
LOGGER_NAME = __name__
SECTION_HEADER = service_name.upper()
LOG = logging.getLogger(LOGGER_NAME)


def get_document_type(entry):
  """Extracts the type of document given DocsEntry is.

  This method returns the type of document the DocsEntry represents. Possible
  values are document, presentation, spreadsheet, folder, or pdf.
  This function appears in gdata-2.x.x python client libraries, and is
  copied here for compatibility with gdata-1.2.4.

  Returns:
    A string representing the type of document.
  """
  data_kind_scheme = 'http://schemas.google.com/g/2005#kind'
  if entry.category:
    for category in entry.category:
      if category.scheme == data_kind_scheme:
        return category.label
  else:
    return None


def get_extension_from_doctype(doctype_label, config_parser):
  """Return file extension based on document type and preferences file."""
  LOG.debug('In get_extension_from_doctype, doctype_label: ' +
             str(doctype_label))
  ext = None
  if doctype_label == SPREADSHEET_LABEL:
    ext = config_parser.safe_get(SECTION_HEADER, 'spreadsheet_format')
  elif doctype_label == DOCUMENT_LABEL:
    ext = config_parser.safe_get(SECTION_HEADER, 'document_format')
  elif doctype_label == PDF_LABEL:
    ext = 'pdf'
  elif doctype_label == PRESENTATION_LABEL:
    ext = config_parser.safe_get(SECTION_HEADER, 'presentation_format')
  elif doctype_label == DRAWING_LABEL:
    ext = config_parser.safe_get(SECTION_HEADER, 'drawing_format')
  elif doctype_label is not None:
    LOG.error('Unknown document type label: %s' % doctype_label)
  if not ext:
    ext = config_parser.safe_get(SECTION_HEADER, 'format')
  return ext


def get_editor(doctype_label, config_parser):
  """Return editor for file based on entry type and preferences file.

  Editor is determined in an order of preference:
  1) Try to load the editor for the specific type (spreadsheet, document, etc.)
  2) If no specification, try to load the "editor" option from config file.
  3) If no default editor, try to load the EDITOR environment variable.
  4) If no EDITOR variable, return None.

  Keyword arguments:
    doctype_label: A string representing the type of document to edit.

  Returns:
    Editor to use to edit the document.
  """
  LOG.debug('In get_editor, doctype_label: ' + str(doctype_label))
  editor = None
  if doctype_label == SPREADSHEET_LABEL:
    editor = config_parser.safe_get(SECTION_HEADER, 'spreadsheet_editor')
  elif doctype_label == DOCUMENT_LABEL:
    editor = config_parser.safe_get(SECTION_HEADER, 'document_editor')
  elif doctype_label == PDF_LABEL:
    editor = config_parser.safe_get(SECTION_HEADER, 'pdf_editor')
  elif doctype_label == PRESENTATION_LABEL:
    editor = config_parser.safe_get(SECTION_HEADER, 'presentation_editor')
  elif doctype_label is not None:
    LOG.error('Unknown document type label: %s' % doctype_label)
  if not editor:
    editor = config_parser.safe_get(SECTION_HEADER, 'editor')
  if not editor:
    editor = os.getenv('EDITOR')
  return editor


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_get(client, options, args):
  if not hasattr(client, 'Download'):
    LOG.error('Downloading documents is not supported for' +
              ' gdata-python-client < 2.0')
    return
  titles_list = googlecl.build_titles_list(options.title, args)
  folder_entries = client.get_folder(options.folder)
  entries = client.get_doclist(titles_list, folder_entries)
  if not os.path.isdir(options.dest) and len(entries) > 1:
    LOG.error(googlecl.safe_encode(u'Specified multiple source files, but ' +
                                   u'destination "' + options.dest +
                                   u'" is not a directory'))
    return
  client.get_docs(options.dest, entries, file_ext=options.format)


def _run_list(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  folder_entries = client.get_folder(options.folder)
  entries = client.get_doclist(titles_list, folder_entries)
  for entry in entries:
    print googlecl.base.compile_entry_string(
                               googlecl.base.BaseEntryToStringWrapper(entry),
                               options.fields.split(','),
                               delimiter=options.delimiter)


def _run_upload(client, options, args):
  folder_entries = client.get_folder(options.folder)
  folder_entry = client.get_single_entry(folder_entries)
  docs_list = options.src + args
  successful_docs = client.upload_docs(docs_list,
                                       title=options.title,
                                       folder_entry=folder_entry,
                                       file_ext=options.format,
                                       convert=options.convert)


def _run_edit(client, options, args):
  if args:
    LOG.info('Sorry, no support for additional arguments for '
             '"docs edit" yet')
    LOG.debug('(Ignoring ' + unicode(args) +')')

  if not hasattr(client, 'Download'):
    LOG.error('Editing documents is not supported' +
              ' for gdata-python-client < 2.0')
    return
  folder_entry_list = client.get_folder(options.folder)
  doc_entry = client.get_single_doc(options.title, folder_entry_list)
  if doc_entry:
    doc_entry_or_title = doc_entry
    doc_type = get_document_type(doc_entry)
  else:
    doc_entry_or_title = options.title
    doc_type = None
    LOG.debug('No matching documents found! Will create one.')
  folder_entry = client.get_single_entry(folder_entry_list)
  if not folder_entry and options.folder:
    # Don't tell the user no matching folders were found if they didn't
    # specify one.
    LOG.debug('No matching folders found! Will create them.')
  format_ext = options.format or \
               get_extension_from_doctype(doc_type, client.config)
  editor = options.editor or get_editor(doc_type, client.config)
  if not editor:
    LOG.error('No editor defined!')
    LOG.info('Define an "editor" option in your config file, set the ' +
             'EDITOR environment variable, or pass an editor in with --editor.')
    return
  if not format_ext:
    LOG.error('No format defined!')
    LOG.info('Define a "format" option in your config file,' +
             ' or pass in a format with --format')
    return
  doc = client.edit_doc(doc_entry_or_title, editor, format_ext,
                        folder_entry_or_path=folder_entry or options.folder)
  if doc is not None:
    LOG.info('Document successfully edited! %s', doc.GetHtmlLink().href)


def _run_delete(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  folder_entries = client.get_folder(options.folder)
  entries = client.get_doclist(titles_list, folder_entries)
  client.DeleteEntryList(entries, 'document', options.prompt)


TASKS = {'upload': googlecl.base.Task('Upload a document',
                                      callback=_run_upload,
                                      required='src',
                                      optional=['title', 'folder', 'format']),
         'edit': googlecl.base.Task('Edit a document', callback=_run_edit,
                                    required=['title'],
                                    optional=['format', 'editor', 'folder']),
         'get': googlecl.base.Task('Download a document', callback=_run_get,
                                   required=[['title', 'folder'], 'dest'],
                                   optional='format'),
         'list': googlecl.base.Task('List documents', callback=_run_list,
                                    required=['fields', 'delimiter'],
                                    optional=['title', 'folder']),
         'delete': googlecl.base.Task('Delete documents',
                                      callback=_run_delete,
                                      required='title',
                                      optional='folder')}
