 Copyright (C) 2010 Google Inc.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
   
      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

Contents:
---------
1. Introduction
  1.1 Other files
  1.2 README style
2. Commands
  2.1 Services
    2.1.1 Blogger
    2.1.2 Calendar
    2.1.3 Contacts
    2.1.4 Docs
    2.1.5 Picasa
    2.1.6 YouTube
  2.2 The 'list' task
3. Options
  3.1 Tags
  3.2 Date

1. Introduction
Welcome to the README. If you're reading this after checking out the svn repository, this should have the most up-to-date information on the capabilities and usage of the code in svn HEAD. Otherwise, it should more or less match the Manual on the GoogleCL project wiki (http://code.google.com/p/googlecl/wiki/Manual)

If you have no idea what this project is or is about, poke around on our home page at http://code.google.com/p/googlecl.

1.1 Other files
For installation instructions, see INSTALL.txt

For help with the configuration file, see README.config

README.new-usage contains a crash-course in the usage changes from the previous version.

1.2 README style
Wiki markup is used occasionally in this document:
  * The '`' character marks example commands.
  * '*' denotes an entry in a list (such as this one).

2. Commands
Some terminology:
  * service - The Google service being used (Picasa, Blogger, etc.)
  * task - The task that the service will be doing (tag, post, delete, etc.)

You can also access help by typing `$ google help` or help on a specific service with `$ google help <service>`. For help with available options and what they mean, use `$ google --help`

2.1 Services
Each sub-section corresponds to a service, which lists the available tasks and some options commonly used with that service. Each task follows the format "task: description. `example`". Note that the `example` omits the initial `$ google <service>`

You can access a list of available tasks and their options with the "help" command as described above.

2.1.1 Blogger
Common options:
  * blog: If you have multiple blogs, you can indicate which one to use. The value you give here the is saved in your config file for future use, if your config file does not already contain an entry for "blog". See ConfigurationOptions.

Tasks:
  * delete: Delete posts. `delete --title "Silly post number [0-9]*"`
  * list: List posts. `list title,url-site`
  * post: Upload posts. `post --tags "GoogleCL, awesome" "Here's a really short post. The next posts will be much longer!" ~/blog/2010/may/*`
  * tag: Label posts `tag --title "Dev post" --tags "Python, software"`

Note: You can use `--owner` to specify another user's blog when listing posts, but you have to provide a Blogger ID (the number in http://www.blogger.com/profile/NUMBER), not the Google account name.

2.1.2 Calendar
Common options:
  * cal: Specify the name of the calendar. This can be a regular expression. If this option is not given, the primary calendar is used.
  * date: Specify a date, or date range. For the add task, this DISABLES the Quick Add text parsing feature, but allows you to specify when the event occurs. For listing and deleting events, `--date` will only return events that fall on or within the given date(s). Dates are inclusive, so `--date 2010-06-23,2010-06-25` will include the 23rd, 24th, and 25th of June 2010. See the detailed description of the `--date` option below.
  * reminder: (for add task only) Add a reminder to the events being added, one per default reminder type in your calendar settings. Default is in minutes, though you can say something like "2h" for one hour, "1d" for one day, etc.

Tasks:
  * add: Add event to calendar. `add "Dinner party with George tomorrow at 6pm" --reminder 1h`
  * delete: Delete an event. `delete --cal "GoogleCL dev cal" --title "Release.*"`
  * list: List events. `list --date 2010-06-01,2010-06-30`
  * today: List events for today only. `today`

*Note:* The add task uses the 'Quick Add' feature unless you specify `--date`. You you can read about Quick Add here: http://www.google.com/support/calendar/bin/answer.py?answer=36604#text
*Warning*: Because the add task uses 'Quick Add', it will not work for non-English calendars. See Issue 211. If you have a non-English calendar, use the `--date` option to add events to your calendar.

2.1.3 Contacts
Tasks:
  * add: Add contacts. `add "Jim Raynor, jimmy@noreaster.com" contacts.csv`
  * delete: Delete contacts. `delete --title Jerkface`
  * list: List contacts. `list name,email --title ".*bob.*" > the_bobs.csv`
  * add-groups: Add contact groups. `add-groups "Work" "Friends"`
  * delete-groups: Delete contact groups. `delete-groups "Friends"`
  * list-groups: List contact groups. `list-groups "my group"`

2.1.4 Docs
Common options:
  * format: Force docs to use the extension you provide.
  * folder: Specify a folder on Docs to search in or upload to.

