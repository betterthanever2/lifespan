from datetime import datetime as dt, date as d
import pandas as pd
import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from connection import *
from dash.dependencies import Input, Output, State
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sd_material_ui as material
from time import sleep
import json

connect = create_connection()
c = connect.cursor()
#
# # add user
# add_user = """
# INSERT INTO person(fname, lname) VALUES('Denis', 'Shvetsov')
# """
#
# quiet_equery(connect, add_user)
# # loud_equery(connect, table_names2)
#
# add_event = f"""
# INSERT INTO events(time, title, description, user_id) VALUES ('{dt(1984,5,11,2,0,0)}', 'Birth', 'Was born in Mykolaiv', 1)
# """
#
# quiet_equery(connect, add_event)
#
# all_events_q = """SELECT * FROM events"""
# all_events = loud_equery(connect, all_events_q)
# all_events_pd = pd.DataFrame(all_events, columns=['ID', 'Time', 'Title', 'Description', 'User'])

######################################

ppl = '''SELECT (fname || ' ' || lname) "name" FROM people'''
n = loud_equery(connect, ppl)
names = [x[0] for x in n]

tags = ['fundamental', 'travel', 'education', 'birth of child', 'marriage', 'divorce', 'violence', 'state', 'work']
significance = {'very': 1, 'not really': 3, 'regular': 2, 'irrelevant': 4}

server = Flask(__name__)
app = dash.Dash(__name__, title='Whole Life', update_title=None, server=server, suppress_callback_exceptions=True)
app.server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# app.server.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123edcxzaqws@localhost/life' #local only

# for live Heroku PostgreSQL db
app.server.config["SQLALCHEMY_DATABASE_URI"] = "postgres://fbqdnsjrufapee:d45f7a8ff55236b9778abbacb443a792d73597718c3a761175f5879a49e3ca21" \
                                               "@ec2-54-228-174-49.eu-west-1.compute.amazonaws.com:5432/d56rpgtdtdbf74"

db = SQLAlchemy(app.server)

class Event(db.Model):
	__tablename__ = 'events'

	Id = db.Column(db.Integer, nullable=False, primary_key=True)
	Title = db.Column(db.String(80))
	Date = db.Column(db.Date)
	User_id = db.Column(db.Integer)
	Description = db.Column(db.String(4000))
	Tags = db.Column(db.String)
	Others = db.Column(db.String)
	Public = db.Column(db.Boolean)
	Added_on = db.Column(db.Date)
	Added_by = db.Column(db.Integer)
	Last_modified = db.Column(db.Date)
	Significance = db.Column(db.Integer)

	def __init__(self, id, title, date, person_id, description, tags, others, public, added_on, added_by, last_modified, sign):
		self.Id = id
		self.Date = date
		self.Title = title
		self.Description = description
		self.User_id = person_id
		self.Tags = tags
		self.Others = others
		self.Public = public
		self.Added_on = added_on
		self.Added_by = added_by
		self.Last_modified = last_modified
		self.Significance = sign

app.layout = html.Div(children=[
	html.H2('Recently added events'),
	html.Hr(),
	html.Div(children=[
		material.Dialog(children=[
			html.H2('Add new life event', style={'text-align': 'center'}),
			html.Fieldset(id='new_event', children=[
				html.Div(children=[
					dcc.Input(id='event_title', placeholder='What happened?', value='',style={'width': '75%', 'padding': '5px', 'margin-bottom': '5px', 'height': '50px',
					                                                                 'border-radius': '3px', 'font-size': '14px'}),
					dcc.DatePickerSingle('event_date', style={'float': 'right', 'margin-left': '5px'}, placeholder='When?', initial_visible_month=d(2021, 1, 15),
					                     display_format='DD.MM.Y', month_format='MMMM Y', first_day_of_week=2, day_size=30, className='datepicker'),], style={'display': 'flex'}),
				html.Div(children=[
					dcc.Dropdown(id='event_significance', options=[{'label': q, 'value': q} for q in significance.keys()], placeholder='Is it significant?',
				                                multi=False, className='dropdown_single', style={'height': '50px'}),
					dcc.Dropdown(id='event_person', placeholder='Whose story is it?', options=[{'label': z, 'value': z} for z in names], multi=False,
					             className='dropdown_single', style={'height': '50px', 'float': 'right'}),], style={'display': 'flex'}),
				dcc.Textarea(id='event_description', placeholder='How it happened? Details, please', value='', className='desc'),
				html.Div(children=[
					dcc.Dropdown(id='event_tags', multi=True, options=[{'label': a, 'value': a} for a in tags], className='dropdown_multi', placeholder='What kind of event is '
					                                                                                                                                    'it?', style={'height': '50px'}),
					dcc.Dropdown(id='people_involved', multi=True, options=[{'label': z, 'value': z} for z in names], className='dropdown_multi', placeholder='Who else was involved?',
					             style={'height': '50px'}),], style={'display': 'flex'}),
			], className='fieldset'),
			dcc.Checklist(id='public', options=[{'label': 'public', 'value': 'public'}], value=['public'], style={'font-size' : '18px', 'display': 'block',
			                                                                                                      'margin-top': '5px'}),
			html.Div(children=[
				html.Div(id='message'),
				material.Button(children='Save', id='savior', variant='outlined', n_clicks=0, className='butt')
			], id='save_div'),
		], id='dialog', open=False, useBrowserSideClose=True, className='dialog', scroll='body'),
		html.Div(id='input', children=[
			material.Button(children='Add new record', id='add_new_record', variant='outlined', className='butt')]),
	]),
	dcc.Interval(id='interval', interval=5, n_intervals=0),
	html.Div(id='table')
])
server = app.server

