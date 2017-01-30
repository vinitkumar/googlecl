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


"""Service details and instances for the Picasa service.

Some use cases:
Add event:
  calendar add "Lunch with Tony on Tuesday at 12:00"

List events for today:
  calendar today

"""
__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import gdata.calendar.service
import googlecl.base
import googlecl.service
import logging
import urllib
from googlecl import safe_encode, safe_decode
from googlecl.calendar import SECTION_HEADER
from googlecl.calendar.date import DateRangeParser


LOG = logging.getLogger(googlecl.calendar.LOGGER_NAME)
USER_BATCH_URL_FORMAT = \
               gdata.calendar.service.DEFAULT_BATCH_URL.replace('default', '%s')


class CalendarError(googlecl.base.Error):
  """Base error for Calendar errors."""
  pass

class EventsNotFound(CalendarError):
  """No events matching given parameters were found."""
  pass


class Calendar():

  """Wrapper class for some calendar entry data."""

  def __init__(self, cal_entry=None, user=None, name=None):
    """Parse a CalendarEntry into "user" and human-readable names,
       or take them directly."""
    if cal_entry:
      # Non-primary calendar feeds look like this:
      # http:blah/.../feeds/JUNK%40group.calendar.google.com/private/full
      # So grab the part after /feeds/ and unquote it.
      self.user = urllib.unquote(cal_entry.content.src.split('/')[-3])
      self.name = safe_decode(cal_entry.title.text)
    else:
      self.user = user
      self.name = name

  def __str__(self):
    return self.name


