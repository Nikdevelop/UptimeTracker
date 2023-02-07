import flask
from flask import render_template


app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run('127.0.0.1', debug=True)
