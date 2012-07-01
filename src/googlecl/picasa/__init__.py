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
import datetime
import googlecl
import googlecl.base
import logging


service_name = __name__.split('.')[-1]
LOGGER_NAME = __name__
SECTION_HEADER = service_name.upper()

LOG = logging.getLogger(LOGGER_NAME)


def make_download_url(url):
  """Makes the given URL for a picasa image point to the download."""
  return url[:url.rfind('/')+1]+'d'+url[url.rfind('/'):]


def _map_access_string(access_string, default_value='private'):
  if not access_string:
    return default_value
  # It seems to me that 'private' is less private than 'protected'
  # but I'm going with what Picasa seems to be using.
  access_string_mappings = {'public': 'public',
                            'private': 'protected',
                            'protected': 'private',
                            'draft': 'private',
                            'hidden': 'private',
                            'link': 'private'}
  try:
    return access_string_mappings[access_string]
  except KeyError:
    import re
    if access_string.find('link') != -1:
      return 'private'
  return default_value


class PhotoEntryToStringWrapper(googlecl.base.BaseEntryToStringWrapper):
  caption = googlecl.base.BaseEntryToStringWrapper.summary

  @property
  def distance(self):
    """The distance to the subject."""
    return self.entry.exif.distance.text

  @property
  def ev(self):
    """Exposure value, if possible to calculate"""
    try:
      # Using the equation for EV I found on Wikipedia...
      N = float(self.fstop)
      t = float(self.exposure)
      import math       # import math if fstop and exposure work
      # str() actually "rounds" floats. Try repr(3.3) and print 3.3
      ev_long_str = str(math.log(math.pow(N,2)/t, 2))
      dec_point = ev_long_str.find('.')
      # In the very rare case that there is no decimal point:
      if dec_point == -1:
        # Technically this can return something like 10000, violating
        # our desired precision. But not likely.
        return ev_long_str
      else:
        # return value to 1 decimal place
        return ev_long_str[0:dec_point+2]
    except Exception:
      # Don't really care what goes wrong -- result is the same.
      return None

  @property
  def exposure(self):
    """The exposure time used."""
    return self.entry.exif.exposure.text
  shutter = exposure
  speed = exposure

  @property
  def flash(self):
    """Boolean value indicating whether the flash was used."""
    return self.entry.exif.flash.text

  @property
  def focallength(self):
    """The focal length used."""
    return self.entry.exif.focallength.text

  @property
  def fstop(self):
    """The fstop value used."""
    return self.entry.exif.fstop.text

  @property
  def imageUniqueID(self):
    """The unique image ID for the photo."""
    return self.entry.exif.imageUniqueID.text
  id = imageUniqueID

  @property
  def iso(self):
    """The iso equivalent value used."""
    return self.entry.exif.iso.text

  @property
  def make(self):
    """The make of the camera used."""
    return self.entry.exif.make.text

  @property
  def model(self):
    """The model of the camera used."""
    return self.entry.exif.model.text

  @property
  def tags(self):
    """Tags / keywords or labels."""
    tags_text = self.entry.media.keywords.text
    tags_text = tags_text.replace(', ', ',')
    tags_list = tags_text.split(',')
    return self.intra_property_delimiter.join(tags_list)
  labels = tags
  keywords = tags

  @property
  def time(self):
    """The date/time the photo was taken.

    Represented as the number of milliseconds since January 1st, 1970.
    Note: The value of this element should always be identical to the value of
    the <gphoto:timestamp>.
    """
    return self.entry.exif.time.text
  when = time

  # Overload from base.EntryToStringWrapper to use make_download_url
  @property
  def url_download(self):
    """URL to the original uploaded image, suitable for downloading from."""
    return make_download_url(self.url_direct)


