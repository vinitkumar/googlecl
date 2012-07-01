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


"""Service details and instances for the Picasa service."""


from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import logging
import os
import urllib
import time

import gdata.photos
from gdata.photos.service import PhotosService, GooglePhotosException

import googlecl
import googlecl.base
import googlecl.service
import googlecl.picasa
import googlecl.calendar.date

# Shortening the names of these guys.
safe_encode = googlecl.safe_encode
safe_decode = googlecl.safe_decode

LOG = logging.getLogger(googlecl.picasa.LOGGER_NAME)
SUPPORTED_VIDEO_TYPES = {'wmv': 'video/x-ms-wmv',
                         'avi': 'video/avi',
                         '3gp': 'video/3gpp',
                         'mov': 'video/quicktime',
                         'qt': 'video/quicktime',
                         'mp4': 'video/mp4',
                         'mpa': 'video/mpeg',
                         'mpe': 'video/mpeg',
                         'mpeg': 'video/mpeg',
                         'mpg': 'video/mpeg',
                         'mpv2': 'video/mpeg',
                         'mpeg4': 'video/mpeg4',}
# XXX gdata.photos.service contains a very strange check against (outdated)
# allowed MIME types. This is a hack to allow videos to be uploaded.
# We're creating a list of the allowed video types stripped of the initial
# 'video/', eliminating duplicates via set(), then converting to tuple()
# since that's what gdata.photos.service uses.
gdata.photos.service.SUPPORTED_UPLOAD_TYPES += \
   tuple(set([vtype.split('/')[1] for vtype in SUPPORTED_VIDEO_TYPES.values()]))
DOWNLOAD_VIDEO_TYPES = {'swf': 'application/x-shockwave-flash',
                        'mp4': 'video/mpeg4',}