@app.callback(
	Output('table', 'children'),
	Input('interval', 'n_intervals')
)
def display_table(n_intervals):
	df = pd.read_sql_table('events', con=db.engine)
	# print(df)
	return [
		dash_table.DataTable(id='events_table', data=df.to_dict('records'),
		                     columns=[{'name': y, 'id': y, 'deletable': False} for y in ['title', 'date', 'the_person', 'description', 'tags', 'people_involved', 'public', 'added_on', 'significance']])
	]

@app.callback(
	Output('dialog', 'open'),
	Input('add_new_record', 'n_clicks'),
	Input('savior', 'n_clicks'),
	State('dialog', 'open')
)
def toggle_event_form(open_clicks, close_clicks, state):
	if not state and open_clicks:
		return True
	elif state and close_clicks:
		sleep(1.5)
		return False

@app.callback(
	Output('message', 'children'),
	Input('savior', 'n_clicks'),
	State('event_date', 'date'),
	State('event_title', 'value'),
	State('event_significance', 'value'),
	State('event_description', 'value'),
	State('event_person', 'value'),
	State('event_tags', 'value'),
	State('people_involved', 'value'),
	State('public', 'value'),
	State('dialog', 'open'), prevent_initial_call=True
)
def add_new_data(save, date, title, sign, desc, person, tags, others, public, modal_state):

	no_output = html.Plaintext("Please, complete all the fields")
	output = html.Plaintext("The data has been saved to your PostgreSQL database")

	if modal_state:
		# print(date, title, sign, desc, person, tags, others, public)
		added_on = last_modified = dt.today()
		added_by = 1 # TODO

		assert person is not None
		person_id = loud_equery(connect, f"""SELECT id FROM people WHERE (fname || ' ' || lname) = '{person}'""")[0][0]

		assert others is not None
		people_involved = []
		for p in others:
			people_involved.append(loud_equery(connect, f"""SELECT id FROM people WHERE (fname || ' ' || lname) = '{p}'""")[0][0])

		# assert public is not None
		if len(public) > 0:
			pbl = True
		else:
			pbl = False

		assert sign is not None
		s = significance[sign]

		# if date is not None and title is not None and desc is not None and person is not None:
		assert title is not None
		assert date is not None
		assert desc is not None
		pg = pd.DataFrame(data=[(title, date, person_id, desc, json.dumps(tags), json.dumps(people_involved), pbl, added_on, added_by, last_modified, s)],
		                  columns=['title', 'date', 'the_person', 'description', 'tags', 'people_involved', 'public', 'added_on', 'added_by', 'last_modified', 'significance'])
		# else:
		# 	pg = None

		if save > 0:
			pg.to_sql('events', con=db.engine, if_exists='append', index=False)
			return output
		else:
			return no_output

# @app.callback(
# 	Output('events_table', 'data'),
# 	Input('add_new_record', 'n_clicks'),
# 	State('events_table', 'data'),
# 	State('events_table', 'columns')
# )
# def add_row(n_clicks, rows, columns):
# 	if n_clicks > 0:
# 		rows.append({c['id']: '' for c in columns})
# 	return rows

if __name__ == '__main__':
	app.run_server(port=8050, debug=True)
	# app.run_server(port=8050, debug=False)