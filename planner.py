from datetime import date, timedelta
import re
import secrets
from flask import request, session, redirect, url_for, render_template, flash

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
LABELS = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică']
CATEGORY_LABELS = {'Învățare': '📚 Școală și învățare', 'Mișcare': '🏃 Sport și mișcare', 'Hobby': '🎨 Pasiuni și hobby-uri', 'Relaxare': '🌿 Pauze și relaxare', 'Personal': '📅 Treburi și viață personală'}
CATEGORY_HELP = {'Învățare': 'Ore la școală, teme, cursuri sau studiu.', 'Mișcare': 'Sală, alergare, plimbări sau alte sporturi.', 'Hobby': 'Muzică, desen, gătit sau jocuri.', 'Relaxare': 'Odihnă, filme, citit de plăcere sau meditație.', 'Personal': 'Cumpărături, curățenie, întâlniri sau alte treburi.'}
CATEGORIES = ['Învățare', 'Mișcare', 'Hobby', 'Relaxare', 'Personal']
IDEAS = [('Învățare', 'Lucrează la un mini-proiect de programare', 45), ('Mișcare', 'O plimbare în aer liber', 30), ('Hobby', 'Încearcă o rețetă nouă', 60), ('Relaxare', 'Citește câteva pagini fără telefon', 20), ('Personal', 'Pregătește obiectivele săptămânii următoare', 15)]

KINDS = {'activity': 'Activitate', 'school': '🏫 Școală', 'test': '📝 Test', 'homework': '📚 Temă', 'project': '💻 Proiect'}

EMOJIS = '🏫 ✨ 💻 📚 📝 🎓 🧠 🗣️ 🏃 🚶 🏋️ 🚴 🧘 🏊 ⚽ 🎨 🎸 🎵 📷 🍳 🌱 🎮 🧩 🎬 ☕ 🌿 😴 🛁 🧹 🛒 📅 💼 💧 🍎 🤝 🐾 ✈️ ❤️ 🎯'.split()

def week_of(value=None):
    try:
        day = date.fromisoformat(value or '')
    except ValueError:
        day = date.today()
    return day - timedelta(days=day.weekday())

