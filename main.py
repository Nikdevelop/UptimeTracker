import flask
import requests
from flask import render_template
import sqlite3
import threading


thread_lock = threading.Lock()
app = flask.Flask(__name__)
connection = sqlite3.connect('Users.db', check_same_thread=False)
cursor = connection.cursor()


@app.route('/<int:id>', methods=['GET'])
def index(id: int):
    # return render_template('index.html')
    return str(load_sites_byUser(id))

@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

def register_user(username: str, password: str) -> None:
    with thread_lock:
        cursor.execute('INSERT INTO Users (Username, Password) VALUES (?, ?)', (username, password, ))
        connection.commit()

def load_sites_byUser(uid: int) -> list:
    with thread_lock:
        cursor.execute(f'SELECT * FROM Sites WHERE UserId = {uid}')
        return cursor.fetchall()
    
def save_site_byUser(uid: int, siteaddr: str) -> None:
    with thread_lock:
        cursor.execute('INSERT INTO Sites (UserId, SiteAddr) VALUES (?, ?)', (uid, siteaddr, ))
        connection.commit()

def check_availability(site: str) -> bool:
    try:
        response = requests.get(site)
        if response.status_code == 200:
            return True
    except:
        pass

    return False


if __name__ == '__main__':
    app.run('127.0.0.1', debug=True)
