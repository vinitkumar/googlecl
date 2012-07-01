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

"""Classes and functions for manipulating strings into dates.

Some parts are specific to Google Calendar."""

__author__ = 'thmiller@google.com (Tom Miller)'
import datetime
import re
import googlecl.base
import time
import logging

LOG = logging.getLogger("date.py")
QUERY_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'

ACCEPTED_DAY_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
ACCEPTED_DAY_FORMATS = ['%Y-%m-%d',
                        '%m/%d',
                        '%m/%d/%Y',
                        '%m/%d/%y',
                        '%b %d',
                        '%B %d',
                        '%b %d %Y',
                        '%B %d %Y']
ACCEPTED_TIME_FORMATS = ['%I%p',
                         '%I %p',
                         '%I:%M%p',
                         '%I:%M %p',
                         '%H:%M']
# Regular expression for strings that specify a time that could be afternoon or
# morning. First group will be the hour, second the minutes.
AMBIGUOUS_TIME_REGEX = '((?:1[0-2])|(?:[1-9]))?(?::([0-9]{2}))?$'

_DAY_TIME_TOKENIZERS = ['@', ' at ']
_RANGE_TOKENIZERS = [',']


class Error(Exception):
  """Base error for this module."""
  pass


class ParsingError(Error):
  """Failed to parse a token."""
  def __init__(self, token):
    self.token = token

  def __str__(self):
    return 'Failed to parse "%s"' % self.token


def datetime_today():
  """Creates a datetime object with zeroed-out time parameters."""
  return datetime.datetime.now().replace(hour=0,
                                         minute=0,
                                         second=0,
                                         microsecond=0)


def determine_duration(duration_token):
  """Determines a duration from a non-time token.

  Args:
    duration_token: String of hours and minutes.

  Returns:
    Timedelta object representing positive offset of hours and minutes.
  """
  hour, minute = parse_ambiguous_time(duration_token)
  if not (hour or minute):
    LOG.error('Duration must be in form of [hours][:minutes]')
    return None
  return datetime.timedelta(hours=hour, minutes=minute)


def get_utc_timedelta():
  """Return the UTC offset of local zone at present time as a timedelta."""
  if time.localtime().tm_isdst and time.daylight:
    return datetime.timedelta(hours=time.altzone/3600)
  else:
    return datetime.timedelta(hours=time.timezone/3600)


def parse_ambiguous_time(time_token):
  """Parses an ambiguous time into an hour and minute value.

  Args:
    time_token: Ambiguous time to be parsed. "Ambiguous" means it could be
        before noon or after noon. For example, "5:30" or "12".

  Returns:
    Tuple of (hour, minute). The hour is still not on a 24 hour clock.
  """
  ambiguous_time = re.match(AMBIGUOUS_TIME_REGEX, time_token)
  if not ambiguous_time:
    return None, None

  hour_text = ambiguous_time.group(1)
  minute_text = ambiguous_time.group(2)
  if hour_text:
    hour = int(hour_text)
  else:
    hour = 0
  if minute_text:
    minute = int(minute_text)
  else:
    minute = 0
  return hour, minute


def split_string(string, tokenizers=None):
  """Splits a string based on a list of potential substrings.

  Strings will only be split once, if at all. That is, at most two tokens can be
  returned, even if a tokenizer is found in multiple positions. The left-most
  tokenizer will be used to split.

  Args:
    string: String to split.
    tokenizers: List of strings that should act as a point to split around.
        Default None to use range tokenizers defined in this module.

  Returns:
    Tuple of (left_token, [True|False], right_token). The middle element is True
    if a tokenizer was found in the provided string, and is False otherwise.
  """
  if not string:
    return ('', False, '')
  if not tokenizers:
    tokenizers = _RANGE_TOKENIZERS
  for tokenizer in tokenizers:
    if string.find(tokenizer) != -1:
      left_token, _, right_token = string.partition(tokenizer)
      return (left_token.strip(), True, right_token.strip())
  return (string.strip(), False, '')


