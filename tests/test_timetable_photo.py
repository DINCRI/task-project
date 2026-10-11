import unittest
from datetime import date
from school_calendar import school_day
from timetable_photo import validate
class TimetableTests(unittest.TestCase):
 def test_calendar(self):
  self.assertTrue(school_day(date(2026,10,12)))
  for value in ['2026-10-26','2026-12-01','2027-03-03','2027-06-01','2027-06-19']:
   self.assertFalse(school_day(date.fromisoformat(value)))
 def test_deduplication_and_overlap(self):
  row=dict(day='Monday',title='Matematică',start='08:00',end='09:00')
  self.assertEqual(len(validate(dict(question='',lessons=[row,row]))),1)
  with self.assertRaises(ValueError): validate(dict(question='',lessons=[row,dict(row,title='Istorie',start='08:30')]))
 def test_clarification_prevents_import(self):
  with self.assertRaises(ValueError): validate(dict(question='Care sunt orele?',lessons=[]))