def install_planner(app, db):
    def schema():
        with db() as conn:
            columns = {r['name'] for r in conn.execute('PRAGMA table_info(PROGRAM)')}
            for name, definition in [('week', "TEXT NOT NULL DEFAULT ''"), ('completed', 'INTEGER NOT NULL DEFAULT 0'), ('category', "TEXT NOT NULL DEFAULT 'Personal'"), ('duration', 'INTEGER NOT NULL DEFAULT 30'), ('emoji', "TEXT NOT NULL DEFAULT '✨'"), ('recurring', 'INTEGER NOT NULL DEFAULT 0'), ('kind', "TEXT NOT NULL DEFAULT 'activity'"), ('subject', "TEXT NOT NULL DEFAULT ''"), ('notes', "TEXT NOT NULL DEFAULT ''")]:
                if name not in columns:
                    conn.execute(f'ALTER TABLE PROGRAM ADD COLUMN {name} {definition}')
            profile_columns = {r['name'] for r in conn.execute('PRAGMA table_info(LOCAL_PROFILE)')}
            if 'selected_week' not in profile_columns:
                conn.execute('ALTER TABLE LOCAL_PROFILE ADD COLUMN selected_week TEXT')
            conn.execute('CREATE TABLE IF NOT EXISTS WEEK_COMPLETION (activity_id INTEGER NOT NULL, week TEXT NOT NULL, PRIMARY KEY (activity_id, week))')
            conn.execute("UPDATE PROGRAM SET week = ? WHERE week = ''", (week_of().isoformat(),))

    def index():
        schema()
        if 'chat_token' not in session:
            session['chat_token'] = secrets.token_urlsafe(32)
        from chat_ai import settings
        with db() as conn:
            saved = conn.execute('SELECT selected_week FROM LOCAL_PROFILE WHERE id=1').fetchone()
            selected = request.args.get('week') or (saved['selected_week'] if saved else None)
            if not selected:
                current = week_of().isoformat()
                upcoming = conn.execute('SELECT MIN(week) AS week FROM PROGRAM WHERE user_id=? AND week>=?', (session['user_id'], current)).fetchone()
                selected = upcoming['week'] if upcoming and upcoming['week'] else current
            week = week_of(selected)
            conn.execute('UPDATE LOCAL_PROFILE SET selected_week=? WHERE id=1', (week.isoformat(),))
        with db() as conn:
            rows = [dict(r) for r in conn.execute('SELECT * FROM PROGRAM WHERE user_id = ? AND (week = ? OR (recurring = 1 AND week <= ?)) ORDER BY time, id', (session['user_id'], week.isoformat(), week.isoformat())).fetchall()]
            completed = {r['activity_id'] for r in conn.execute('SELECT activity_id FROM WEEK_COMPLETION WHERE week = ?', (week.isoformat(),))}
            for row in rows:
                end_minutes = int(row['time'][:2])*60 + int(row['time'][3:]) + row['duration']
                row['end_time'] = f'{end_minutes//60%24:02d}:{end_minutes%60:02d}'
                if row['recurring']:
                    row['completed'] = int(row['id'] in completed)
        from school_calendar import visible
        rows = [r for r in rows if visible(r, week, DAYS)]
        done = sum(r['completed'] for r in rows)
        interest = request.args.get('interest', '')
        return render_template('index.html', username=session.get('usernm', ''), chat_ready=bool(settings()[0]), chat_token=session['chat_token'], user_programs=rows,
            days=list(zip(DAYS, LABELS, [week+timedelta(days=i) for i in range(7)])), week=week.isoformat(),
            week_label=f'{week:%d.%m} – {week+timedelta(days=6):%d.%m.%Y}', previous=(week-timedelta(days=7)).isoformat(),
            following=(week+timedelta(days=7)).isoformat(), today=date.today(), categories=CATEGORIES, kinds=KINDS, category_labels=CATEGORY_LABELS, category_help=CATEGORY_HELP, emojis=EMOJIS,
            suggestions=[s for s in IDEAS if not interest or s[0] == interest], interest=interest,
            done=done, total=len(rows), progress=round(done/len(rows)*100) if rows else 0)

    def activities():
        if request.method != 'POST':
            return redirect(url_for('index'))
        schema()
        week = week_of(request.form.get('week')).isoformat()
        title = request.form.get('activities', '').strip()
        time = request.form.get('time', '')
        day = request.form.get('day', '')
        kind = request.form.get('kind', 'activity')
        subject = request.form.get('subject', '').strip()
        notes = request.form.get('notes', '').strip()
        recurring = request.form.get('recurring') == 'weekly' and kind in ('activity', 'school')
        if kind in ('test', 'homework', 'project'):
            try:
                event_date = date.fromisoformat(request.form.get('event_date', ''))
                week = week_of(event_date.isoformat()).isoformat()
                day = DAYS[event_date.weekday()]
            except ValueError:
                flash('Alege o dată validă pentru test sau termenul de predare.')
                return redirect(url_for('index', week=week))
        selected_days = list(dict.fromkeys([day] + (request.form.getlist('repeat_days') if recurring else [])))
        category = 'Învățare' if kind != 'activity' else request.form.get('category', 'Personal')
        emoji = request.form.get('emoji', '✨')
        if emoji not in EMOJIS:
            emoji = '✨'
        try:
            duration = int(request.form.get('duration', 30))
        except ValueError:
            duration = 0
        if kind == 'school':
            end_time = request.form.get('end_time', '')
            if re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', time) and re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', end_time):
                duration = (int(end_time[:2])*60 + int(end_time[3:])) - (int(time[:2])*60 + int(time[3:]))
            else:
                duration = 0
        if kind not in KINDS or len(subject) > 80 or len(notes) > 1000 or (kind in ('test', 'homework', 'project') and not subject) or not title or len(title) > 160 or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', time) or any(d not in DAYS for d in selected_days) or category not in CATEGORIES or not 5 <= duration <= 480:
            flash('Verifică activitatea, ora și durata (5–480 minute).')
        else:
            with db() as conn:
                for chosen_day in selected_days:
                    conn.execute('INSERT INTO PROGRAM (activities, time, day, user_id, week, category, duration, emoji, recurring, kind, subject, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (title, time, chosen_day, session['user_id'], week, category, duration, emoji, int(recurring), kind, subject, notes))
        return redirect(url_for('index', week=week))

    def delete_activity():
        schema()
        with db() as conn:
            conn.execute('DELETE FROM WEEK_COMPLETION WHERE activity_id IN (SELECT id FROM PROGRAM WHERE id = ? AND user_id = ?)', (request.form.get('activity_id'), session['user_id']))
            conn.execute('DELETE FROM PROGRAM WHERE id = ? AND user_id = ?', (request.form.get('activity_id'), session['user_id']))
        return redirect(url_for('index', week=week_of(request.form.get('week')).isoformat()))

    def complete_activity():
        schema()
        with db() as conn:
            row = conn.execute('SELECT * FROM PROGRAM WHERE id = ? AND user_id = ?', (request.form.get('activity_id'), session['user_id'])).fetchone()
            week = week_of(request.form.get('week')).isoformat()
            if row and row['recurring'] and row['week'] <= week:
                done = conn.execute('SELECT 1 FROM WEEK_COMPLETION WHERE activity_id = ? AND week = ?', (row['id'], week)).fetchone()
                if done:
                    conn.execute('DELETE FROM WEEK_COMPLETION WHERE activity_id = ? AND week = ?', (row['id'], week))
                else:
                    conn.execute('INSERT INTO WEEK_COMPLETION VALUES (?, ?)', (row['id'], week))
            elif row and row['week'] == week:
                conn.execute('UPDATE PROGRAM SET completed = 1 - completed WHERE id = ?', (row['id'],))
        return redirect(url_for('index', week=week_of(request.form.get('week')).isoformat()))

    app.add_url_rule('/', view_func=index)
    app.add_url_rule('/activities', view_func=activities, methods=['POST'])
    app.add_url_rule('/delete_activity', view_func=delete_activity, methods=['POST'])
    app.add_url_rule('/complete_activity', view_func=complete_activity, methods=['POST'])
