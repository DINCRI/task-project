import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect ,session



app = Flask(__name__) 
app.secret_key = "super secret key"
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/register/', methods=('GET','POST'))
def register():
    if request.method == 'POST':
        user = request.form['usernm']
        password1 = request.form['password']
    
        if not user:
            flash('Username required!')
        elif not password1:
            flash('Password reqired')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO DETAILS (usernm, password) VALUES (?,?)', [user,password1])
            conn.commit()
            conn.close
            return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login/', methods=('GET','POST'))
def login():
    if request.method == 'POST':
        user = request.form['usernm']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM DETAILS WHERE usernm = ? AND password = ?', (user, password))
        user_data = cursor.fetchone()

        if user_data:
            
            session['user_id'] = user_data['id']
            session['usernm'] = user_data['usernm']
            conn.close()
            return redirect(url_for('index'))
        else:
           
            flash('Invalid username or password')

    return render_template('login.html')


@app.route('/')
def index():
    if 'user_id' in session and 'usernm' in session:
        user_id = session['user_id']
        username = session['usernm']


        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM PROGRAM WHERE user_id = ?', (user_id,))
        user_programs = cursor.fetchall()
        conn.close()

        return render_template('index.html', username=username, user_programs=user_programs)
    else:
        return redirect(url_for('login'))
    

@app.route('/activities', methods=('POST','GET'))
def activities():
    if request.method == 'POST':
        act = request.form['activities']
        tm = request.form['time']
        day = request.form['day']
        
        user_id =session.get('user_id')

    
        if not act:
            flash('required!')
        elif not tm:
            flash('required')
        else:

            conn = get_db_connection()
            conn.execute('INSERT INTO PROGRAM (activities, time, day, user_id) VALUES (?,?,?,?)', [act,tm,day,user_id])
            conn.commit()
            conn.close
            return redirect(url_for('index'))
        
    return render_template('activities.index')

@app.route('/delete_activity', methods=['POST'])
def delete_activity():
    if request.method == 'POST':
        activity_id = request.form['activity_id']
        
        conn = get_db_connection()
        conn.execute('DELETE FROM PROGRAM WHERE id = ?', (activity_id,))
        conn.commit()
        conn.close()
        
        flash('Activity removed successfully!')
        return redirect(url_for('index'))



@app.route('/logout/')
def logout():
    
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/about')
def about():
   username = session['usernm']
   return render_template('about.html', username=username)

@app.route('/calendar/')
def calendar():
    username = session['usernm']
    return render_template('calendar.html', username=username)

if __name__ == '__main__': 
    app.run(debug=False) 
