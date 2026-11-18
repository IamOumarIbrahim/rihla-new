# the connection to the PostgreSQL database
# the rest of the server talks to the database only through this file
#
# the old code was written for SQLite, so this file changes the few
# SQLite words into PostgreSQL words before the query is sent:
#   ?                              -> %s      (how psycopg marks a value)
#   INTEGER PRIMARY KEY AUTOINCREMENT -> SERIAL PRIMARY KEY
#   REAL                           -> DOUBLE PRECISION
#   INSERT OR IGNORE INTO ...      -> INSERT INTO ... ON CONFLICT DO NOTHING
#   BEGIN IMMEDIATE                -> a lock so only one booking is saved at a time
#   PRAGMA table_info(x)           -> the column list of table x
import os
import psycopg

# where the database is, it can be changed with the RIHLA_DATABASE_URL setting
DATABASE_URL = os.environ.get("RIHLA_DATABASE_URL", "postgresql://rihla:rihla@localhost:5432/rihla")

# the tests use their own schema so the real data is never touched
SCHEMA = os.environ.get("RIHLA_SCHEMA", "public")

IntegrityError = psycopg.IntegrityError

# any number works, it is only the name of our booking lock
BOOKING_LOCK = 4242


# turns one SQLite query into a PostgreSQL query
# params is needed because sqlite can also use names like :staff for the values
def translate(sql, params):
    sql = sql.replace("?", "%s")
    if isinstance(params, dict):
        # longest names first so :id does not break :idx
        names = sorted(params.keys(), key=len, reverse=True)
        for name in names:
            sql = sql.replace(":" + name, "%(" + name + ")s")
    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    sql = sql.replace(" REAL", " DOUBLE PRECISION")
    # sqlite writes the time as 2026-11-18 22:15:00, we keep the same text
    sql = sql.replace("CURRENT_TIMESTAMP", "to_char(now(), 'YYYY-MM-DD HH24:MI:SS')")
    if "INSERT OR IGNORE INTO" in sql:
        sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
        sql = sql + " ON CONFLICT DO NOTHING"
    return sql


# looks like the cursor sqlite gives back, so the old code still works
class Result:
    def __init__(self, cursor, rows, last_id):
        self.cursor = cursor
        self.rows = rows
        self.lastrowid = last_id
        self.rowcount = cursor.rowcount

    def fetchone(self):
        if self.rows is None:
            return None
        if len(self.rows) == 0:
            return None
        return self.rows[0]

    def fetchall(self):
        if self.rows is None:
            return []
        return self.rows

    def __iter__(self):
        return iter(self.fetchall())


class Connection:
    def __init__(self):
        self.conn = psycopg.connect(DATABASE_URL)
        self.conn.execute("CREATE SCHEMA IF NOT EXISTS " + SCHEMA)
        self.conn.execute("SET search_path TO " + SCHEMA)

    def execute(self, sql, params=None):
        if params is None:
            params = ()
        text = sql.strip()

        # sqlite locks the whole file here, we only lock bookings
        if text == "BEGIN IMMEDIATE":
            cursor = self.conn.cursor()
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", (BOOKING_LOCK,))
            return Result(cursor, [], None)

        # PRAGMA table_info(name) gives one row per column, the name is in row[1]
        if text.startswith("PRAGMA table_info("):
            table = text[len("PRAGMA table_info("):-1]
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT ordinal_position, column_name FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
                (SCHEMA, table),
            )
            return Result(cursor, cursor.fetchall(), None)

        cursor = self.conn.cursor()
        cursor.execute(translate(sql, params), params)

        rows = None
        if cursor.description is not None:
            rows = cursor.fetchall()

        # new rows get their id from a sequence, lastval() gives the last one
        last_id = None
        if text.upper().startswith("INSERT") and cursor.rowcount > 0:
            try:
                cursor.execute("SAVEPOINT get_id")
                cursor.execute("SELECT lastval()")
                last_id = cursor.fetchone()[0]
                cursor.execute("RELEASE SAVEPOINT get_id")
            except psycopg.Error:
                # the table has no id column (users), so there is no lastval
                cursor.execute("ROLLBACK TO SAVEPOINT get_id")
        return Result(cursor, rows, last_id)

    def executemany(self, sql, rows):
        for row in rows:
            self.execute(sql, row)

    def cursor(self):
        return Cursor(self)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


# some old code asks for a cursor first, it works the same as conn.execute
class Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.result = None
        self.lastrowid = None

    def execute(self, sql, params=None):
        self.result = self.connection.execute(sql, params)
        self.lastrowid = self.result.lastrowid
        return self.result

    def fetchone(self):
        return self.result.fetchone()

    def fetchall(self):
        return self.result.fetchall()


def connect():
    return Connection()


# deletes the schema with all its tables (only used by the tests)
def drop_schema(name):
    conn = psycopg.connect(DATABASE_URL)
    conn.execute("DROP SCHEMA IF EXISTS " + name + " CASCADE")
    conn.commit()
    conn.close()
