#!/usr/bin/python
#
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

"""Tests for calendar dates."""

__author__ = 'thmiller@google.com (Tom Miller)'

import date
import unittest
from datetime import datetime
from datetime import timedelta


# If "now" changes, the ONE_DAY, edge, and trick tests
# below must be changed carefully!!
def static_now():
  return datetime(year=2010,
                  month=10,
                  day=22,
                  hour=14,
                  minute=5)


def static_today():
  return static_now().replace(hour=0,
                              minute=0,
                              second=0,
                              microsecond=0)

NOW = static_now()
YEAR = NOW.year
ONE_DAY = timedelta(hours=24)


MONTH_DAY_TESTS = {'1/1': datetime(year=YEAR+1, month=1, day=1),
                   '12/31': datetime(year=YEAR, month=12, day=31),
                   '10/30': datetime(year=YEAR, month=10, day=30),
                   '2/28': datetime(year=YEAR+1, month=2, day=28),
                   '11/1': datetime(year=YEAR, month=11, day=1)}

TIME_TESTS = {'7pm': NOW.replace(hour=19, minute=0),
              '8am': NOW.replace(hour=8, minute=0) + ONE_DAY,
              '01:00': NOW.replace(hour=1, minute=0) + ONE_DAY,
              '14:00': NOW.replace(hour=14, minute=0) + ONE_DAY}

AMBIGUOUS_TESTS = {'6': NOW.replace(hour=18, minute=0),
                   '7:01': NOW.replace(hour=7, minute=1) + ONE_DAY,
                   '4:59': NOW.replace(hour=16, minute=59)}

FULL_DATE_TESTS = {'7/15/2011': datetime(year=2011, month=7, day=15),
                   '4/30/2000': datetime(year=2000, month=4, day=30),
                   '2010-06-02': datetime(year=2010, month=6, day=2),
                   '2010-9-2': datetime(year=2010, month=9, day=2),
                   'March 30 2010': datetime(year=2010, month=3, day=30),
                   'Jan 1 1970': datetime(year=1970, month=1, day=1)}

JOINED_TESTS = {'06/15/11 at 6': datetime(year=2011, day=15, month=6, hour=18),
                '3/4@19:00': datetime(year=YEAR+1, day=4, month=3, hour=19),
                '10/22/2012 @ 12:53pm': datetime(year=2012, month=10, day=22,
                                                 hour=12, minute=53),
                'Aug 23 2020 at 5pm': datetime(year=2020, month=8, day=23,
                                               hour=17)}

EDGE_TESTS = {'10/22/2010 @ 14:05': NOW,
              '10/22 @ 14:04': NOW.replace(minute=4),
              '2:05pm': NOW,
              'tomorrow at 2:04': NOW.replace(minute=4) + ONE_DAY,
              '10/21 at 00:00': datetime(year=YEAR+1, month=10, day=21)}

TRICK_TESTS = {'today at 2': NOW.replace(minute=0),
               '10/22 at 2': NOW.replace(minute=0)}

DURATION_TESTS = {'+3': NOW + timedelta(hours=3),
                  '+1:20': NOW + timedelta(hours=1, minutes=20),
                  '+:45': NOW + timedelta(minutes=45)}

FAIL_TESTS = [',', '@', '115', 'notadate', '1-4']

RANGE_BASE_TEXT = '11/3 @ 9pm'
RANGE_EXPECTED_START = datetime(year=YEAR, month=11, day=3, hour=21)


class ParsingDatesTest(unittest.TestCase):
  def assertConvertedEqual(self, text, expected, actual):
    if expected != actual:
      self.fail('%s was not parsed correctly (%s != %s)'
                % (text, expected, actual))


