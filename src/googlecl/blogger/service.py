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


"""Service details and instances for the Blogger service."""


from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import atom
import gdata
import gdata.blogger
import gdata.blogger.service
import logging
import os
from googlecl import safe_encode
import googlecl.base
import googlecl.service
from googlecl.blogger import SECTION_HEADER


LOG = logging.getLogger(googlecl.blogger.LOGGER_NAME)


class BloggerServiceCL(gdata.blogger.service.BloggerService,
                       googlecl.service.BaseServiceCL):

  """Command-line-friendly service for the Blogger API.

  Some of this is based off gdata/samples/blogger/BloggerExampleV1.py

  """

  def __init__(self, config):
    """Constructor."""
    gdata.blogger.service.BloggerService.__init__(self, account_type='GOOGLE')
    googlecl.service.BaseServiceCL.__init__(self, SECTION_HEADER, config)

  def _upload_content(self, post_title, content, blog_id=None, is_draft=False):
    """Uploads content.

    Keyword arguments:
      blog_title: Title of the blog to post to.
      title: Title to give the post.
      content: String to get posted. This may be contents from a file, but NOT
               the path itself!
      is_draft: If this content is a draft post or not. (Default False)

    Returns:
      Entry of post. (Returns same results as self.AddPost())
    """
    entry = gdata.blogger.BlogPostEntry()
    entry.title = atom.Title(title_type='xhtml', text=post_title)
    entry.content = atom.Content(content_type='html', text=content)
    if is_draft:
      control = atom.Control()
      control.draft = atom.Draft(text='yes')
      entry.control = control
    return self.AddPost(entry, blog_id)

  def _get_blog_id(self, blog_title=None, user_id='default'):
    """Return the blog ID of the blog that matches blog_title.

    Keyword arguments:
      blog_title: Name or title of the blog.
      user_id: Profile ID of blog's owner as seen in the profile view URL.
              Default 'default' for the authenticated user.

    Returns:
      Blog ID (blog_entry.GetSelfLink().href.split('/')[-1]) if a blog is
      found matching the user and blog_title. None otherwise.
    """
    blog_entry = self.GetSingleEntry('/feeds/' + user_id + '/blogs', blog_title)
    if blog_entry:
      return blog_entry.GetSelfLink().href.split('/')[-1]
    else:
      if blog_title is not None:
        LOG.error('Did not find a blog with title matching %s', blog_title)
      else:
        LOG.error('No blogs found!')
      return None

  def is_token_valid(self, test_uri='/feeds/default/blogs'):
    """Check that the token being used is valid."""
    return googlecl.service.BaseServiceCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid

  def get_posts(self, blog_title=None, post_titles=None, user_id='default'):
    """Get entries for posts that match a title.

    Keyword arguments:
      blog_title: Name or title of the blog the post is in. (Default None)
      post_titles: string or list Titles that the posts should have.
                   Default None, for all posts
      user_id: Profile ID of blog's owner as seen in the profile view URL.
              (Default 'default' for authenticated user)

    Returns:
      List of posts that match parameters, or [] if none do.
    """
    blog_id = self._get_blog_id(blog_title, user_id)
    if blog_id:
      uri = '/feeds/' + blog_id + '/posts/default'
      return self.GetEntries(uri, post_titles)
    else:
      return []

  GetPosts = get_posts

  def label_posts(self, post_entries, tags):
    """Add or remove labels on a list of posts.

    Keyword arguments:
      post_entries: List of post entry objects.
      tags: String representation of tags in a comma separated list.
            For how tags are generated from the string,
            see googlecl.base.generate_tag_sets().
    """
    scheme = 'http://www.blogger.com/atom/ns#'
    remove_set, add_set, replace_tags = googlecl.base.generate_tag_sets(tags)
    successes = []
    for post in post_entries:
      # No point removing tags if we're replacing all of them.
      if remove_set and not replace_tags:
        # Keep categories if they meet one of two criteria:
        # 1) Are of a different scheme than the one we're looking at, or
        # 2) Are of the same scheme, but the term is in the 'remove' set
        post.category = [c for c in post.category \
                          if c.scheme != scheme or \
                          (c.scheme == scheme and c.term not in remove_set)]

      if replace_tags:
        # Remove categories that match the scheme we are updating.
        post.category = [c for c in post.category if c.scheme != scheme]
      if add_set:
        new_tags = [atom.Category(term=tag, scheme=scheme) for tag in add_set]
        post.category.extend(new_tags)
      updated_post = self.UpdatePost(post)
      if updated_post:
        successes.append(updated_post)
    return successes

  LabelPosts = label_posts

  def upload_posts(self, content_list, blog_title=None, post_title=None,
                   is_draft=False):
    """Uploads posts.

    Args:
      content_list: List of filenames or content to upload.
      blog_title: Name of the blog to upload to.
      post_title: Name to give the post(s).
      is_draft: Set True to upload as private draft(s), False to make upload(s)
          public.

    Returns:
      List of entries of successful posts.
    """
    max_size = 500000
    entry_list = []
    blog_id = self._get_blog_id(blog_title)
    if not blog_id:
      return []
    for content_string in content_list:
      if os.path.exists(content_string):
        with open(content_string, 'r') as content_file:
          content = content_file.read(max_size)
          if content_file.read(1):
            LOG.warning('Only read first %s bytes of file %s' %
                        (max_size, content_string))
        if not post_title:
          title = os.path.basename(content_string).split('.')[0]
      else:
        if not post_title:
          title = 'New post'
        content = content_string
      try:
        entry = self._upload_content(post_title or title,
                                     content,
                                     blog_id=blog_id,
                                     is_draft=is_draft)
      except self.request_error, err:
        LOG.error(safe_encode('Failed to post: ' + unicode(err)))
      else:
        entry_list.append(entry)
        if entry.control and entry.control.draft.text == 'yes':
          html_link = _build_draft_html(entry)
        else:
          html_link = entry.GetHtmlLink().href
        LOG.info('Post created: %s', html_link)
    return entry_list

  UploadPosts = upload_posts


SERVICE_CLASS = BloggerServiceCL


def _build_draft_html(entry):
  template = 'http://www.blogger.com/post-edit.g?blogID=%s&postID=%s'
  return template % (entry.GetBlogId(), entry.GetPostId())