Tasks:
  * delete: Delete docs. `delete --title "Evidence"`
  * edit: Edit or view a document. `edit --title "Shopping list" --editor vim`
  * get: Download docs. `get --title "Homework [0-9]*"`
  * list: List documents. `list title,url-direct --delimiter ": "`
  * upload: Upload documents. `upload the_bobs.csv ~/work/docs_to_share`

Note: Uploading arbitrary files is only possible for Apps Premier customers, using the --no-convert option. See the FAQ.

2.1.5 Picasa
Common options:
  * owner: Owner of the albums you want to deal with. This will work with all tasks but create and delete. For example, to download bob's album, add `--owner bob` to the "get" task. To post to your friend's album that she shared with you, add `--owner your_friend` to the "post" task.

Tasks:
  * create: Create an album. `create --title "Summer Vacation 2009" --tags Vermont ~/photos/vacation2009/*`
  * delete: Delete photos or albums. `delete --title "Stupid album"`
  * get: Download photos. `get --title "My Album" /path/to/download/folder`
  * list: List photos or albums. `list title,url-direct --query "A tag"`
  * post: Add photos to an album. `post --title "Summer Vacation 2008" ~/old_photos/*.jpg`
  * tag: Tag photos. `tag --title "Album I forgot to tag" --tags oops`

2.1.6 YouTube
Common options:
  * category: YouTube category to assign to the video. This is required, and a little tricky. Here's the mapping for YouTube categories to `--category` values (and capitalization counts!)
|| *YouTube category* || *Value for* `--category` ||
|| Autos & Vehicles || Autos ||
|| Comedy || Comedy ||
|| Education || Education ||
|| Entertainment || Entertainment ||
|| Film & Animation || Film ||
|| Gaming || Games ||
|| Howto & Style || Howto ||
|| Music || Music ||
|| News & Politics || News ||
|| Nonprofits & Activism || Nonprofit ||
|| People & Blogs || People ||
|| Pets & Animals || Animals ||
|| Science & Technology || Tech ||
|| Sports || Sports ||
|| Travel & Events || Travel ||

Tasks:
  * delete: Delete videos. `delete --title ".*"`
  * list: List your videos. `list`
  * post: Post a video. `post --category Education --devtags GoogleCL killer_robots.avi`
  * tag: Tag videos. `tag -n ".*robot.*" --tags robot`

2.2. The List task
The list task can be given additional arguments to specify what exactly is being listed. For example,

`$ google <service> list field1,field2,field3 --delimiter ": "`

will output those fields, in that order, with ": " as a delimiter. Valid values for `<`field1`>` etc. are dependent on the service being used.

Common (all services):

*Note:* These are enabled for all services, but the service may not have a definition for it. For example, Docs does not support summaries.
  * 'summary' - summary text. Includes Picasa captions.
  * 'title', 'name' - displayed title or name.
  * 'url' - treated as 'url-direct' or 'url-site' depending on setting in preferences file. See the note at the end of this section.
  * 'url-site' - url of the site associated with the resource.
  * 'url-direct' - url directly to the resource.
  * 'xml' - dump the XML representation of the result.

Blogger:
  * 'access' - access level of the post (either 'public' or 'draft')
  * 'author' - author of the post
  * 'tags', 'labels', - tags or labels on the post.

Calendar:
  * 'when' - when an event takes place.
  * 'where' - where the event takes place.

Contacts:
  * 'address', 'where' - postal addresses.
  * 'birthday', 'bday' - birthday.
  * 'email' - email address(es).
  * 'event', 'dates', 'when' - events such as birthdays, anniversaries, etc.
  * 'im' - instant messanger handles.
  * 'name' - full name.
  * 'nickname' - nickname.
  * 'notes' - notes on a contact.
  * 'organization', 'company' - company or organization.
  * 'phone_number', 'phone' - phone numbers.
  * 'relation' - names of relations, such as manager, spouse, etc.
  * 'title', 'org_title' - job title.
  * 'user_defined', 'other' - custom labels.
  * 'website', 'links' - websites and links.

Picasa:
  * Photos (picasa list)
  ** 'caption', 'summary' - photo caption
  ** 'distance' - distance between camera and target.
  ** 'ev' - exposure value.
  ** 'exposure' - exposure time.
  ** 'flash' - if flash was used.
  ** 'focallength'- focal length used.
  ** 'fstop' - focal length divided by "effective" aperture diameter (aka f-number, focal ratio, or relative aperture)
  ** 'imageUniqueID', 'id' - EXIF identifier assigned uniquely to each image.
  ** 'iso' - iso equivalent value used.
  ** 'make' - make of the camera used.
  ** 'model' - model of the camera used.
  ** 'tags' - tags on the photo.
  ** 'time', 'when' - time the photo was taken (as millisecond timestamp).
  ** 'url-download' - link directly to download an image.
  * Albums (picasa list-albums)
  ** 'access', 'visibility' - visibility setting on the album.
  ** 'location', 'where' - location text of the album properties.
  ** 'published', 'when' - when the album was uploaded

