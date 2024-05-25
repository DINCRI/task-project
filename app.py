import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect ,session
import re
import nltk
from nltk.chat.util import Chat, reflections


app = Flask(__name__) 
app.secret_key = "super secret key"
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def verifica_parola(parola):
    if len(parola) < 6 or len(parola) > 20:
        return False
    if not re.search("[A-Z]",parola):
        return False
    if not re.search("[0-9]",parola):
        return False
    return True

def verifica_email(email):
    if len(email) < 6 :
        return False
    if not re.search("@",email):
        return False
    return True
    

@app.route('/register/', methods=('GET','POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        user = request.form['usernm']
        password1 = request.form['password']
        password2 = request.form['confirm_password']  

        if not user:
            flash('Username required!')
        elif not email:
            flash('Email is required')
        elif not verifica_email(email):
            flash('That email is invalid')
        elif not password1:
            flash('Password required')
        elif not verifica_parola(password1):
            flash('Password must be between 6 and 20 characters, contain at least one uppercase letter, and at least one number.')
        elif password1 != password2:
            flash('Passwords do not match!')
        else:
            conn = get_db_connection()
            cursor = conn.execute('SELECT * FROM DETAILS WHERE usernm = ? OR email = ?', (user, email))
            existing_user = cursor.fetchone()

            if existing_user:
                if existing_user['usernm'] == user:
                    flash('Username already exists!')
                if existing_user['email'] == email:
                    flash('Email already exists!')
            else:
                conn.execute('INSERT INTO DETAILS (usernm, password, email) VALUES (?, ?, ?)', (user, password1, email))
                conn.commit()
                conn.close()
                flash('Registration successful!')
                return redirect(url_for('index'))

    return render_template('register.html')



@app.route('/login/', methods=('GET','POST'))
def login():
    if request.method == 'POST':
        user_input = request.form['usernm']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        
        cursor.execute('SELECT * FROM DETAILS WHERE usernm = ? OR email = ?', (user_input, user_input))
        user_data = cursor.fetchone()

        if user_data and user_data['password'] == password:
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
    

@app.route('/activities', methods=('POST', 'GET'))
def activities():
    if request.method == 'POST':
        act = request.form['activities']
        tm = request.form['time']
        day = request.form['day']
        
        user_id = session.get('user_id')

        if not act:
            flash('Activity is required!')
        elif not tm:
            flash('Time is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO PROGRAM (activities, time, day, user_id) VALUES (?,?,?,?)', [act, tm, day, user_id])
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        
    return render_template('index.html')  


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
    if 'user_id' in session and 'usernm' in session:
        session.clear()
        flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/change_username', methods=['POST'])
def change_username():
     if request.method == 'POST':
        newuser = request.form['usernm']
        user_id = session['user_id']  

        conn = get_db_connection()
        conn.execute('UPDATE DETAILS SET usernm = ? WHERE id = ?', (newuser, user_id))  
        conn.commit()
        conn.close()
        session['usernm']=newuser
        flash('Username changed successfully!')
        return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    if 'user_id' in session and 'usernm' in session:
        user_id = session['user_id']
        username = session['usernm']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM DETAILS WHERE id = ?', (user_id,))
        user_email = cursor.fetchone()['email']
        conn.close()

        return render_template('profile.html', username=username, email=user_email)
    else:
        return redirect(url_for('login'))
    
#nltk

reflections = {
    "i am"       : "you are",
    "i was"      : "you were",
    "i"          : "you",
    "i'm"        : "you are",
    "i'd"        : "you would",
    "i've"       : "you have",
    "i'll"       : "you will",
    "my"         : "your",
    "you are"    : "I am",
    "you were"   : "I was",
    "you've"     : "I have",
    "you'll"     : "I will",
    "your"       : "my",
    "yours"      : "mine",
    "you"        : "me",
    "me"         : "you"
}

pairs = [
    [
        r"my name is (.*)",
        ["Hello %1, How are you today ?", "Nice to meet you %1!"]
    ],
    [
        r"how are you ?",
        ["I'm just an AI assistant, but thank you for asking.", "I'm here to help. How can I assist you?"]
    ],
    [
        r"what do you do ?",
        ["I'm a chatbot designed to answer your questions and assist you.", "Feel free to ask me anything!"]
    ],
    [
        r"i'm (.*)",
        ["Hi %1, How are you feeling today ?", "Nice to meet you %1!"]
    ],
    [
        r"quit",
        ["Bye Bye!! Take Care.", "See you later, have a nice day."]
    ],
    [
        r"thanks?",
        ["You are welcome.", "Anytime!"]
    ]
]

def chat():
    print("Chatbot: Hi there! I'm your friendly chatbot. How can I assist you?")
    chat = Chat(pairs, reflections)
    chat.converse()

chat = Chat(pairs, reflections)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_input = request.form['user_message']
    response = chat.respond(user_input)
    return response

if __name__ == '__main__': 
    app.run(debug=False) 