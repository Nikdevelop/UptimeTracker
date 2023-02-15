import sqlite3
import os


def create():
    connection = sqlite3.connect('Users.db')
    cursor = connection.cursor()
    cursor.executescript(
'''CREATE TABLE Users (
Id       INTEGER PRIMARY KEY AUTOINCREMENT
                    UNIQUE
                    NOT NULL,
Username STRING  UNIQUE
                    NOT NULL,
Password STRING  NOT NULL
);
CREATE TABLE Sites (
    Id       INTEGER PRIMARY KEY AUTOINCREMENT
                     NOT NULL,
    UserId   INTEGER NOT NULL,
    SiteAddr STRING  NOT NULL
);
''')
    connection.commit()

if __name__ == '__main__':
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    create()