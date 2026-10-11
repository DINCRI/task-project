import unittest, tempfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as application
class WeekPersistenceTests(unittest.TestCase):
 def test_reopening_keeps_selected_week_and_entries(self):
  with tempfile.TemporaryDirectory() as tmp:
   application.app.config.update(TESTING=True,DATABASE=tmp+'/test.db')
   client=application.app.test_client();client.get('/')
   client.post('/activities',data=dict(week='2026-10-12',activities='Activitate păstrată',time='08:00',day='Monday',kind='activity',category='Personal',duration='60'))
   client.get('/?week=2026-10-12')
   # New session simulates reopening after the server invalidates cookies.
   reopened=application.app.test_client()
   result=reopened.get('/')
   self.assertIn('Activitate păstrată',result.text)
   self.assertIn('12.10 – 18.10.2026',result.text)
   with application.get_db_connection() as conn:
    self.assertEqual(conn.execute('SELECT COUNT(*) FROM PROGRAM').fetchone()[0],1)
