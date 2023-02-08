import hashlib
from queue import Queue
import sqlite3
import threading
import base64

from concurrent.futures.thread import ThreadPoolExecutor
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
    
    q = []
    # sites = [(site, 'Доступен' if check_availability(site) else 'Недоступен') for site in load_sites_byUser(user[0])]
    with ThreadPoolExecutor(max_workers=2) as executor:
        for s in load_sites_byUser(user[0]):
            executor.submit(check_availability, s, q)
    
    # tasks = []
    # for i in load_sites_byUser(user[0]):
    #     tasks.append(asyncio.ensure_future(check_availability(i)))
    
    # results = await asyncio.gather(*tasks)
    # results = sorted([(b, 'Доступен' if a else 'Недоступен') for a, b in loop.run(check_all_sites(load_sites_byUser(user[0]), user))], key=lambda x: x[0])

    return render_template('index.html', user=user, data=q)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username, password = [request.form.get(p) for p in ['username', 'password']]
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
        auth = base64.b64encode(f'{username}\n{pass_hashed}'.encode()).hex()

        resp = make_response(redirect('/'))
        resp.set_cookie('auth', auth)
        return resp

@app.route('/logout', methods=['GET'])
def logout():
    resp = make_response(redirect('/'))
    resp.delete_cookie('auth')
    return resp

@app.route('/create/', methods=['POST'])
def create():
    authcookie = request.cookies.get('auth')
    if not authcookie:
        return flask.abort(403)
    user = check_auth(authcookie)
    if not user:
        return flask.abort(401)
    
    save_site_byUser(user[0], request.form.get('siteaddr'))
    return redirect(request.referrer or '/')

@app.route('/delete/<int:siteid>', methods=['GET'])
def delete(siteid: str):
    authcookie = request.cookies.get('auth')
    if not authcookie:
        return flask.abort(403)
    user = check_auth(authcookie)
    if not user:
        return flask.abort(401)
    
    can_user_remove_it = any((s[0], s[1]) == (siteid, user[0]) for s in load_sites_byUser(user[0]))
    if not can_user_remove_it:
        return flask.abort(403)
    
    delete_site_byUser(user[0], siteid)
    return redirect(request.referrer or '/')


def get_password_hash(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth(token: str):
    username, passwd = base64.b64decode(bytes.fromhex(token)).decode().split('\n')
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

def delete_site_byUser(uid: int, siteid: int):
    with thread_lock:
        cursor.execute(f'DELETE FROM Sites WHERE UserId=? AND Id=?', (uid, siteid, ))

def load_sites_byUser(uid: int) -> list:
    with thread_lock:
        cursor.execute(f'SELECT * FROM Sites WHERE UserId = {uid}')
        return cursor.fetchall()


def save_site_byUser(uid: int, siteaddr: str) -> None:
    siteaddr = siteaddr if siteaddr.startswith('https://') else 'https://' + siteaddr
    with thread_lock:
        cursor.execute(
            'INSERT INTO Sites (UserId, SiteAddr) VALUES (?, ?)', (uid, siteaddr, ))
        connection.commit()


def check_availability(site: str, q: list) -> bool:
    try:
        response = requests.get(site[-1])
        if response.status_code == 200:
            q.append((True, site))
            return
    except:
        pass

    q.append((False, site))


if __name__ == '__main__':
    app.run('127.0.0.1', debug=True)
