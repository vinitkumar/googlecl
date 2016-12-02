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
"""Data for GoogleCL's calendar service."""
import datetime
import googlecl
import googlecl.base
import logging
import re
import time
from googlecl.calendar.date import DateRangeParser

service_name = __name__.split('.')[-1]
LOGGER_NAME = __name__
SECTION_HEADER = service_name.upper()

LOG = logging.getLogger(LOGGER_NAME)
# Rename to reduce verbosity
safe_encode = googlecl.safe_encode


def condense_recurring_events(events):
  seen_ids = []
  combined_events = []
  for event in events:
    print "looking at event %s" % event.title.text
    if event.original_event.id not in seen_ids:
      seen_ids.append(event.original_event.id)
      combined_events.append(event)
  return combined_events


def convert_reminder_string(reminder):
  """Convert reminder string to minutes integer.

  Keyword arguments:
    reminder: String representation of time,
              e.g. '10' for 10 minutes,
                   '1d' for one day,
                   '3h' for three hours, etc.
  Returns:
    Integer of reminder converted to minutes.

  Raises:
    ValueError if conversion failed.
  """
  if not reminder:
    return None
  unit = reminder.lower()[-1]
  value = reminder[:-1]
  if unit == 's':
    return int(value) / 60
  elif unit == 'm':
    return int(value)
  elif unit == 'h':
    return int(value) * 60
  elif unit == 'd':
    return int(value) * 60 * 24
  elif unit == 'w':
    return int(value) * 60 * 24 * 7
  else:
    return int(reminder)


def filter_recurring_events(events, recurrences_expanded):
  if recurrences_expanded:
    is_recurring = lambda event: event.original_event
  else:
    is_recurring = lambda event: event.recurrence
  return [e for e in events if not is_recurring(e)]


def filter_single_events(events, recurrences_expanded):
  if recurrences_expanded:
    is_single = lambda event: not event.original_event
  else:
    is_single = lambda event: not event.recurrence
  return [e for e in events if not is_single(e)]


def filter_all_day_events_outside_range(start_date, end_date, events):
  if start_date:
    if start_date.all_day:
      start_datetime = start_date.local
    else:
      start_datetime = datetime.datetime(year=start_date.local.year,
                                         month=start_date.local.month,
                                         day=start_date.local.day)
  if end_date:
    if end_date.all_day:
      inclusive_end_datetime = end_date.local + datetime.timedelta(hours=24)
    else:
      end_datetime = datetime.datetime(year=end_date.local.year,
                                       month=end_date.local.month,
                                       day=end_date.local.day)
  new_events = []
  for event in events:
    try:
      start = datetime.datetime.strptime(event.when[0].start_time, '%Y-%m-%d')
      end = datetime.datetime.strptime(event.when[0].end_time, '%Y-%m-%d')
    except ValueError, err:
      if str(err).find('unconverted data remains') == -1:
        raise err
      else:
        #Errors that complain of unconverted data are events with duration
        new_events.append(event)
    else:
      if ((not start_date or start >= start_datetime) and
          (not end_date or end <= inclusive_end_datetime)):
        new_events.append(event)
      elif event.recurrence:
        # While writing the below comment, I was 90% sure it was true. Testing
        # this case, however, showed that things worked out just fine -- the
        # events were filtered out. I must have misunderstood the "when" data.

        # The tricky case: an Event that describes a recurring all-day event.
        # In the rare case that:
        # NO recurrences occur in the given range AND AT LEAST ONE recurrence
        # occurs just outside the given range (AND it's an all-day recurrence),
        # we will incorrectly return this event.
        # This is unavoidable unless we a) perform another query or b)
        # incorporate a recurrence parser.
        new_events.append(event)

  return new_events


