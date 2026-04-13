from sqlite3 import Connection

def insertData(connection: Connection):

    data = [
        ("Monty Python Live at the Hollywood Bowl", 1982, 7.9),
        ("Monty Python's The Meaning of Life", 1983, 7.5),
        ("Monty Python's Life of Brian", 1979, 8.0),
    ]
    cursor = connection.cursor()
    cursor.executemany("INSERT INTO movie VALUES(?, ?, ?)", data)
    connection.commit()
