from mysql.connector import connect
from os.path import isfile
import json, logging, datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from mysql.connector.cursor import CursorBase
from mysql.connector import MySQLConnection
from CutleryBot.data.bot.data import EVENT_TYPES

with open("./secret/dbCredentials.json") as f:
    dbCredentials = json.load(f)
    host = dbCredentials["host"]
    user = dbCredentials["user"]
    password = dbCredentials["password"]
    database = dbCredentials["database"]

BUILD_PATH = "./data/db/build.sql"

cxn: MySQLConnection = connect(
    host=host,
    user=user,
    password=password,
    database=database,

)
cur: CursorBase = cxn.cursor(prepared=True)
def interact_with_server():
	"""
	Prevents database disconnecting from inactivity by sending request to
	database every 60 seconds
	"""
	try:
		records("SHOW DATABASES")
	except: # For when Cutlery Bot loses connection to db
		logging.error("Connection to database lost, reconnecting.....")
		reload()

db_scheduler = AsyncIOScheduler()
db_scheduler.add_job(
	interact_with_server,
	CronTrigger(
		second=10
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
    cur = cxn.cursor(prepared=True)
    logging.info("Successfully reconnected to the database")

def close():
    """
    Disconnects the database from the server
    """
    commit()
    logging.info("Closing database connection.....")
    try:
        cur.close()
        cxn.close()
        logging.info("Database connection closed")
    except:
        logging.error("THIS FAILED")
        pass

def lastrowid():
	return cur.lastrowid

def with_commit(func):
	def inner(*args, **kwargs):
		func(*args, **kwargs)
		commit()

	return inner

class Cache:
	def __init__(self):
		self.recent_requests = [] # Limit of 5 items
		self.recent_values = []
		self.recent_outputs = []
		self.request_timestamps = []
		CacheScheduler = AsyncIOScheduler()
		CacheScheduler.add_job(
			self.clear_cache,
			CronTrigger(second=0,jitter=10)
		)
		CacheScheduler.start()
	def clear_cache(self):
		self.recent_requests = [] # Limit of 5 items
		self.recent_values = []
		self.recent_outputs = []
		self.request_timestamps = []
	def check_cache(self,command, values) -> list | None:
		if command in self.recent_requests:
			index = self.recent_requests.index(command)
			if values == self.recent_values[index]:
				output = self.recent_outputs[index]
				timestamp = self.request_timestamps[index]
				if int(datetime.datetime.today().timestamp()) - int(timestamp) < 3: # 3 second cache
					return output
				else:
					self.remove_item_from_cache(index)
					return None
			else:
				# Expired entry in requests
				self.remove_item_from_cache(index)
				return None
		else:
			return None
	def add_to_cache(self,command,values,output):
		# Assumes that this output is not already in the cache
		if len(self.recent_requests) >= 10:
			self.recent_requests.append(command)
			self.recent_outputs.append(output)
			self.recent_values.append(values)
			self.request_timestamps.append(int(datetime.datetime.today().timestamp()))
   
			self.remove_item_from_cache(0)
		else:
			self.recent_requests.append(command)
			self.recent_outputs.append(output)
			self.recent_values.append(values)
			self.request_timestamps.append(int(datetime.datetime.today().timestamp()))


	def remove_item_from_cache(self,index):
		self.recent_requests.pop(index)
		self.recent_values.pop(index)
		self.recent_outputs.pop(index)
		self.request_timestamps.pop(index)

	def show_cache(self, index=None):
		if index is None:
			print(self.recent_requests,self.recent_values,self.recent_outputs,self.request_timestamps)
		else:
			print(self.recent_requests[index],self.recent_values[index],self.recent_outputs[index],self.request_timestamps[index])
			

db_cache = Cache()

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
	try:
		cache_output = db_cache.check_cache(command,values=(values))
		if cache_output is not None:
			return cache_output
		else:
			cur.execute(command, tuple(values))
			output = cur.fetchone()
			db_cache.add_to_cache(command,values,output)
			return output
	except:
		reload()
		cache_output = db_cache.check_cache(command,values=(values))
		if cache_output is not None:
			return cache_output
		else:
			cur.execute(command, tuple(values))
			output = cur.fetchone()
			db_cache.add_to_cache(command,values,output)
			return output
def records(command, *values):
	try:
		cache_output = db_cache.check_cache(command,values=(values))
		if cache_output is not None:
			return cache_output
		else:
			cur.execute(command, tuple(values))
			output = cur.fetchall()
			db_cache.add_to_cache(command,values,output)
			return output
	except:
		reload()
		cache_output = db_cache.check_cache(command,values=(values))
		if cache_output is not None:
			return cache_output
		else:
			cur.execute(command, tuple(values))
			output = cur.fetchall()
			db_cache.add_to_cache(command,values,output)
			return output

def column(command, *values):
	

	cur.execute(command, tuple(values))

	return [item[0] for item in cur.fetchall()]

def count(command,*values):
	
	cur.execute(command,tuple(values))
	return (cur.fetchone()[0])


def execute(command, *values):
	try:
		cur.execute(command, tuple(map(str,values)))
	except:
		reload()
		cur.execute(command, tuple(map(str,values)))


def multiexec(command, valueset):
	try:
		cur.executemany(command, valueset)
	except:
		reload()
		cur.executemany(command, valueset)


def scriptexec(path):
	with open(path, "r", encoding="utf-8") as script:
		script_list = script.read().split(";")
		for script in script_list:
			cur.execute(script)

def insert_hikari_events():
    possible_events = EVENT_TYPES
    LogActions = column("SELECT action_name FROM log_action")
    if sorted(LogActions) != sorted(possible_events): # Oh no- they're not the same!?! big sad
        logging.info("Adding new log actions to database")
        for event in possible_events:
            if event not in LogActions:
                execute("INSERT INTO log_action(action_name) VALUES (?)",event)
                logging.info(f"{event} added.")
    commit()

def is_in_db(value,col,table):
    """
    Checks if an item in in the database
    Returns None if not, row if is
    """
    return record(f"SELECT * FROM {table} WHERE {col} = ?",value)

build()