def filter_canceled_events(events, recurrences_expanded):
  AT_LEAST_ONE_EVENT = 'not dead yet!'
  canceled_recurring_events = {}
  ongoing_events = []
  is_canceled = lambda e: e.event_status.value == 'CANCELED' or not e.when

  for event in events:
    print 'looking at event %s' % event.title.text
    if recurrences_expanded:
      if event.original_event:
        print 'event is original: %s' % event.title.text
        try:
          status = canceled_recurring_events[event.original_event.id]
        except KeyError:
          status = None
        if is_canceled(event) and status != AT_LEAST_ONE_EVENT:
          print 'adding event to canceled: %s' % event.title.text
          canceled_recurring_events[event.original_event.id] = event
        if not is_canceled(event):
          print 'at least one more of: %s' % event.title.text
          canceled_recurring_events[event.original_event.id]= AT_LEAST_ONE_EVENT
      ongoing_events.append(event)
    # If recurrences have not been expanded, we can't tell if they were
    # canceled or not.
    if not is_canceled(event):
      ongoing_events.append(event)

  for event in canceled_recurring_events.values():
    if event != AT_LEAST_ONE_EVENT:
      ongoing_events.remove(event)

  return ongoing_events


def get_datetimes(cal_entry):
  """Get datetime objects for the start and end of the event specified by a
  calendar entry.

  Keyword arguments:
    cal_entry: A CalendarEventEntry.

  Returns:
    (start_time, end_time, freq) where
      start_time - datetime object of the start of the event.
      end_time - datetime object of the end of the event.
      freq - string that tells how often the event repeats (NoneType if the
           event does not repeat (does not have a gd:recurrence element)).

  """
  if cal_entry.recurrence:
    return parse_recurrence(cal_entry.recurrence.text)
  else:
    freq = None
    when = cal_entry.when[0]
    try:
      # Trim the string data from "when" to only include down to seconds
      start_time_data = time.strptime(when.start_time[:19],
                                      '%Y-%m-%dT%H:%M:%S')
      end_time_data = time.strptime(when.end_time[:19],
                                    '%Y-%m-%dT%H:%M:%S')
    except ValueError:
      # Try to handle date format for all-day events
      start_time_data = time.strptime(when.start_time, '%Y-%m-%d')
      end_time_data = time.strptime(when.end_time, '%Y-%m-%d')
  return (start_time_data, end_time_data, freq)


def parse_recurrence(time_string):
  """Parse recurrence data found in event entry.

  Keyword arguments:
    time_string: Value of entry's recurrence.text field.

  Returns:
    Tuple of (start_time, end_time, frequency). All values are in the user's
    current timezone (I hope). start_time and end_time are datetime objects,
    and frequency is a dictionary mapping RFC 2445 RRULE parameters to their
    values. (http://www.ietf.org/rfc/rfc2445.txt, section 4.3.10)

  """
  # Google calendars uses a pretty limited section of RFC 2445, and I'm
  # abusing that here. This will probably break if Google ever changes how
  # they handle recurrence, or how the recurrence string is built.
  data = time_string.split('\n')
  start_time_string = data[0].split(':')[-1]
  start_time = time.strptime(start_time_string,'%Y%m%dT%H%M%S')

  end_time_string = data[1].split(':')[-1]
  end_time = time.strptime(end_time_string,'%Y%m%dT%H%M%S')

  freq_string = data[2][6:]
  freq_properties = freq_string.split(';')
  freq = {}
  for prop in freq_properties:
    key, value = prop.split('=')
    freq[key] = value
  return (start_time, end_time, freq)


class CalendarEntryToStringWrapper(googlecl.base.BaseEntryToStringWrapper):
  def __init__(self, entry, config):
    """Initialize a CalendarEntry wrapper.

    Args:
      entry: CalendarEntry to interpret to strings.
      config: Configuration parser. Needed for some values.
    """
    googlecl.base.BaseEntryToStringWrapper.__init__(self, entry)
    self.config_parser = config

  @property
  def when(self):
    """When event takes place."""
    start_date, end_date, freq = get_datetimes(self.entry)
    print_format = self.config_parser.lazy_get(SECTION_HEADER,
                                                      'date_print_format')
    start_text = time.strftime(print_format, start_date)
    end_text = time.strftime(print_format, end_date)
    value = start_text + ' - ' + end_text
    if freq:
      if freq.has_key('BYDAY'):
        value += ' (' + freq['BYDAY'].lower() + ')'
      else:
        value += ' (' + freq['FREQ'].lower() + ')'
    return value

  @property
  def where(self):
    """Where event takes place"""
    return self._join(self.entry.where, text_attribute='value_string')