class CalendarServiceCL(gdata.calendar.service.CalendarService,
                        googlecl.service.BaseServiceCL):

  """Extends gdata.calendar.service.CalendarService for the command line.

  This class adds some features focused on using Calendar via an installed
  app with a command line interface.

  """

  def __init__(self, config):
    """Constructor."""
    gdata.calendar.service.CalendarService.__init__(self)
    googlecl.service.BaseServiceCL.__init__(self, SECTION_HEADER, config)

  def _batch_delete_recur(self, event, cal_user,
                          start_date=None, end_date=None):
    """Delete a subset of instances of recurring events."""
    request_feed = gdata.calendar.CalendarEventFeed()
    # Don't need to decode event.title.text here because it's not being
    # displayed to the user. Totally internal.
    _, recurring_events = self.get_events(cal_user, start_date=start_date,
                                          end_date=end_date,
                                          titles=event.title.text,
                                          expand_recurrence=True)

    delete_events = [e for e in recurring_events if e.original_event and
                     e.original_event.id == event.original_event.id]
    if not delete_events:
      raise EventsNotFound
    map(request_feed.AddDelete, [None], delete_events, [None])
    self.ExecuteBatch(request_feed, USER_BATCH_URL_FORMAT % cal_user)

  def add_reminders(self, calendar_user, events, minutes):
    """Add default reminders to events.

    Keyword arguments:
      calendar_user: "User" of the calendar.
      events: List of events to add reminder to.
      minutes: Number of minutes before each event to send reminder.

    Returns:
      List of events with batch results.

    """
    request_feed = gdata.calendar.CalendarEventFeed()
    for event in events:
      if event.when:
        for a_when in event.when:
          a_when.reminder.append(gdata.calendar.Reminder(minutes=minutes))
      else:
        LOG.debug('No "when" data for event!')
        event.when.append(gdata.calendar.When())
        event.when[0].reminder.append(gdata.calendar.Reminder(minutes=minutes))
      request_feed.AddUpdate(entry=event)
    response_feed = self.ExecuteBatch(request_feed,
                                      USER_BATCH_URL_FORMAT % calendar_user)
    return response_feed.entry

  AddReminders = add_reminders

  def delete_recurring_events(self, events, start_date, end_date, cal_user,
                              prompt):
    """Delete recurring events from a calendar.

    Keyword arguments:
      events: List of non-expanded calendar events to delete.
      start_date: Date specifying the start of events (inclusive).
      end_date: Date specifying the end of events (inclusive). None for no end
          date.
      cal_user: "User" of the calendar to delete events from.
      prompt: True if we should prompt before deleting events, False otherwise.

    """
    # option_list is a list of tuples, (prompt_string, deletion_instruction)
    # prompt_string gets displayed to the user,
    # deletion_instruction is a special value that will let the program know
    #   what to do.
    #     'ALL' -- delete all events in the series.
    #     'NONE' -- don't delete anything.
    #     'TWIXT' -- delete events between start_date and end_date.
    #     'ON' -- delete events on the single date given.
    #     'ONAFTER' -- delete events on and after the date given.
    deletion_choice = 'ALL'
    option_list = [('All events in this series', deletion_choice)]
    if start_date and end_date:
      deletion_choice = 'TWIXT'
      option_list.append(('Instances between %s and %s' %
                          (start_date, end_date), deletion_choice))
    elif start_date or end_date:
      delete_date = (start_date or end_date)
      option_list.append(('Instances on %s' % delete_date, 'ON'))
      option_list.append(('All events on and after %s' % delete_date,
                          'ONAFTER'))
      deletion_choice = 'ON'
    option_list.append(('Do not delete', 'NONE'))
    prompt_str = ''
    for i, option in enumerate(option_list):
      prompt_str += str(i) + ') ' + option[0] + '\n'
    # Condense events so that the user isn't prompted for the same event
    # multiple times. This is assuming that recurring events have been expanded.
    events = googlecl.calendar.condense_recurring_events(events)
    for event in events:
      if prompt:
        delete_selection = -1
        while delete_selection < 0 or delete_selection > len(option_list)-1:
          msg = 'Delete "%s"?\n%s' %\
                (safe_decode(event.title.text), prompt_str)
          try:
            delete_selection = int(raw_input(safe_encode(msg)))
          except ValueError:
            continue
        deletion_choice = option_list[delete_selection][1]

      # deletion_choice has either been picked by the prompt, or is the default
      # value. The default value is determined by the date info passed in,
      # and should be the "least destructive" option.
      if deletion_choice == 'ALL':
        self._delete_original_event(event, cal_user)
      elif deletion_choice == 'TWIXT':
        self._batch_delete_recur(event, cal_user,
                                 start_date=start_date,
                                 end_date=end_date)
      elif deletion_choice == 'ON':
        self._batch_delete_recur(event, cal_user,
                                 start_date=delete_date,
                                 end_date=delete_date)
      elif deletion_choice == 'ONAFTER':
        self._batch_delete_recur(event, cal_user,
                                 start_date=delete_date)
      elif deletion_choice != 'NONE':
        raise CalendarError('Got unexpected batch deletion command!')

  DeleteRecurringEvents = delete_recurring_events

  def _delete_original_event(self, expanded_event, cal_user):
    """Deletes the original event corresponding to an expanded recurrence.

    Args:
      expanded_event: Expanded recurrence. Should contain the "original_event"
          attribute.
      cal_user: Calendar user, used to retrieve events.
    """
    _, recurring_events = self.get_events(cal_user,
                                          query=expanded_event.title.text,
                                          expand_recurrence=False)
    for event in recurring_events:
      if event.id.text.split('/')[-1] == expanded_event.original_event.id:
        LOG.debug('Matched on event %s, deleting without prompt' %
                  event.title.text)
        self.Delete(event.GetEditLink().href)

  def full_add_event(self, titles, calendar_user, date, reminder):
    """Create an event piece by piece (no quick add).

    Args:
      titles: List of titles of events.
      calendar_user: "User" of the calendar to add to.
      date: Text representation of a date and/or time.
      reminder: Number of minutes before event to send reminder. Set to 0 for no
          reminder.

    Returns:
      Response entries from batch-inserting the events.
    """

    import atom
    request_feed = gdata.calendar.CalendarEventFeed()