class Date(object):
  def __init__(self, local_datetime=None, utc_datetime=None, all_day=False):
    """Initializes the object.

    The datetime objects passed in are treated as naive -- no timezone info will
    be read from them.

    Args:
      local_datetime: A datetime object that specifies the date and time in the
          local timezone. Default None to set off utc_datetime.
      utc_datetime: Datetime object that specifies date and time in Coordinated
          Universal Time (UTC). Default None to set off local_datetime.
      all_day: Set True to indicate this Date is associated with an all day, or
          "time-less" date. Default False.

    Raises:
      Error: local_datetime and utc_datetime are both left undefined.
    """
    if not (local_datetime or utc_datetime):
      raise Error('Need to provide a local or UTC datetime')
    if local_datetime:
      self.local = local_datetime
      if not utc_datetime:
        self.utc = self.local + get_utc_timedelta()
    if utc_datetime:
      self.utc = utc_datetime
      if not local_datetime:
        self.local = self.utc - get_utc_timedelta()
    self.all_day = all_day

  def __add__(self, other):
    """Returns a Date with other added to its time."""
    return Date(utc_datetime=(self.utc + other), all_day=self.all_day)

  def __sub__(self, other):
    """Returns a Date with other subtracted from its time."""
    return Date(utc_datetime=(self.utc - other), all_day=self.all_day)

  def __str__(self):
    """Formats local datetime info into human-friendly string."""
    basic_string_format = '%m/%d/%Y'
    if self.all_day:
      return self.local.strftime(basic_string_format)
    else:
      return self.local.strftime(basic_string_format + ' %H:%M')

  def to_format(self, format_string):
    """Converts UTC data to specific format string."""
    return self.utc.strftime(format_string)

  def to_inclusive_query(self):
    """Converts UTC data to query-friendly, date-inclusive string.

    Note: This behavior is specific to Google Calendar.
    """
    if self.all_day:
      # If it's an all-day date, we need to boost the time by a day to make it
      # inclusive.
      new_datetime = self.utc + datetime.timedelta(hours=24)
    else:
      # The smallest unit Calendar appears to concern itself with
      # is minutes, so add a minute to make it inclusive.
      new_datetime = self.utc + datetime.timedelta(minutes=1)
    return new_datetime.strftime(QUERY_DATE_FORMAT)

  def to_query(self):
    """Converts UTC data to a query-friendly string."""
    return self.to_format(QUERY_DATE_FORMAT)

  def to_timestamp(self):
    """Converts UTC data to timestamp in seconds.

    Returns:
      Seconds since the epoch as a float.
    """
    return time.mktime(time.strptime(self.utc.strftime(format_string),
                                     '%Y-%m-%dT%H:%M'))

  def to_when(self):
    """Returns datetime info formatted to Google Calendar "when" style."""
    if self.all_day:
      # All day events must leave off hour data.
      return self.to_format('%Y-%m-%d')
    else:
      # Otherwise, treated like a query string.
      return self.to_query()