YouTube:
  * 'author', 'owner' - username of video uploader.
  * 'minutes', 'time', 'length', 'duration' - length of the video, in MM:SS format. (Note that if you specify ':' as a delimiter, it will be MM SS).
  * 'seconds' - length of the video in seconds.
  * 'status' - status of the video. This is still an uncertain feature.
  * 'tags' - tags on the video.

The difference between 'url-site' and 'url-direct' is best exemplified by a picasa photo: 'url-site' gives a link to the photo in the user's album, 'url-direct' gives a link to the image url. If 'url-direct' is specified but is not applicable, 'url-site' is placed in its stead, and vice-versa.

3. Options
GoogleCL will fill in options in what it hopes is a natural way. If you do not specify any options explicitly with `-<letter>` or `--<option>`, the program will suck in values from the command line to replace the missing required options. For example,
`$ google help contacts`
...
`list: List contacts`
`   Requires: fields AND title AND delimiter`

says that `--fields --title --delimiter` are all required. If you haven't changed your basic configuration, there should be a line under the config header `[CONTACTS]` that says `fields = name,email`, so that required option is fulfilled. (Note that there is a `fields` entry under `[GENERAL]` so you never need to supply a value for `fields`, and shouldn't, unless you specify it with `--fields=<my new fields>`)

Next up is `title`, so if you issue the contacts list command with any free-floating arguments, the first one will be set to `title`.

Finally, `delimiter` is always set to "," by default, so that's satisfied as well.

This means that

`$ google contacts list Huey Dewey Louie`
`$ google contacts list Huey Dewey Louie --fields name,email`
`$ google contacts list --fields name,email --title Huey Dewey Louie`

all give the same output.

Some tasks have a conditional requirement, such as (title OR query). In this case, `title` is filled first, and GoogleCL assumes you do not want to specify a query. Of course, if you filled `query` explicitly and not `title`, `title` is not filled in with any command line arguments.

Here are some more details on the trickier options you can specify.

3.1 Tags
The tags option will let you both add and remove tags / labels. Here are some examples:
  * 'tag1, tag2, tag3': Add tag1, tag2, and tag3 to the item's tags
  * '-tag1, tag4': Remove tag1, add tag4
  * '-- tag5': Remove all tags, then add tag5

3.2 Date
The behavior given here is applicable to the calendar service.

  * '[datetime]': Specify date/time.
  * '[datetime],': On and after given date/time.
  * '[starting datetime],[ending datetime]': Between the two dates/times, inclusive
  * ',[datetime]': On or before date/time.

The contents of [datetime] can follow several formats. You can specify a date with any of the following:

  * today/tomorrow
  * YYYY-M-D ("2010-9-25")
  * M/D[/YY or /YYYY] (e.g. "9/2", "9/2/10", "9/2/2010")
  * Month/mo. D [YYYY] (e.g. "January 1", "Feb 20", "Dec 31 1999")

You can specify a time in most typical formats:

  * hour [am or pm] (e.g. "3pm", but NOT just "23")
  * hour:minute [am or pm] (e.g. "10:30am" "11:45", "23:00")

  but note that if you specify a time without specifying am or pm, it will be converted the same way Google Calendar Quick Add does. 1-6 are interpreted as "pm", 7-12 are "am". So "6" will be interpreted as "18:00".

Finally, you can combine a date and time with "at" or "@"

  * 11/3 @ 5:30pm
  * Feb 5 at 16:00
  * tomorrow @ 3:33am

In case those weren't enough options for you, you can specify an offset by prefixing a number with "+", which is interpreted based on where it appears in the date expression. Appearing by itself, it translates to an offset from the current time. After a datetime and comma, it translates to an offset from the previous datetime.

  * '+3': A time of "three hours from now"
  * '1/1/11 at 4pm,+2': A range of "1/1/11 at 4pm" to "1/1/11 at 6pm"
  * '+4,+1': A range of "four hours from now" to "five hours from now"

See the example scripts for examples on how to use this option.

*Note:* the calendar delete task will interpret 'datetime,' and ',datetime' identically.

*Note:* picasa create will only accept the "date" portion of possibilities for `--date`
