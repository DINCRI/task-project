import sys
import io
import json
import tempfile
import unittest
from datetime import date
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as application
import chat_ai
from chat_planning import plan_message


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        application.app.config.update(TESTING=True, DATABASE=self.tmp.name + '/test.db')
        self.today = patch('chat_ai.today_local', return_value=date(2026, 10, 11))
        self.today.start()
        self.client = application.app.test_client()
        self.client.get('/?week=2026-09-07')
        with self.client.session_transaction() as state:
            self.token = state['chat_token']

    def tearDown(self):
        self.today.stop()
        self.tmp.cleanup()

    def post(self, message, request_id=''):
        return self.client.post('/chat', json={'message': message, 'request_id': request_id, 'week': '2026-09-07'}, headers={'X-Chat-Token': self.token})

    def rows(self):
        with application.get_db_connection() as conn:
            return conn.execute('SELECT * FROM PROGRAM').fetchall()

    def test_range_saved_directly_once(self):
        result = self.post('Mâine am de la 8-9 istorie', 'same').json
        self.assertTrue(result['changed'])
        self.assertEqual(result['week'], '2026-10-12')
        self.assertIn('08:00–09:00', result['reply'])
        self.assertIn('Ai teme', result['reply'])
        self.post('Mâine am de la 8-9 istorie', 'same')
        self.post('Mâine am de la 8-9 istorie', 'another')
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['activities'], 'Istorie')
        self.assertEqual(rows[0]['duration'], 60)
        self.assertEqual(rows[0]['kind'], 'school')

    def test_followup_and_history_survive_new_session(self):
        self.post('Mâine am istorie')
        second = application.app.test_client()
        second.get('/')
        self.client = second
        with second.session_transaction() as state:
            self.token = state['chat_token']
        self.assertEqual(len(second.get('/chat/history').json['messages']), 2)
        result = self.post('de la 8:30 la 9:45').json
        self.assertTrue(result['changed'])
        self.assertEqual(self.rows()[0]['duration'], 75)
        self.assertEqual(len(second.get('/chat/history').json['messages']), 4)
        self.post('Am matematică de la 10 la 11')
        self.assertEqual(self.rows()[1]['week'], '2026-10-12')

    def test_repeated_event_updates_duration(self):
        self.post('Mâine am istorie la 8')
        self.post('Mâine am istorie de la 8 la 9')
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.rows()[0]['duration'], 60)

    def test_bad_intervals_do_not_write(self):
        self.assertNotIn('changed', self.post('Mâine am istorie de la 9 la 8').json)
        self.assertNotIn('changed', self.post('Mâine am istorie la 99:99').json)
        self.assertEqual(len(self.rows()), 0)
        self.assertEqual(self.client.post('/chat', json={'message': 'Mâine am sport la 9'}).status_code, 403)

    def test_questions_do_not_write(self):
        self.assertIsNone(plan_message('Cum învăț pentru istorie?', None, date(2026, 10, 11)))
        self.assertIsNone(plan_message('Am nevoie de ajutor cu istoria', None, date(2026, 10, 11)))

    def test_model_uses_persisted_conversation_and_schedule(self):
        self.post('Mâine am istorie de la 8 la 9')
        seen = []
        def answer(req, timeout):
            seen.append(json.loads(req.data))
            return io.BytesIO(json.dumps({'message': {'content': 'Putem recapitula în sesiuni scurte. Ce capitole ai de pregătit?'}}).encode())
        with patch('chat_ai.http.urlopen', side_effect=answer):
            result = self.post('Cum mă pregătesc pentru test?')
            self.assertEqual(result.status_code, 200)
            self.client.get('/')
            self.post('Primul Război Mondial')
        self.assertIn('08:00', seen[0]['messages'][0]['content'])
        self.assertIn('2026-10-12', seen[0]['messages'][0]['content'])
        self.assertTrue(any('Ce capitole' in message['content'] for message in seen[1]['messages']))
        self.assertEqual(len(self.rows()), 1)

    def test_clear_preserves_events(self):
        self.post('Mâine am fotbal de la 17 la 18')
        result = self.client.post('/chat/clear', headers={'X-Chat-Token': self.token})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.client.get('/chat/history').json['messages'], [])
        self.assertEqual(len(self.rows()), 1)


if __name__ == '__main__':
    unittest.main()
