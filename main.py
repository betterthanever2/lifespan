from datetime import datetime as dt, date as d
import pandas as pd
import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as bootstrap
from connection import *
from dash.dependencies import Input, Output, State
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from time import sleep
import json

connect = create_connection()
c = connect.cursor()

def name_for_id(uuid) -> str:
    return loud_equery(connect,f"""SELECT (fname || ' ' || lname) FROM people WHERE id = '{uuid}'""")[0][0]

def id_for_name(name) -> int:
    return loud_equery(connect,f"""SELECT id FROM people WHERE (fname || ' ' || lname) = '{name}'""")[0][0]

def display_human_date(timestamp):
    return dt.strftime(timestamp, '%d.%m.%Y, %a')

people_query = """SELECT (fname || ' ' || lname) FROM people"""
people = loud_equery(connect, people_query)
names = [name[0] for name in people]

tags = [
    "fundamental",
    "travel",
    "education",
    "birth of child",
    "marriage",
    "divorce",
    "violence",
    "state",
    "work",
]
significance = {1: "very", 3: "not really", 2: "somewhat", 4: "not at all"}

server = Flask(__name__)
app = dash.Dash(
    __name__,
    title="Whole Life",
    update_title=None,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[bootstrap.themes.BOOTSTRAP]
)
app.server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# app.server.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123edcxzaqws@localhost/life' #local only

# for live Heroku PostgreSQL db
app.server.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://fbqdnsjrufapee:d45f7a8ff55236b9778abbacb443a792d73597718c3a761175f5879a49e3ca21"
    "@ec2-54-228-174-49.eu-west-1.compute.amazonaws.com:5432/d56rpgtdtdbf74"
)

db = SQLAlchemy(app.server)

class Event(db.Model):
    __tablename__ = "events"

    Id = db.Column(db.Integer, nullable=False, primary_key=True)
    Title = db.Column(db.String(80))
    Date = db.Column(db.Date)
    People_main = db.Column(db.String)
    Description = db.Column(db.String(4000))
    Tags = db.Column(db.String)
    People_secondary = db.Column(db.String)
    Public = db.Column(db.Boolean)
    Added_on = db.Column(db.Date)
    Added_by = db.Column(db.Integer)
    Last_modified = db.Column(db.Date)
    Significance = db.Column(db.Integer)
    Location = db.Column(db.String)

    def __init__(
        self,
        id,
        title,
        date,
        people_main,
        description,
        tags,
        people_secondary,
        public,
        added_on,
        added_by,
        last_modified,
        sign,
        location,
    ):
        self.Id = id
        self.Date = date
        self.Title = title
        self.Description = description
        self.People_main = people_main
        self.Tags = tags
        self.People_secondary = people_secondary
        self.Public = public
        self.Added_on = added_on
        self.Added_by = added_by
        self.Last_modified = last_modified
        self.Significance = sign
        self.Location = location


ttl = bootstrap.FormGroup( # title
    [
        bootstrap.Label("Title", html_for="event_title"),
        bootstrap.Input(type="text", id="event_title", placeholder="What happened?", required=True,
                        style={'width': '100%', 'height': '50px'}),
    ]
)

ddt = bootstrap.FormGroup( # date
    [
        bootstrap.Label("Date", html_for="event_date"),
        dcc.DatePickerSingle(
            "event_date",
            style={'display': 'flex', 'border-radius': '3px', 'overflow': 'visible', 'font-size': '14px'},
            placeholder="When?",
            initial_visible_month=d(2021, 1, 15),
            display_format="DD.MM.Y",
            month_format="MMMM Y",
            first_day_of_week=2,
            day_size=30,
        ),
    ]
)

prs = bootstrap.FormGroup( # person
    [
        bootstrap.Label("Primary people", html_for="people_m"),
        dcc.Dropdown(
            id="people_m",
            multi=True,
            options=[{"label": z, "value": z} for z in names],
            className="dropdown_multi",
            placeholder="Who was in the center?",
            style={"height": "50px", 'width': '98%'},
        ),
    ]
)

sgn = bootstrap.FormGroup( # significance
    [
        bootstrap.Label("Significance", html_for="event_significance"),
        bootstrap.Select(
            id="event_significance",
            placeholder="Is it serious?",
            options=[{"label": q, "value": q} for q in significance.values()],
            required=True,
            style={'height': '50px'}
        ),
    ]
)

dsc = bootstrap.FormGroup( # description
    [
        bootstrap.Label("Description", html_for="event_description"),
        bootstrap.Textarea(id="event_description", placeholder="How did it happen?",
                           style={'width': '100%', 'height': '150px'}),
    ]
)

tgs = bootstrap.FormGroup( # tags (type)
    [
        bootstrap.Label("Type", html_for="event_tags"),
        dcc.Dropdown(
            id="event_tags",
            multi=True,
            options=[{"label": a, "value": a} for a in tags],
            className="dropdown_multi",
            placeholder="What kind of event is it?",
            style={"height": "50px", 'width': '98%'},
        ),
    ]
)

nvl = bootstrap.FormGroup( # people involved
    [
        bootstrap.Label("Other people involved", html_for="people_involved"),
        dcc.Dropdown(
            id="people_involved",
            multi=True,
            options=[{"label": z, "value": z} for z in names],
            className="dropdown_multi",
            placeholder="Who else was involved?",
            style={"height": "50px", 'width': '98%'},
        ),
    ]
)

pbl = bootstrap.FormGroup( # public or private
    [
        bootstrap.Checkbox(id="public_check", checked=True),
        bootstrap.Label("public", html_for="public_check", style={'margin-left': '3px'}),
    ],
    check=True,
)