class AlbumEntryToStringWrapper(googlecl.base.BaseEntryToStringWrapper):
  @property
  def access(self):
    """Access level of the album, one of "public", "private", or "unlisted"."""
    # Convert values to ones the user selects on the web
    txt = self.entry.access.text
    if txt == 'protected':
      return 'private'
    if txt == 'private':
      return 'anyone with link'
    return txt
  visibility = access

  @property
  def location(self):
    """Location of the album (where pictures were taken)."""
    return self.entry.location.text
  where = location

  @property
  def published(self):
    """When the album was published/uploaded in local time."""
    date = datetime.datetime.strptime(self.entry.published.text,
                                      googlecl.calendar.date.QUERY_DATE_FORMAT)
    date = date - googlecl.calendar.date.get_utc_timedelta()
    return date.strftime('%Y-%m-%dT%H:%M:%S')
  when = published


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_create(client, options, args):
  # Paths to media might be in options.src, args, both, or neither.
  # But both are guaranteed to be lists.
  media_list = options.src + args

  album = client.create_album(title=options.title, summary=options.summary,
                              access=options.access, date=options.date)
  if media_list:
    client.InsertMediaList(album, media_list=media_list,
                           tags=options.tags)
  LOG.info('Created album: %s' % album.GetHtmlLink().href)


def _run_delete(client, options, args):
  if options.query or options.photo:
    entry_type = 'media'
    search_string = options.query
  else:
    entry_type = 'album'
    search_string = options.title

  titles_list = googlecl.build_titles_list(options.title, args)
  entries = client.build_entry_list(titles=titles_list,
                                    query=options.query,
                                    photo_title=options.photo)
  if not entries:
    LOG.info('No %ss matching %s' % (entry_type, search_string))
  else:
    client.DeleteEntryList(entries, entry_type, options.prompt)


def _run_list(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  entries = client.build_entry_list(user=options.owner or options.user,
                                    titles=titles_list,
                                    query=options.query,
                                    force_photos=True,
                                    photo_title=options.photo)
  for entry in entries:
    print googlecl.base.compile_entry_string(PhotoEntryToStringWrapper(entry),
                                             options.fields.split(','),
                                             delimiter=options.delimiter)


def _run_list_albums(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  entries = client.build_entry_list(user=options.owner or options.user,
                                    titles=titles_list,
                                    force_photos=False)
  for entry in entries:
    print googlecl.base.compile_entry_string(AlbumEntryToStringWrapper(entry),
                                             options.fields.split(','),
                                             delimiter=options.delimiter)


def _run_post(client, options, args):
  media_list = options.src + args
  if not media_list:
    LOG.error('Must provide paths to media to post!')
  album = client.GetSingleAlbum(user=options.owner or options.user,
                                title=options.title)
  if album:
    client.InsertMediaList(album, media_list, tags=options.tags,
                           user=options.owner or options.user,
                           photo_name=options.photo, caption=options.summary)
  else:
    LOG.error('No albums found that match ' + options.title)


def _run_get(client, options, args):
  if not options.dest:
    LOG.error('Must provide destination of album(s)!')
    return

  titles_list = googlecl.build_titles_list(options.title, args)
  client.DownloadAlbum(options.dest,
                       user=options.owner or options.user,
                       video_format=options.format or 'mp4',
                       titles=titles_list,
                       photo_title=options.photo)


def _run_tag(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  entries = client.build_entry_list(user=options.owner or options.user,
                                    query=options.query,
                                    titles=titles_list,
                                    force_photos=True,
                                    photo_title=options.photo)
  if entries:
    client.TagPhotos(entries, options.tags, options.summary)
  else:
    LOG.error('No matches for the title and/or query you gave.')


TASKS = {'create': googlecl.base.Task('Create an album',
                                      callback=_run_create,
                                      required='title',
                                      optional=['src', 'date',
                                                'summary', 'tags', 'access']),
         'post': googlecl.base.Task('Post photos to an album',
                                    callback=_run_post,
                                    required=['title', 'src'],
                                    optional=['tags', 'owner', 'photo',
                                              'summary']),
         'delete': googlecl.base.Task('Delete photos or albums',
                                      callback=_run_delete,
                                      required=[['title', 'query']],
                                      optional='photo'),
         'list': googlecl.base.Task('List photos', callback=_run_list,
                                    required=['fields', 'delimiter'],
                                    optional=['title', 'query',
                                              'owner', 'photo']),
         'list-albums': googlecl.base.Task('List albums',
                                           callback=_run_list_albums,
                                           required=['fields', 'delimiter'],
                                           optional=['title', 'owner']),
         'get': googlecl.base.Task('Download albums', callback=_run_get,
                                   required=['title', 'dest'],
                                   optional=['owner', 'format', 'photo']),
         'tag': googlecl.base.Task('Tag/caption photos', callback=_run_tag,
                                   required=[['title', 'query'],
                                             ['tags', 'summary']],
                                   optional=['owner', 'photo'])}
