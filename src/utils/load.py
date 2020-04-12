import sqlite3
from io import StringIO


def load_db_into_memory(db_path='db.sqlite3'):
    connection = sqlite3.connect(db_path)
    file = StringIO('\n'.join(connection.iterdump()))
    connection.close()
    file.seek(0)
    connection = sqlite3.connect(':memory:')
    connection.executescript(file.read())
    connection.commit()
    connection.row_factory = sqlite3.Row
    print('Finished load db into memory ')
    return connection
