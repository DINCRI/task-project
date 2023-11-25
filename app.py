import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect
  
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
        name = request.form['name']
        
        if not name:
            flash('Name is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO USER (name) VALUES (?)',(name))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('login.html')

  
if __name__ == '__main__': 
    app.run(debug=False) 
