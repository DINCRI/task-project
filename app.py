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
        return render_template('index.html', username=username)
    else:
    
        return redirect(url_for('login'))
    

@app.route('/activities', methods=('POST','GET'))
def activities():
    if request.method == 'POST':
        act = request.form['activites']
        tm = request.form['time']
    
        if not act:
            flash('required!')
        elif not tm:
            flash('required')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO PROGRAM (activities, time) VALUES (?,?)', [act,tm])
            conn.commit()
            conn.close
            return redirect(url_for('index'))
    return render_template('activities.index')


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
