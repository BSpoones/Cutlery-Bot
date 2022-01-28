from mysql.connector import connect
from os.path import isfile
import json, logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from mysql.connector.errors import OperationalError
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
def interact_with_server():
	"""
	Prevents database disconnecting from inactivity by sending request to
	database every 60 seconds
	"""
	try:
		records("SHOW DATABASES")
	except: # For when ERL loses connection to db
		reload()
		logging.error("Connection to database lost.")

db_scheduler = AsyncIOScheduler()
db_scheduler.add_job(
	interact_with_server,
	CronTrigger(
		second=0
	)
)
db_scheduler.start()

def reload():
    global cxn, cur
    try:
        cur.close()
        cxn.close()
    except:
        logging.error("THIS FAILED")
        pass
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

def count(command,*values):
	
	cur.execute(command,tuple(values))
	return (cur.fetchone()[0])


def execute(command, *values):
	cur.execute(command, tuple(values))


def multiexec(command, valueset):
	cur.executemany(command, valueset)


def scriptexec(path):
	

	with open(path, "r", encoding="utf-8") as script:
		script_list = script.read().split(";")
		for script in script_list:
			cur.execute(script)
build()

