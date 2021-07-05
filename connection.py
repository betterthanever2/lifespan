"""
Functions used to connect, query and modify the competition DB
Modules required: psycopg2, psycopg2.OperationalError

"""
import psycopg2
from psycopg2 import OperationalError

def create_connection(db='d56rpgtdtdbf74', user='fbqdnsjrufapee', passw='d45f7a8ff55236b9778abbacb443a792d73597718c3a761175f5879a49e3ca21',
                      host='ec2-54-228-174-49.eu-west-1.compute.amazonaws.com', prt='5432'):
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