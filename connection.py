"""
Functions used to connect, query and modify the competition DB
Modules required: psycopg2, psycopg2.OperationalError

"""
import psycopg2
from psycopg2 import OperationalError

def create_connection(db='life', user='postgres', passw='123edcxzaqws', host='', prt=''):
	from psycopg2 import OperationalError
	connection = None
	try:
		connection = psycopg2.connect(
			database=db,
			user=user,
			password=passw,
			host=host,
			port=prt,
		)
		print("Connection to PostgreSQL DB successful")
	except OperationalError as e:
		print(f"The error '{e}' occurred")
	return connection

def quiet_equery(connection, query):
	connection.autocommit = True
	cursor = connection.cursor()
	try:
		cursor.execute(query)
		print("Updated")
	except OperationalError as e:
		print(f"The error '{e}' occurred")

def loud_equery(connect, query):
	cursor = connect.cursor()
	result = None
	try:
		cursor.execute(query)
		result = cursor.fetchall()
		return result
	except OperationalError as e:
		print(f"The error '{e}' occurred")