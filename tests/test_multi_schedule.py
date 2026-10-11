import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as application
from chat_extraction import validate

MESSAGE = 'hei salut imi poti pune ca am scoala luni si vineri de la 8 la 15 si miercuri joi si marti de la 8 la 14'


def result():
    return {'question': '', 'events': [
        dict(title='Școală', days=['luni', 'vineri'], date=None, start='08:00', end='15:00', duration=None, recurring=True),
        dict(title='Școală', days=['miercuri', 'joi', 'marti'], date=None, start='08:00', end='14:00', duration=None, recurring=True),
    ]}


class MultiScheduleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        application.app.config.update(TESTING=True, DATABASE=self.tmp.name + '/test.db')
        self.client = application.app.test_client()
        self.client.get('/')
        with self.client.session_transaction() as session:
            self.token = session['chat_token']

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_message_creates_five_recurring_entries_without_duplicates(self):
        extracted = validate(result(), MESSAGE, date(2026, 10, 11))
        with patch('chat_ai.extract', return_value=extracted):
            for identifier in ['first', 'first', 'repeated']:
                response = self.client.post('/chat', json={'message': MESSAGE, 'request_id': identifier}, headers={'X-Chat-Token': self.token})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json['changed'])
        with application.get_db_connection() as conn:
            rows = conn.execute('SELECT day,time,duration,recurring FROM PROGRAM').fetchall()
        actual = {row['day']: (row['time'], row['duration'], row['recurring']) for row in rows}
        self.assertEqual(len(rows), 5)
        self.assertEqual(actual, {
            'Monday': ('08:00', 420, 1), 'Friday': ('08:00', 420, 1),
            'Tuesday': ('08:00', 360, 1), 'Wednesday': ('08:00', 360, 1), 'Thursday': ('08:00', 360, 1),
        })

    def test_omitted_day_and_swapped_ranges_are_rejected(self):
        incomplete = result()
        incomplete['events'][1]['days'].remove('marti')
        with self.assertRaises(ValueError):
            validate(incomplete, MESSAGE, date(2026, 10, 11))
        swapped = result()
        swapped['events'][0]['end'] = '14:00'
        swapped['events'][1]['end'] = '15:00'
        with self.assertRaises(ValueError):
            validate(swapped, MESSAGE, date(2026, 10, 11))

    def test_validation_failure_writes_nothing(self):
        with patch('chat_ai.extract', side_effect=ValueError('Care este intervalul corect?')):
            response = self.client.post('/chat', json={'message': MESSAGE}, headers={'X-Chat-Token': self.token})
        self.assertNotIn('changed', response.json)
        with application.get_db_connection() as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM PROGRAM').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