class PhotosServiceCL(PhotosService, googlecl.service.BaseServiceCL):

  """Extends gdata.photos.service.PhotosService for the command line.

  This class adds some features focused on using Picasa via an installed app
  with a command line interface.

  """

  def __init__(self, config):
    """Constructor."""
    PhotosService.__init__(self)
    googlecl.service.BaseServiceCL.__init__(self,
                                            googlecl.picasa.SECTION_HEADER,
                                            config)

  def build_entry_list(self, user='default', titles=None, query=None,
                       force_photos=False, photo_title=None):
    """Build a list of entries of either photos or albums.

    If no title is specified, entries will be of photos matching the query.
    If no query is specified, entries will be of albums matching the title.
    If both title and query are specified, entries will be of photos matching
      the query that are also in albums matching the title.

    Keyword arguments:
      user: Username of the owner of the albums / photos (Default 'default').
      titles: list Titles of the albums (Default None).
      query: Query for photos, url-encoded (Default None).
      force_photos: If true, returns photo entries, even if album entries would
                    typically be returned. The entries will be for all photos
                    in each album.
      photo_title: Title of the photo(s) to return. Default None for all photos.

    Returns:
      A list of entries, as specified above.

    """
    album_entry = []
    if titles[0] or not(titles[0] or query):
      album_entry = self.GetAlbum(user=user, titles=titles)
    if photo_title or query or force_photos:
      uri = '/data/feed/api/user/' + user
      if query and not album_entry:
        entries = self.GetEntries(uri + '?kind=photo&q=' + query, photo_title)
      else:
        entries = []
        uri += '/albumid/%s?kind=photo'
        if query:
          uri += '&q=' + query
        for album in album_entry:
          photo_entries = self.GetEntries(uri % album.gphoto_id.text,
                                          photo_title)
          entries.extend(photo_entries)
    else:
      entries = album_entry

    return entries

  def create_album(self, title, summary, access, date):
    """Create photo album

    Args:
      title: Title of the album.
      summary: Summary or description of the album.
      access: Access level string. See the picasa package __init__ file for
          valid values.
      date: Date on the album, as a string.  If eveluates to False, uses today.

    Returns:
      AlbumEntry of newly created album.
    """
    if date:
      parser = googlecl.calendar.date.DateParser()
      date = parser.determine_day(date, shift_dates=False)
      if date:
        timestamp = time.mktime(date.timetuple())
        timestamp_ms = '%i' % int((timestamp * 1000))
      else:
        LOG.error('Could not parse date %s. (Picasa only takes day info)' %
                  date)
        timestamp_ms = ''
    else:
      timestamp_ms = ''

    access = googlecl.picasa._map_access_string(access)
    return self.InsertAlbum(title=title, summary=summary,
                            access=access,
                            timestamp=timestamp_ms)

  CreateAlbum = create_album

  def download_album(self, base_path, user, video_format='mp4', titles=None,
                     photo_title=None):
    """Download an album to the local host.

    Keyword arguments:
      base_path: Path on the filesystem to copy albums to. Each album will
                 be stored in base_path/<album title>. If base_path does not
                 exist, it and each non-existent parent directory will be
                 created.
      user: User whose albums are being retrieved. (Default 'default')
      titles: list or string Title(s) that the album(s) should have.
              Default None, for all albums.

    """
    def _get_download_info(photo_or_video, video_format):
      """Get download link and extension for photo or video.

      video_format must be in DOWNLOAD_VIDEO_TYPES.

      Returns:
        (url, extension)
      """
      wanted_content = None
      for content in photo_or_video.media.content:
        if content.medium == 'image' and not wanted_content:
          wanted_content = content
        elif content.type == DOWNLOAD_VIDEO_TYPES[video_format]:
          wanted_content = content
      if not wanted_content:
        LOG.error('Did not find desired medium!')
        LOG.debug('photo_or_video.media:\n' + photo_or_video.media)
        return None
      elif wanted_content.medium == 'image':
        url = googlecl.picasa.make_download_url(photo_or_video.content.src)
        mimetype = photo_or_video.content.type
        extension = mimetype.split('/')[1]
      else:
        url = wanted_content.url
        extension = video_format
      return (url, extension)
    # End _get_download_info

    if not user:
      user = 'default'
    entries = self.GetAlbum(user=user, titles=titles)
    if video_format not in DOWNLOAD_VIDEO_TYPES.keys():
      LOG.error('Unsupported video format: ' + video_format)
      LOG.info('Try one of the following video formats: ' +
               str(DOWNLOAD_VIDEO_TYPES.keys())[1:-1])
      video_format = 'mp4'
      LOG.info('Downloading videos as ' + video_format)

    for album in entries:
      album_path = os.path.join(base_path, safe_decode(album.title.text))
      album_concat = 1
      if os.path.exists(album_path):
        base_album_path = album_path
        while os.path.exists(album_path):
          album_path = base_album_path + '-%i' % album_concat
          album_concat += 1
      os.makedirs(album_path)

      uri = ('/data/feed/api/user/%s/albumid/%s?kind=photo' %
             (user, album.gphoto_id.text))
      photo_entries = self.GetEntries(uri, photo_title)

      for photo_or_video in photo_entries:
        #TODO: Test on Windows (upload from one OS, download from another)
        photo_or_video_name = safe_decode(photo_or_video.title.text)
        photo_or_video_name = photo_or_video_name.split(os.extsep)[0]
        url, extension = _get_download_info(photo_or_video, video_format)
        path = os.path.join(album_path,
                            photo_or_video_name + os.extsep + extension)
        # Check for a file extension, add it if it does not exist.
        if os.path.exists(path):
          base_path = path
          photo_concat = 1
          while os.path.exists(path):
            path = base_path + '-%i' % photo_concat
            photo_concat += 1
        LOG.info(safe_encode('Downloading %s to %s' %
                             (safe_decode(photo_or_video.title.text), path)))
        urllib.urlretrieve(url, path)

  DownloadAlbum = download_album

  def get_album(self, user='default', titles=None):
    """Get albums from a user feed.

    Keyword arguments:
      user: The user whose albums are being retrieved. (Default 'default')
      titles: list or string Title(s) that the album(s) should have.
              Default None, for all albums.

    Returns:
      List of albums that match parameters, or [] if none do.

    """
    uri = '/data/feed/api/user/' + user + '?kind=album'
    return self.GetEntries(uri, titles)

  GetAlbum = get_album

  def get_single_album(self, user='default', title=None):
    """Get a single album."""
    uri = '/data/feed/api/user/' + user + '?kind=album'
    return self.GetSingleEntry(uri, title=title)

  GetSingleAlbum = get_single_album

  def insert_media_list(self, album, media_list, tags='', user='default',
                        photo_name=None, caption=None):
    """Insert photos or videos into an album.

    Keyword arguments:
      album: The album entry of the album getting the media.
      media_list: A list of paths, each path a picture or video on
                  the local host.
      tags: Text of the tags to be added to each item, e.g. 'Islands, Vacation'
            (Default '').
      caption: Caption/summary to give each item. Default None for no caption.
    """
    album_url = ('/data/feed/api/user/%s/albumid/%s' %
                 (user, album.gphoto_id.text))
    keywords = tags
    if caption is None:
      caption = ''
    failures = []
    for path in media_list:
      LOG.info(safe_encode('Loading file ' + path + ' to album ' +
                           safe_decode(album.title.text)))

      ext = googlecl.get_extension_from_path(path)
      if not ext:
        LOG.debug('No extension match on path ' + path)
        content_type = 'image/jpeg'
      else:
        ext = ext.lower()
        try:
          content_type = SUPPORTED_VIDEO_TYPES[ext]
        except KeyError:
          content_type = 'image/' + ext.lower()
      title = photo_name
      if not title:
        title = os.path.split(path)[1]
      try:
        self.InsertPhotoSimple(album_url,
                               title=title,
                               summary=caption,
                               filename_or_handle=path,
                               keywords=keywords,
                               content_type=content_type)
      except GooglePhotosException, err:
        LOG.error('Failed to upload %s. (%s: %s)', path,
                                                   err.args[0],
                                                   err.args[1])
        failures.append(file)
      except Exception, err:
        # Don't let a stray error wreck an upload of 1000 photos
        LOG.error(safe_encode('Unexpected error -- ' + unicode(err)))
        failures.append(file)
    if failures:
      LOG.info(str(len(failures)) + ' photos failed to upload')
      LOG.debug(safe_encode('Failed files: ' + unicode(failures)))
    return failures

  InsertMediaList = insert_media_list

  def is_token_valid(self, test_uri='/data/feed/api/user/default'):
    """Check that the token being used is valid."""
    return googlecl.base.BaseCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid

  def tag_photos(self, photo_entries, tags, caption):
    """Add or remove tags on a list of photos.

    Keyword arguments:
      photo_entries: List of photo entry objects.
      tags: String representation of tags in a comma separated list.
            For how tags are generated from the string,
            see googlecl.base.generate_tag_sets(). Set None to leave the tags as
            they currently are.
      caption: New caption for the photo. Set None to leave the caption as it
          is.
    """
    from gdata.media import Group, Keywords
    from atom import Summary
    if tags is not None:
      remove_set, add_set, replace_tags = googlecl.base.generate_tag_sets(tags)
    for photo in photo_entries:
      if tags is not None:
        if not photo.media:
          photo.media = Group()
        if not photo.media.keywords:
          photo.media.keywords = Keywords()
        # No point removing tags if the photo has no keywords,
        # or we're replacing the keywords.
        if photo.media.keywords.text and remove_set and not replace_tags:
          current_tags = photo.media.keywords.text.replace(', ', ',')
          current_set = set(current_tags.split(','))
          photo.media.keywords.text = ','.join(current_set - remove_set)

        if replace_tags or not photo.media.keywords.text:
          photo.media.keywords.text = ','.join(add_set)
        elif add_set:
          photo.media.keywords.text += ',' + ','.join(add_set)

      if caption is not None:
        if not photo.summary:
          photo.summary = Summary(text=caption, summary_type='text')
        else:
          photo.summary.text = caption

      self.UpdatePhotoMetadata(photo)

  TagPhotos = tag_photos


SERVICE_CLASS = PhotosServiceCL