def _list(client, options, args):
  cal_user_list = client.get_calendar_user_list(options.cal)
  if not cal_user_list:
    LOG.error('No calendar matches "' + options.cal + '"')
    return
  titles_list = googlecl.build_titles_list(options.title, args)
  parser = DateRangeParser()
  date_range = parser.parse(options.date)
  for cal in cal_user_list:
    print ''
    print safe_encode('[' + unicode(cal) + ']')
    single_events = client.get_events(cal.user,
                                      start_date=date_range.start,
                                      end_date=date_range.end,
                                      titles=titles_list,
                                      query=options.query,
                                      split=False)

    for entry in single_events:
      print googlecl.base.compile_entry_string(
                            CalendarEntryToStringWrapper(entry, client.config),
                            options.fields.split(','),
                            delimiter=options.delimiter)


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
  # If no other search parameters are mentioned, set date to be
  # today. (Prevent user from retrieving all events ever)
  if not (options.title or args  or options.query or options.date):
    options.date = 'today,'
  _list(client, options, args)


def _run_list_today(client, options, args):
  options.date = 'today'
  _list(client, options, args)


def _run_add(client, options, args):
  cal_user_list = client.get_calendar_user_list(options.cal)
  if not cal_user_list:
    LOG.error('No calendar matches "' + options.cal + '"')
    return
  reminder_in_minutes = convert_reminder_string(options.reminder)
  events_list = options.src + args
  reminder_results = []
  for cal in cal_user_list:
    if options.date:
      results = client.full_add_event(events_list, cal.user, options.date,
                                      reminder_in_minutes)
    else:
      results = client.quick_add_event(events_list, cal.user)
      if reminder_in_minutes is not None:
        reminder_results = client.add_reminders(cal.user,
                                                results,
                                                reminder_in_minutes)
    if LOG.isEnabledFor(logging.DEBUG):
      for entry in results + reminder_results:
        LOG.debug('ID: %s, status: %s, reason: %s',
                  entry.batch_id.text,
                  entry.batch_status.code,
                  entry.batch_status.reason)
    for entry in results:
      LOG.info('Event created: %s' % entry.GetHtmlLink().href)


def _run_delete(client, options, args):
  cal_user_list = client.get_calendar_user_list(options.cal)
  if not cal_user_list:
    LOG.error('No calendar matches "' + options.cal + '"')
    return
  parser = DateRangeParser()
  date_range = parser.parse(options.date)

  titles_list = googlecl.build_titles_list(options.title, args)
  for cal in cal_user_list:
    single_events, recurring_events = client.get_events(cal.user,
                                                    start_date=date_range.start,
                                                    end_date=date_range.end,
                                                    titles=titles_list,
                                                    query=options.query,
                                                    expand_recurrence=True)
    if options.prompt:
      LOG.info(safe_encode('For calendar ' + unicode(cal)))
    if single_events:
      client.DeleteEntryList(single_events, 'event', options.prompt)
    if recurring_events:
      if date_range.specified_as_range:
        # if the user specified a date that was a range...
        client.delete_recurring_events(recurring_events, date_range.start,
                                       date_range.end, cal.user, options.prompt)
      else:
        client.delete_recurring_events(recurring_events, date_range.start,
                                       None, cal.user, options.prompt)
    if not (single_events or recurring_events):
      LOG.warning('No events found that match your options!')


TASKS = {'list': googlecl.base.Task('List events on a calendar',
                                    callback=_run_list,
                                    required=['fields', 'delimiter'],
                                    optional=['title', 'query',
                                              'date', 'cal']),
         'today': googlecl.base.Task('List events for the next 24 hours',
                                     callback=_run_list_today,
                                     required=['fields', 'delimiter'],
                                     optional=['title', 'query', 'cal']),
         'add': googlecl.base.Task('Add event to a calendar',
                                   callback=_run_add,
                                   required='src',
                                   optional='cal'),
         'delete': googlecl.base.Task('Delete event from a calendar',
                                      callback=_run_delete,
                                      required=[['title', 'query']],
                                      optional=['date', 'cal'])}
