import sqlite3


def get_dict_cursor(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row

    return cursor