class DateParser(object):
  """Produces Date objects given data."""

  def __init__(self, today=None, now=None):
    """Initializes the DateParser object.

    Args:
      today: Function capable of giving the current local date. Default None to
          use datetime_today
      now: Function capable of giving the current local time. Default None to
          use datetime.datetime.now
    """
    if today is None:
      today = datetime_today
    if now is None:
      now = datetime.datetime.now
    self.today = today
    self.now = now

  def parse(self, text, base=None, shift_dates=True):
    """Parses text into a Date object.

    Args:
      text: String representation of one date, or an offset from a date. Will be
          interpreted as local time, unless "UTC" appears somewhere in the text.
      base: Starting point for this Date. Used if the text represents an hour,
          or an offset.
      shift_dates: If the date is earlier than self.today(), and the year is not
          specified, shift it to the future. True by default.
          Set to False if you want to set a day in the past without referencing
          the year. For example, today is 10/25/2010. Parsing "10/24" with
          shift_dates=True will return a date of 10/24/2011. If
          shift_dates=False, will return a date of 10/24/2010.

    Returns:
      Date object.

    Raises:
      ParsingError: Given text could not be parsed.
    """
    local_datetime = None
    day = None
    all_day = False
    try:
      # Unlikely anyone uses this, but if so, it's done in one shot
      all_info = datetime.datetime.strptime(text, ACCEPTED_DAY_TIME_FORMAT)
    except ValueError:
      pass
    else:
      return Date(local_datetime=all_info, all_day=False)

    day_token, _, time_token = split_string(text, _DAY_TIME_TOKENIZERS)
    if not (day_token or time_token):
      raise ParsingError(text)

    past_time_to_tomorrow = False
    if day_token:
      day = self.determine_day(day_token, shift_dates)
      if day is None:
        # If we couldn't figure out the day...
        # ...Calendar will shift times that already happened to tomorrow
        past_time_to_tomorrow = True
        # ...Maybe the day_token is actually a time_token
        time_token = day_token
        if base:
          # ... and we'll use the starting point passed in.
          day = base
      else:
        # If there's no time token, we're parsing an all day date.
        all_day = not bool(time_token)

    if time_token:
      if time_token.startswith('+'):
        delta = determine_duration(time_token.lstrip('+'))
        if delta and not day:
          # Durations go off of right now.
          day = self.now()
      else:
        time_offset = self.determine_time(time_token)
        if time_offset is None:
          delta = None
        else:
          if past_time_to_tomorrow and self._time_has_passed(time_offset):
            delta = datetime.timedelta(hours=time_offset.hour + 24,
                                       minutes=time_offset.minute)
          else:
            delta = datetime.timedelta(hours=time_offset.hour,
                                       minutes=time_offset.minute)
          if not day:
            # Hour/minutes (i.e. not durations) go off of the date.
            day = self.today()
      if delta is not None:
        local_datetime = day + delta
    else:
      local_datetime = day

    if local_datetime:
      return Date(local_datetime=local_datetime, all_day=all_day)
    else:
      raise ParsingError(text)

  def _day_has_passed(self, date):
    """"Checks to see if date has passed.

    Args:
      date: Datetime object to compare to today.

    Returns:
      True if date is earlier than today, False otherwise.
    """
    today = self.today()
    return (date.month < today.month or
            (date.month == today.month and date.day < today.day))

  def determine_day(self, day_token, shift_dates):
    """Parses day token into a date.

    Args:
      day_token: String to be interpreted as a year, month, and day.
      shift_dates: Indicates if past dates should be shifted to next year. Set
          True to move the date to next year if the date has already occurred
          this year, False otherwise.

    Returns:
      Datetime object with year, month, and day fields filled in if the
      day_token could be parsed. Otherwise, None.
    """
    if day_token == 'tomorrow':
      return self.today() + datetime.timedelta(hours=24)
    elif day_token == 'today':
      return self.today()
    else:
      date, valid_format = self._extract_time(day_token, ACCEPTED_DAY_FORMATS)
      if not date:
        LOG.debug('%s did not match any expected day formats' % day_token)
        return None
      # If the year was not explicitly mentioned...
      # (strptime will set a default year of 1900)
      if valid_format.lower().find('%y') == -1:
        if self._day_has_passed(date) and shift_dates:
          date = date.replace(year=self.today().year + 1)
        else:
          date = date.replace(year=self.today().year)
      return date

  def determine_time(self, time_token):
    """Parses time token into a time.

    Note: ambiguous times like "6" are converted according to how Google
    Calendar interprets them. So "1" - "6" are converted to 13-18 on a 24 hour
    clock.

    Args:
      time_token: String to be interpreted as an hour and minute.

    Returns:
      Time object with hour and minute fields filled in if the
      time_token could be parsed. Otherwise, None.
    """
    hour, minute = parse_ambiguous_time(time_token)
    if (hour or minute):
      # The ambiguous hours arranged in order, according to Google Calendar:
      # 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6
      if 1 <= hour and hour <= 6:
        hour += 12
    else:
      tmp, _ = self._extract_time(time_token, ACCEPTED_TIME_FORMATS)
      if not tmp:
        LOG.debug('%s did not match any expected time formats')
        return None
      hour = tmp.hour
      minute = tmp.minute
    return datetime.time(hour=hour, minute=minute)

  def _extract_time(self, time_string, possible_formats):
    """Returns date data contained in a string.

    Args:
      time_string: String representing a date and/or time.
      possible_formats: List of possible formats "time" may be in.

    Returns:
      Tuple of (datetime, format) with the datetime object populated by data
      found in "time" according to the returned format, or (None, None)
      if no formats matched.
    """
    for time_format in possible_formats:
      try:
        date = datetime.datetime.strptime(time_string, time_format)
      except ValueError, err:
        continue
      else:
        return date, time_format
    return None, None

  def _time_has_passed(self, time_container):
    """Checks if time has already passed the current time.

    Args:
      time_container: Object with hour and minute fields.

    Returns:
      True if the given time has passed, False otherwise.
    """
    now = self.now()
    return (time_container.hour < now.hour or
            (time_container.hour == now.hour and
             time_container.minute < now.minute))