lcc = bootstrap.FormGroup( # location
    [
        bootstrap.Label("Location", html_for="event_location"),
        bootstrap.Input(type="text", id="event_location", placeholder="Where?",
                        style={'height': '50px'}),
    ]
)

app.layout = html.Div(
    children=[
        html.H2("Recently added events"),
        html.Hr(),
        bootstrap.Row(children=[
            bootstrap.Col(id='filters_placeholder', width=9),
            bootstrap.Col(bootstrap.Button("Add record", id="open_modal", n_clicks=0, style={'float': 'right', 'margin-right': '50px'}), width=3),]
        ),
        bootstrap.Modal(
            [
                bootstrap.ModalHeader("Add new life event"),
                bootstrap.ModalBody(
                    [bootstrap.Form([
                            bootstrap.Row(
                                [
                                    bootstrap.Col([ttl], width=12)
                                ]
                            ),
                            bootstrap.Row(
                                [
                                    bootstrap.Col([ddt], width=3),
                                    bootstrap.Col([lcc], width=9),
                                ]
                            ),
                            bootstrap.Row(
                                [
                                    bootstrap.Col([prs], width=6),
                                    bootstrap.Col([sgn], width=6),
                                ]
                            ),
                            bootstrap.Row([bootstrap.Col([dsc], width=12)]),
                            bootstrap.Row(
                                [
                                    bootstrap.Col([tgs], width=6),
                                    bootstrap.Col([nvl], width=6),
                                ]
                            ),
                            bootstrap.Row([pbl]),
                            bootstrap.Row(
                                [
                                    bootstrap.Col(
                                        [], width=9),
                                    bootstrap.Col(
                                        [
                                            bootstrap.Button("Save", id="savior_button", n_clicks=0, className='savior_button', color='primary', type='submit')
                                        ], width=3),
                                ]
                            ),
                    ], id='modal_form', n_submit=0)]
                ),
            ],
            id="event_modal",
            is_open=False,
            className= 'modal_window'
        ),
        dcc.Interval(id='interval', interval=(864000/36), n_intervals=0),
        html.Div(id="events_table")
    ]
)
server = app.server


@app.callback(Output("events_table", "children"), Input("interval", "n_intervals"))
def display_table(n_intervals):
    df = pd.read_sql_table("events", con=db.engine)

    h = pd.Series([
        '\n'.join(name_for_id(b) for b in an) for an in df['people_involved']
    ])

    people_involved = pd.Series([
        '\n'.join(name_for_id(b) for b in an) for an in df['people_involved']
    ])

    event_date = pd.Series([
        display_human_date(da) for da in df['date']
    ])

    date_added = pd.Series([
        display_human_date(da) for da in df['added_on']
    ])

    df_modified = pd.DataFrame({'Title': df['title'], 'Date': event_date, 'Persona': h, 'Description': df['description'], 'Location': df['location'], 'Tags': df['tags'],
                                'People involved': people_involved, 'Date added': date_added})
    return [
        dash_table.DataTable(
            id="events_table",
            data=df_modified.to_dict("records"),
            columns=[
                {"name": y, "id": y, "deletable": False}
                for y in df_modified.columns
            ], style_table={'margin-left': '15px', 'width': '98%', 'margin-top': '15px'}
        )
    ]


@app.callback(
    Output('event_modal', 'is_open'),
    Input('modal_form', 'n_submit'),
    Input('open_modal', 'n_clicks'),
    State('event_modal', 'is_open'),
    State("event_date", "date"),
    State("event_title", "value"),
    State("event_significance", "value"),
    State("event_description", "value"),
    State("people_m", "value"),
    State("event_tags", "value"),
    State("people_involved", "value"),
    State("public_check", "checked"),
    State('event_location', 'value'), prevent_initial_call=True
)
def save_data(submit_form, open_modal, is_open, event_date, event_title, event_nificance, event_desc, people_m, event_ags, people_s, public_check, loc):
    if not open_modal:
        return
    added_on = last_modified = dt.today()
    people_main = []
    if people_m:
        for p in people_m:
            people_main.append(
                id_for_name(p)
            )

    people_involved = []
    if people_s:
        for p in people_s:
            people_involved.append(
                id_for_name(p)
            )
    if event_nificance:
        for k,v in significance.items():
            if v == event_nificance:
                s = k
    else:
        s = significance[2]

    if all([event_date, event_title, event_nificance, event_desc, people_m, event_ags, people_s, loc]):
        added_by = 1  # TODO

        pcheck = bool(public_check)
        idd = 0
        location = loc

        # current_event = Event(idd, event_title, event_date, json.dumps(people_main), event_desc, json.dumps(event_ags), json.dumps(people_involved), pcheck, added_on, added_by,
        #                       last_modified, s, location)
        # pg = pd.DataFrame(current_event)
        pg = pd.DataFrame(
            data=[
                (
                    event_title,
                    event_date,
                    json.dumps(people_main),
                    event_desc,
                    json.dumps(event_ags),
                    json.dumps(people_involved),
                    pcheck,
                    added_on,
                    added_by,
                    last_modified,
                    s,
                    loc
                )
            ],
            columns=[
                "title",
                "date",
                "the_person",
                "description",
                "tags",
                "people_involved",
                "public",
                "added_on",
                "added_by",
                "last_modified",
                "significance",
                "location"
            ],
        )

    if submit_form:
        pg.to_sql("events", con=db.engine, if_exists="append", index=False)
        return not is_open
    return not is_open


if __name__ == "__main__":
    # app.run_server(port=8050, debug=True)
    app.run_server(port=8050, debug=False)
