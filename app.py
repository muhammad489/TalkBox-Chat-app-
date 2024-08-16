"""
from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from mysql.connector import Error
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
socketio = SocketIO(app)

# Dictionary to keep track of users in each room
room_users = {}

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='a@@@@@@@@@@',  # Replace with your MySQL password
            database='chatlogin'  # Replace with your MySQL database
        )
    except Error as e:
        print(f"Error: '{e}'")
    return connection

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user:
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return 'Invalid credentials'

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('create_room')
def handle_create_room(data):
    room_id = data['room_id']
    room_name = data['room_name']
    room_password = generate_password_hash(data['room_password'])

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO rooms (room_id, room_name, room_password) VALUES (%s, %s, %s)", 
                   (room_id, room_name, room_password))
    connection.commit()
    cursor.close()
    connection.close()

    room_users[room_id] = []  # Initialize the room in the room_users dictionary

    emit('room_created', {'room_id': room_id, 'room_name': room_name}, broadcast=True)

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    password = data['password']
    
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT room_password FROM rooms WHERE room_id=%s", (room_id,))
    room = cursor.fetchone()
    cursor.close()
    connection.close()

    if room and check_password_hash(room['room_password'], password):
        join_room(room_id)
        if room_id not in room_users:
            room_users[room_id] = []
        room_users[room_id].append(session['username'])
        emit('status', {'msg': f"{session['username']} has joined the room."}, room=room_id)
        emit('room_joined', {'room_id': room_id}, room=session.get('current_room'))
        session['current_room'] = room_id
        emit('update_users', {'users': room_users[room_id]}, room=room_id)
    else:
        emit('status', {'msg': 'Invalid room ID or password.'})

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data['room_id']
    leave_room(room_id)
    if session['username'] in room_users.get(room_id, []):
        room_users[room_id].remove(session['username'])
    emit('status', {'msg': f"{session['username']} has left the room."}, room=room_id)
    if session.get('current_room') == room_id:
        session.pop('current_room', None)
    emit('update_users', {'users': room_users.get(room_id, [])}, room=room_id)

@socketio.on('send_message')
def handle_send_message(data):
    room_id = data['room_id']
    message = data['message']
    emit('receive_message', {'msg': message, 'user': session['username']}, room=room_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
"""

from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
socketio = SocketIO(app)

# Dictionary to keep track of users in each room
room_users = {}

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='a@@@@@@@@@@',  # Replace with your MySQL password
            database='chatlogin'  # Replace with your MySQL database
        )
        return connection
    except Error as e:
        print(f"Error: '{e}'")
        return None

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user:
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return 'Invalid credentials'

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        connection = create_connection()
        if connection is not None:
            try:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                               (username, hashed_password))
                connection.commit()
                return redirect(url_for('login'))
            finally:
                cursor.close()
                connection.close()
    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@app.route('/logout', methods=['POST'])
def logout():
    username = session.get('username')
    if username:
        # Remove the user from the current room
        current_room = session.get('current_room')
        if current_room:
            if username in room_users.get(current_room, []):
                room_users[current_room].remove(username)
                emit('status', {'msg': f"{username} has left the room."}, room=current_room)
                emit('update_users', {'users': room_users[current_room]}, room=current_room)
            session.pop('current_room', None)
        
        # Remove user from session
        session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    if username:
        current_room = session.get('current_room')
        if current_room:
            if username in room_users.get(current_room, []):
                room_users[current_room].remove(username)
                emit('status', {'msg': f"{username} has left the room."}, room=current_room)
                emit('update_users', {'users': room_users[current_room]}, room=current_room)
            session.pop('current_room', None)

@socketio.on('create_room')
def handle_create_room(data):
    room_id = data['room_id']
    room_name = data['room_name']
    room_password = generate_password_hash(data['room_password'])

    connection = create_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO rooms (room_id, room_name, room_password) VALUES (%s, %s, %s)", 
                           (room_id, room_name, room_password))
            connection.commit()

            room_users[room_id] = []  # Initialize the room in the room_users dictionary

            emit('room_created', {'room_id': room_id, 'room_name': room_name, 'success': True}, broadcast=True)
        except Error as e:
            emit('room_created', {'success': False})
        finally:
            cursor.close()
            connection.close()

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    password = data['password']
    
    connection = create_connection()
    if connection is not None:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT room_password FROM rooms WHERE room_id=%s", (room_id,))
            room = cursor.fetchone()
            if room and check_password_hash(room['room_password'], password):
                join_room(room_id)
                if room_id not in room_users:
                    room_users[room_id] = []
                room_users[room_id].append(session['username'])
                session['current_room'] = room_id

                emit('status', {'msg': f"{session['username']} has joined the room."}, room=room_id)
                emit('room_joined', {'room_id': room_id}, room=room_id)
                emit('update_users', {'users': room_users[room_id]}, room=room_id)
            else:
                emit('status', {'msg': 'Invalid room ID or password.'})
        finally:
            cursor.close()
            connection.close()

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data['room_id']
    username = session.get('username')
    leave_room(room_id)
    if username in room_users.get(room_id, []):
        room_users[room_id].remove(username)
    emit('status', {'msg': f"{username} has left the room."}, room=room_id)
    if session.get('current_room') == room_id:
        session.pop('current_room', None)
    emit('update_users', {'users': room_users.get(room_id, [])}, room=room_id)

@socketio.on('send_message')
def handle_send_message(data):
    room_id = data['room_id']
    message = data['message']
    username = session['username']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Broadcast the message to all users in the room except the sender
    socketio.emit('receive_message', {'msg': message, 'user': username, 'timestamp': timestamp}, room=room_id, include_self=False)

    # Optionally, you can save the message to a database here

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)