#    start_text, _, end_text = googlecl.calendar.date.split_string(date, [','])
    parser = DateRangeParser()
    date_range = parser.parse(date)
    start_time, end_time = date_range.to_when()
    for title in titles:
      event = gdata.calendar.CalendarEventEntry()
      event.title = atom.Title(text=title)
      when = gdata.calendar.When(start_time=start_time,
                                 end_time=end_time)
      if reminder:
        when.reminder.append(gdata.calendar.Reminder(minutes=reminder))
      event.when.append(when)
      request_feed.AddInsert(event, 'insert-' + title[0:5])
    response_feed = self.ExecuteBatch(request_feed,
                                      USER_BATCH_URL_FORMAT % calendar_user)
    return response_feed.entry

  def quick_add_event(self, quick_add_strings, calendar_user):
    """Add an event using the Calendar Quick Add feature.

    Keyword arguments:
      quick_add_strings: List of strings to be parsed by the Calendar service,
                         as if it was entered via the "Quick Add" function.
      calendar_user: "User" of the calendar to add to.

    Returns:
      The event that was added, or None if the event was not added.

    """
    import atom
    request_feed = gdata.calendar.CalendarEventFeed()
    for i, event_str in enumerate(quick_add_strings):
      event = gdata.calendar.CalendarEventEntry()
      event.content = atom.Content(text=event_str)
      event.quick_add = gdata.calendar.QuickAdd(value='true')
      request_feed.AddInsert(event, 'insert-' + event_str[0:5] + str(i))
    response_feed = self.ExecuteBatch(request_feed,
                                      USER_BATCH_URL_FORMAT % calendar_user)
    return response_feed.entry

  QuickAddEvent = quick_add_event

  def get_calendar_user_list(self, cal_name=None):
    """Get "user" name and human-readable name for one or more calendars.

    The "user" for a calendar is an awful misnomer for the ID for the calendar.
    To get events for a calendar, you can form a query with
      cal_list = self.get_calendar_user_list('my calendar name')
      if cal_list:
        query = gdata.calendar.CalendarEventQuery(user=cal_list[0].user)

    Keyword arguments:
      cal_name: Name of the calendar to match. Default None to return the
                an instance representing only the default / main calendar.

    Returns:
      A list of Calendar instances, or None of there were no matches
      for cal_name.

    """
    if not cal_name:
      return [Calendar(user='default', name=self.email)]
    else:
      cal_list = self.GetEntries('/calendar/feeds/default/allcalendars/full',
                                 cal_name,
                          converter=gdata.calendar.CalendarListFeedFromString)
      if cal_list:
        return [Calendar(cal) for cal in cal_list]
    return None

  GetCalendarUserList = get_calendar_user_list

  def get_events(self, calendar_user, start_date=None, end_date=None,
                 titles=None, query=None, expand_recurrence=True, split=True):
    """Get events.

    Keyword arguments:
      calendar_user: "user" of the calendar to get events for.
                     See get_calendar_user_list.
      start_date: Start date of the event(s). Default None.
      end_date: End date of the event(s). Default None.
      titles: string or list Title(s) to look for in the event, supporting
              regular expressions. Default None for any title.
      query: Query string (not encoded) for doing full-text searches on event
             titles and content.
      expand_recurrence: If true, expand recurring events per the 'singleevents'
                         query parameter. Otherwise, don't.
      split: Split events into "one-time" and "recurring" events.

    Returns:
      List of events from calendar that match the given params.
    """
    query = gdata.calendar.service.CalendarEventQuery(user=calendar_user,
                                                      text_query=query)
    if start_date:
      query.start_min = start_date.to_query()
    if end_date:
      # End dates are naturally exclusive, so make it inclusive.
      query.start_max = end_date.to_inclusive_query()
    if expand_recurrence:
      query.singleevents = 'true'
    query.orderby = 'starttime'
    query.sortorder = 'ascend'
    events = self.GetEntries(query.ToUri(), titles,
                           converter=gdata.calendar.CalendarEventFeedFromString)

    if split:
      single_events = googlecl.calendar.filter_recurring_events(events,
                                                              expand_recurrence)
      recurring_events = googlecl.calendar.filter_single_events(events,
                                                              expand_recurrence)
      if start_date or end_date:
        # Because of how the "when" info on all-day events is stored, we need to
        # do a filter step to remove all-day events on the edge of the date
        # range.
        single_events = \
            googlecl.calendar.filter_all_day_events_outside_range(start_date,
                                                                  end_date,
                                                                  single_events)
        recurring_events = \
            googlecl.calendar.filter_all_day_events_outside_range(start_date,
                                                                  end_date,
                                                               recurring_events)
      return single_events, recurring_events
    else:
      if start_date or end_date:
        return googlecl.calendar.filter_all_day_events_outside_range(start_date,
                                                                     end_date,
                                                                     events)
      else:
        return events

  GetEvents = get_events

  def is_token_valid(self, test_uri='/calendar/feeds/default/private/full'):
    """Check that the token being used is valid."""
    return googlecl.service.BaseServiceCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid


SERVICE_CLASS = CalendarServiceCL
