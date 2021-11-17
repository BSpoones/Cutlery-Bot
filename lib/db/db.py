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
cur = cxn.cursor(prepared=True)

def reload():
    global cxn, cur
    cxn = connect(
            host=host,
            user=user,
            password=password,
            database=database,
        )
    cur = cxn.cursor()

def is_connected():
	print("TESTING CONNECTION")
	try:
		cxn.ping(True)
		print("CONNECTION MAINTAINED")
	except:
		print("CONNECTION LOST")
		reload()

def lastrowid():
	return cur.lastrowid

def with_commit(func):
	def inner(*args, **kwargs):
		func(*args, **kwargs)
		commit()

	return inner


@with_commit
def build():
	is_connected()
	if isfile(BUILD_PATH):
		scriptexec(BUILD_PATH)


def commit():
	is_connected()
	cxn.commit()

def close():
	is_connected()
	cxn.close()


def field(command, *values):
	is_connected()
	cur.execute(command, tuple(values))
	if (fetch := cur.fetchone()) is not None:
		return fetch[0]


def record(command, *values):
	is_connected()
	cur.execute(command, tuple(values))
	return cur.fetchone()


def records(command, *values):
	is_connected()

	cur.execute(command, tuple(values))

	return cur.fetchall()


def column(command, *values):
	is_connected()

	cur.execute(command, tuple(values))

	return [item[0] for item in cur.fetchall()]

def count(command,*values):
	
	cur.execute(command,tuple(values))
	return (cur.fetchone()[0])


def execute(command, *values):
	is_connected()

	cur.execute(command, tuple(values))


def multiexec(command, valueset):
	is_connected()

	cur.executemany(command, valueset)


def scriptexec(path):
	is_connected()

	with open(path, "r", encoding="utf-8") as script:
		script_list = script.read().split(";")
		for script in script_list:
			cur.execute(script)
build()

