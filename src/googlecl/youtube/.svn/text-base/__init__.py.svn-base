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
import re

service_name = __name__.split('.')[-1]
LOGGER_NAME = __name__
SECTION_HEADER = service_name.upper()


def _map_access_string(access_string):
  """Map an access string to a value YouTube will understand.

  In this case, YouTube only cares about "is private" so 'public' gets mapped to
  False, everything else to True.

  Returns:
    Boolean indicating True (is private) or False (is not private).
  """
  if not access_string:
    return False
  if access_string == 'public':
    return False
  return True


class VideoEntryToStringWrapper(googlecl.base.BaseEntryToStringWrapper):
  @property
  def author(self):
    """Author."""
    # Name of author 'x' name is in entry.author[x].name.text
    text_extractor = lambda entry: getattr(getattr(entry, 'name'), 'text')
    return self._join(self.entry.author, text_extractor=text_extractor)
  owner = author

  @property
  def minutes(self):
    """Length of the video, in minutes (MM:SS)."""
    minutes = int(self.seconds) / 60
    seconds = int(self.seconds) % 60
    return '%d:%#02d' % (minutes, seconds)
  time = minutes
  length = minutes
  duration = minutes

  @property
  def seconds(self):
    """Length of the video, in seconds."""
    return self.entry.media.duration.seconds

  @property
  def status(self):
    """Status of the video."""
    if self.entry.control:
      # Apparently the structure for video entries isn't fully fleshed out,
      # so use a regex on the xml.
      xml_string = self.xml
      reason_regex = r'<ns1:control .*? name="(\w+)" reasonCode="(\w+)"'
      match = re.search(reason_regex, xml_string)
      if match:
        return '%s (%s)' % (match.group(1), match.group(2))
    if self.entry.media.private:
      return 'private'
    if self.entry.racy:
      return 'racy'
    else:
      # Can't find a difference between public and unlisted videos, in the XML
      # or self.entry data structure...
      return 'public/unlisted'

  @property
  def tags(self):
    """Tags / keywords or labels."""
    tags_text = self.entry.media.keywords.text
    tags_text = tags_text.replace(', ', ',')
    tags_list = tags_text.split(',')
    return self.intra_property_delimiter.join(tags_list)
  labels = tags
  keywords = tags


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_list(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  entries = client.GetVideos(user=options.owner or 'default',
                             titles=titles_list)
  for vid in entries:
    print googlecl.base.compile_entry_string(VideoEntryToStringWrapper(vid),
                                             options.fields.split(','),
                                             delimiter=options.delimiter)


def _run_post(client, options, args):
  video_list = options.src + args
  is_private = _map_access_string(options.access)
  client.PostVideos(video_list, title=options.title, desc=options.summary,
                    tags=options.tags, category=options.category,
                    is_private=is_private)


def _run_tag(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  video_entries = client.GetVideos(titles=titles_list)
  if options.category:
    client.CategorizeVideos(video_entries, options.category)
  if options.tags:
    client.TagVideos(video_entries, options.tags)


def _run_delete(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  entries = client.GetVideos(titles=titles_list)
  client.DeleteEntryList(entries, 'video', options.prompt)


TASKS = {'post': googlecl.base.Task('Post a video.', callback=_run_post,
                                    required=['src', 'category', 'devkey'],
                                    optional=['title', 'summary', 'tags',
                                              'access']),
         'list': googlecl.base.Task('List videos by user.',
                                    callback=_run_list,
                                    required=['fields', 'delimiter'],
                                    optional=['title', 'owner']),
         'tag': googlecl.base.Task('Add tags to a video and/or ' +\
                                   'change its category.',
                                   callback=_run_tag,
                                   required=['title', ['tags', 'category'],
                                             'devkey']),
         'delete': googlecl.base.Task('Delete videos.', callback=_run_delete,
                                      required=['title', 'devkey'])}
