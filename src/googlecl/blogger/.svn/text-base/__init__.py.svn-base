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

service_name = __name__.split('.')[-1]
LOGGER_NAME = __name__
SECTION_HEADER = service_name.upper()


def _map_access_string(access_string):
  """Map an access string to a value Blogger will understand.

  In this case, Blogger only cares about "is draft" so 'public' gets mapped to
  False, everything else to True.

  Returns:
    Boolean indicating True (is a draft) or False (is not a draft).
  """
  if not access_string:
    return False
  if access_string == 'public':
    return False
  return True


class BloggerEntryToStringWrapper(googlecl.base.BaseEntryToStringWrapper):
  @property
  def access(self):
    """Access level (draft or public)."""
    if self.entry.control and self.entry.control.draft.text == 'yes':
      return 'draft'
    else:
      return 'public'

  @property
  def author(self):
    """Author."""
    # Name of author 'x' name is in entry.author[x].name.text
    text_extractor = lambda entry: getattr(getattr(entry, 'name'), 'text')
    return self._join(self.entry.author, text_extractor=text_extractor)

  @property
  def tags(self):
    return self.intra_property_delimiter.join(
                            [c.term for c in self.entry.category if c.term])
  labels = tags
#===============================================================================
# Each of the following _run_* functions execute a particular task.
#
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_post(client, options, args):
  content_list = options.src + args
  entry_list = client.UploadPosts(content_list,
                                  blog_title=options.blog,
                                  post_title=options.title,
                                  is_draft=_map_access_string(options.access))
  if options.tags:
    client.LabelPosts(entry_list, options.tags)


def _run_delete(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  post_entries = client.GetPosts(blog_title=options.blog,
                                 post_titles=titles_list)
  client.DeleteEntryList(post_entries, 'post', options.prompt)


def _run_list(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  entries = client.GetPosts(options.blog, titles_list,
                            user_id=options.owner or 'default')
  for entry in entries:
    print googlecl.base.compile_entry_string(
                                             BloggerEntryToStringWrapper(entry),
                                             options.fields.split(','),
                                             delimiter=options.delimiter)


def _run_tag(client, options, args):
  titles_list = googlecl.build_titles_list(options.title, args)
  entries = client.GetPosts(options.blog, titles_list)
  client.LabelPosts(entries, options.tags)


TASKS = {'delete': googlecl.base.Task('Delete a post.', callback=_run_delete,
                                      required=['blog', 'title']),
         'post': googlecl.base.Task('Post content.', callback=_run_post,
                                    required=['src', 'blog'],
                                    optional=['title', 'tags', 'access']),
         'list': googlecl.base.Task('List posts in a blog',
                                    callback=_run_list,
                                    required=['fields', 'blog', 'delimiter'],
                                    optional=['title', 'owner']),
         'tag': googlecl.base.Task('Label posts', callback=_run_tag,
                                   required=['blog', 'title', 'tags'])}