class DateRange(object):
  """Holds info on a range of dates entered by the user."""
  def __init__(self, start, end, is_range):
    """Initializes the object.

    Args:
      start: Start of the range.
      end: End of the range.
      is_range: Set True if the user specified this range as a range, False if
          it was interpreted as a range.
    """
    self.start = start
    self.end = end
    self.specified_as_range = is_range

  def to_when(self):
    """Returns Google Calendar friendly text for "when" attribute.

    Raises:
      Error: starting point or ending point are not defined.
    """
    if not self.start or not self.end:
      raise Error('Cannot convert range of dates without start and end points.')
    else:
      start = self.start
    if not self.specified_as_range:
      # If only a start date was given...
      if self.start.all_day:
        end = self.start + datetime.timedelta(hours=24)
      else:
        end = self.start + datetime.timedelta(hours=1)
    else:
      end = self.end
    return start.to_when(), end.to_when()


class DateRangeParser(object):
  """Parser that treats strings as ranges."""

  def __init__(self, today=None, now=None, range_tokenizers=None):
    """Initializes the object.

    Args:
      today: Callback that returns the date.
      now: Callback that returns the date and time.
      range_tokenizers: List of strings that will be used to split date strings
          into tokens. Default None to use module default.
    """
    self.date_parser = DateParser(today, now)
    if range_tokenizers is None:
      range_tokenizers = _RANGE_TOKENIZERS
    self.range_tokenizers = range_tokenizers

  def parse(self, date_string, shift_dates=False):
    """"Parses a string into a start and end date.

    Note: This is Google Calendar specific. If date_string does not contain a
    range tokenizer, it will be treated as the starting date of a one day range.

    Args:
      date_string: String to parse.
      shift_dates: Whether or not to shift a date to next year if it has
          occurred earlier than today. See documentation for DateParser. Default
          False.

    Returns:
      Tuple of (start_date, end_date), representing start and end dates of the
      range. Either may be None, in which case it is an open range (i.e. from
      start until the distant future, or from the distant past until the end
      date.) If date_string is empty or None, this will be (None, None).
    """
    start_date = None
    end_date = None
    start_text, is_range, end_text = split_string(date_string,
                                                  self.range_tokenizers)
    if start_text:
      start_date = self.date_parser.parse(start_text, shift_dates=shift_dates)

    if end_text:
      if start_date:
        base = start_date.local
      else:
        base = None
      end_date = self.date_parser.parse(end_text, base=base,
                                        shift_dates=shift_dates)
    elif not is_range:
      # If no range tokenizer was given, the end date is effectively the day
      # after the given date.
      end_date = start_date
    return DateRange(start_date, end_date, is_range)
