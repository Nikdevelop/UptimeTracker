import hashlib
import sqlite3
import threading
import base64

import flask
import requests
from flask import (redirect, render_template, request, make_response)


thread_lock = threading.Lock()
app = flask.Flask(__name__)
connection = sqlite3.connect('Users.db', check_same_thread=False)
cursor = connection.cursor()


@app.route('/', methods=['GET'])
def index():
    if not request.cookies.get('auth'):
        return render_template('index.html', message='Пожалуйста, войдите или зарегистрируйте аккаунт для отслеживания статистики сайтов.')
    
    user = check_auth(request.cookies.get('auth'))
    if not user:
        resp = make_response(render_template('index.html', message='Некорректные данные для авторизации!'))
        resp.delete_cookie('auth')
        return resp
    
    return render_template('index.html', user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username, password = [request.form.get(
            p) for p in ['username', 'password']]
        register_user(username, get_password_hash(password))
        return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username, password = [request.form.get(p) for p in ['username', 'password']]
        pass_hashed = get_password_hash(password)

        user = get_user(username, pass_hashed)
        if not user:
            return render_template('/login', error='Некорректное имя пользователя или пароль')
        auth = base64.b64encode(f'{username}:{pass_hashed}'.encode()).hex()

        resp = make_response(redirect('/'))
        resp.set_cookie('auth', auth)
        return resp


def get_password_hash(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth(token: str):
    username, passwd = base64.b64decode(token).decode().split(':')
    return get_user(username, passwd)

def get_user(name: str, passhash: str):
    with thread_lock:
        cursor.execute(
            f'SELECT * FROM Users WHERE (Username="{name}" AND Password="{passhash}" )')
        return cursor.fetchone()


def register_user(username: str, password: str) -> None:
    with thread_lock:
        cursor.execute(
            'INSERT INTO Users (Username, Password) VALUES (?, ?)', (username, password, ))
        connection.commit()


def load_sites_byUser(uid: int) -> list:
    with thread_lock:
        cursor.execute(f'SELECT * FROM Sites WHERE UserId = {uid}')
        return cursor.fetchall()


def save_site_byUser(uid: int, siteaddr: str) -> None:
    with thread_lock:
        cursor.execute(
            'INSERT INTO Sites (UserId, SiteAddr) VALUES (?, ?)', (uid, siteaddr, ))
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
