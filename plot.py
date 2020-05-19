from datetime import datetime
import dash
from dash.dependencies import Output, Input
from flask_login import LoginManager, UserMixin,login_required, login_user, logout_user 
from flask import Flask, request, url_for, redirect, render_template, make_response, Response, session, abort
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
import sqlite3
import pandas as pd
import numpy as np
import os 

port = 8090
debug = True
file = open('./config/tickers.txt')
tickerList = file.read().split('\n')
tickerList = [i for i in tickerList if i != '']

server = Flask(__name__)
app = dash.Dash(__name__,server=server)
app.layout = html.Div([
        dcc.Dropdown(
                id='ticker_select',
                options=[{'label': v, 'value': v} for v in tickerList],
                multi=True,
                value='Tickers',
            ),
        dcc.Graph(id='graph')
    ])



login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "login"

server.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx'
)

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = "user" + str(id)
        self.password = self.name + "_secret"
    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)

   
users = [User(id) for id in range(1, 2)]

@server.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']        
        if password == username + "_secret":
            id = username.split('user')[1]
            user = User(id)
            login_user(user)
            return redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')

@server.route("/logout")
@login_required
def logout():
    logout_user()
    return Response('<p>Logged out</p>')


@server.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')
    
    
@login_manager.user_loader
def load_user(userid):
    return User(userid)


@login_required
@server.route('/',methods=['GET','POST'])
@app.callback(Output('graph', 'figure'),[Input('ticker_select', 'value')])
def update_graph_scatter(input_ticker):
    conn = sqlite3.connect('./data/fin_app.db')
    df = pd.read_sql_query('select * from daily_data',conn)
    df['date'] = pd.to_datetime(df['date'])
    df['close'] = pd.to_numeric(df['close'])
    tickerList = list(df['ticker'].drop_duplicates())

    data = []
    trace1 = []

    if input_ticker is None:
        input_ticker = ['SPY']
    
    for i in input_ticker:
        trace1.append(
            go.Scatter(
                x = df[df['ticker'] == i]['date'], 
                y=df[df['ticker'] == i]['close'],
                name=i,
                mode= 'lines'
            )
        )

    layout = go.Layout(
        legend=dict(
            x=0,
            y=0,
            orientation="h"
        ),
        xaxis=dict(
            domain=[0, 1]
        ),
        yaxis=dict(
            domain=[0, 1]
        ),
        height=750,
        margin={'t':20,'b':20}
    )

    data = trace1

    return {'data': data,'layout' : layout}


if __name__ == '__main__':
    server.run(host="0.0.0.0", port=8090)
