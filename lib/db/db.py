from mysql.connector import connect
from os.path import isfile
import json

with open("./secret/dbCredentials.json") as f:
    dbCredentials = json.load(f)
    host = dbCredentials["host"]
    user = dbCredentials["user"]
    password = dbCredentials["password"]
    database = dbCredentials["database"]

BUILD_PATH = "./data/db/build.sql"

cxn = connect(
    host=host,
    user=user,
    password=password,
    database=database,
)
cur = cxn.cursor()

def reload():
    global cxn, cur
    cxn = connect(
            host=host,
            user=user,
            password=password,
            database=database,
        )
    cur = cxn.cursor()


def lastrowid():
	return cur.lastrowid

def with_commit(func):
	def inner(*args, **kwargs):
		func(*args, **kwargs)
		commit()

	return inner


@with_commit
def build():
	if isfile(BUILD_PATH):
		scriptexec(BUILD_PATH)


def commit():
	cxn.commit()

def close():
	cxn.close()


def field(command, *values):
	cur.execute(command, tuple(values))

	if (fetch := cur.fetchone()) is not None:
		return fetch[0]


def record(command, *values):
	cur.execute(command, tuple(values))

	return cur.fetchone()


def records(command, *values):
	cur.execute(command, tuple(values))

	return cur.fetchall()


def column(command, *values):
	cur.execute(command, tuple(values))

	return [item[0] for item in cur.fetchall()]


def execute(command, *values):
	cur.execute(command, tuple(values))


def multiexec(command, valueset):
	cur.executemany(command, valueset)


def scriptexec(path):
	with open(path, "r", encoding="utf-8") as script:
		cur.executescript(script.read())