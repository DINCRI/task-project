import sqlite3
import secrets
from pathlib import Path
from flask import Flask, session, redirect, url_for

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024
app.secret_key = secrets.token_hex(32)

def get_db_connection():
    conn = sqlite3.connect(app.config.get('DATABASE', str(Path(__file__).with_name('database.db'))))
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def local_profile():
    # Keep the existing planner owner when converting to a single local profile.
    conn = get_db_connection()
    try:
        with conn:
            conn.execute('CREATE TABLE IF NOT EXISTS PROGRAM (id INTEGER PRIMARY KEY, activities TEXT, time TEXT, day TEXT, user_id INTEGER)')
            conn.execute('CREATE TABLE IF NOT EXISTS LOCAL_PROFILE (id INTEGER PRIMARY KEY CHECK (id = 1), owner_id INTEGER NOT NULL)')
            profile = conn.execute('SELECT owner_id FROM LOCAL_PROFILE WHERE id = 1').fetchone()
            if profile is None:
                owner = session.get('user_id')
                if not isinstance(owner, int):
                    existing = conn.execute('SELECT user_id FROM PROGRAM WHERE user_id IS NOT NULL GROUP BY user_id ORDER BY COUNT(*) DESC, user_id LIMIT 1').fetchone()
                    owner = existing['user_id'] if existing else 1
                conn.execute('INSERT INTO LOCAL_PROFILE VALUES (1, ?)', (owner,))
            else:
                owner = profile['owner_id']
        session['user_id'] = owner
        session['usernm'] = 'Profil local'
    finally:
        conn.close()

# Old bookmarks open the planner directly.
@app.route('/login/', methods=['GET', 'POST'])
@app.route('/register/', methods=['GET', 'POST'])
@app.route('/logout/')
@app.route('/profile')
@app.route('/change_username', methods=['POST'])
def former_account_page():
    return redirect(url_for('index'))

from planner import install_planner
install_planner(app, get_db_connection)
from chat_ai import install_chat
install_chat(app, get_db_connection)

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=False)