class ParseSingleDateTest(ParsingDatesTest):

  def setUp(self):
    self.parser = date.DateParser(static_today, static_now)

  def runTestSet(self, test_dict):
    for text, expected_date in test_dict.items():
      parsed_date = self.parser.parse(text)
      self.assertConvertedEqual(text, expected_date, parsed_date.local)

  def testDatetimeParse(self):
    parsed_date = self.parser.parse('2010-01-20T13:45:00')
    self.assertEqual(datetime(year=2010, month=1, day=20, hour=13, minute=45),
                     parsed_date.local)

  def testMonthDayParsing(self):
    self.runTestSet(MONTH_DAY_TESTS)

  def testTimeParsing(self):
    self.runTestSet(TIME_TESTS)

  def testAmbiguous(self):
    self.runTestSet(AMBIGUOUS_TESTS)

  def testFullDateParsing(self):
    self.runTestSet(FULL_DATE_TESTS)

  def testJoined(self):
    self.runTestSet(JOINED_TESTS)

  def testEdge(self):
    self.runTestSet(EDGE_TESTS)

  def testTrick(self):
    self.runTestSet(TRICK_TESTS)

  def testDuration(self):
    self.runTestSet(DURATION_TESTS)

  def testFailures(self):
    for text in FAIL_TESTS:
      try:
        self.parser.parse(text)
      except date.ParsingError, err:
        pass
      else:
        self.fail('Expected ParsingError for %s' % text)


class ParseDateRange(ParsingDatesTest):

  def setUp(self):
    self.parser = date.DateRangeParser(static_today, static_now)

  def testSingleDate(self):
    date_range = self.parser.parse(RANGE_BASE_TEXT)
    self.assertConvertedEqual(RANGE_BASE_TEXT,
                              RANGE_EXPECTED_START,
                              date_range.start.local)
    self.assertEqual(date_range.end.local, RANGE_EXPECTED_START)
    self.assertFalse(date_range.specified_as_range)

  def testStartRange(self):
    text = RANGE_BASE_TEXT + ','
    date_range = self.parser.parse(text)
    self.assertConvertedEqual(text,
                              RANGE_EXPECTED_START,
                              date_range.start.local)
    self.assertEqual(date_range.end, None)
    self.assertTrue(date_range.specified_as_range)

  def testStartAndDurationRange(self):
    text = RANGE_BASE_TEXT + ',+5'
    date_range = self.parser.parse(text)
    self.assertConvertedEqual(RANGE_BASE_TEXT,
                              RANGE_EXPECTED_START,
                              date_range.start.local)
    self.assertEqual(date_range.end.local,
                     RANGE_EXPECTED_START + timedelta(hours=5))
    self.assertTrue(date_range.specified_as_range)

  def testAllDurationRange(self):
    text = '+2,+3'
    date_range = self.parser.parse(text)
    self.assertEqual(date_range.start.local,
                     NOW + timedelta(hours=2))
    self.assertEqual(date_range.end.local,
                     NOW + timedelta(hours=5))
    self.assertTrue(date_range.specified_as_range)

  def testEndDurationRange(self):
    text = ',+3'
    date_range = self.parser.parse(text)
    self.assertEqual(date_range.start, None)
    self.assertEqual(date_range.end.local,
                     NOW + timedelta(hours=3))
    self.assertTrue(date_range.specified_as_range)

  def testDurationStart(self):
    text = '+1' + ',' + RANGE_BASE_TEXT
    date_range = self.parser.parse(text)
    self.assertEqual(date_range.start.local, NOW + timedelta(hours=1))
    self.assertConvertedEqual(RANGE_BASE_TEXT,
                              RANGE_EXPECTED_START,
                              date_range.end.local)
    self.assertTrue(date_range.specified_as_range)

  def testStartEndRange(self):
    end_text = '11/29'
    text = RANGE_BASE_TEXT + ',' + end_text
    date_range = self.parser.parse(text)
    self.assertConvertedEqual(RANGE_BASE_TEXT,
                              RANGE_EXPECTED_START,
                              date_range.start.local)
    self.assertConvertedEqual(end_text,
                              datetime(year=YEAR, month=11, day=29),
                              date_range.end.local)
    self.assertTrue(date_range.specified_as_range)

  def testEndRange(self):
    text = ',' + RANGE_BASE_TEXT
    date_range = self.parser.parse(text)
    self.assertEqual(date_range.start, None)
    self.assertConvertedEqual(text,
                              RANGE_EXPECTED_START,
                              date_range.end.local)
    self.assertTrue(date_range.specified_as_range)


if __name__ == '__main__':
  unittest.main()
