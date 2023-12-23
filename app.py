import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, abort  
app = Flask(__name__) 
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn



@app.route('/')
def index():
    return render_template('index.html')



@app.route('/login/', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        nm = request.form['name']
        
        if not nm:
            flash('Name is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO USER (name) VALUES (?)',[nm])
            conn.commit()
            conn.close()
            return render_template('index.html')

    return render_template('login.html')

@app.route('/register/', methods=('GET',))
def register():
    if request.method == 'post':
        user = request.form['usernm']
        password1 = request.form['password']
    
        if not user:
            flash('Username required!')
        elif not password1:
            flash('Password reqired')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO DETAILS (usernm, password) VALUES (?,?)', [user],[password1])
            conn.commit()
            conn.close
            return render_template('index.html')
    return render_template('register.html')
if __name__ == '__main__': 
    app.run(debug=False) 
