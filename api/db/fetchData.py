from sqlite3 import Connection

def getData(connection: Connection):
   cursor = connection.cursor()
   cursor.execute("SELECT year, title FROM movie ORDER BY year")
   return [dict(row) for row in cursor.fetchall()]

