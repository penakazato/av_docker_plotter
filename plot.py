from datetime import datetime
import dash
from dash.dependencies import Output, Input
from flask_login import LoginManager, UserMixin,login_required, login_user, logout_user 
from flask import Flask, request, url_for, redirect, render_template, make_response, Response, session, abort
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
from sqlalchemy import create_engine
import sqlite3
import pandas as pd
import numpy as np
import os 

env = os.environ['FINAPP_ENV']

if env == 'LOCAL':
    file = open('./config/tickers.txt')
    port = 8090
    debug = True
    refresh=1000
else:
    file = open('/home/pi/daily_movers_pull/config/tickers.txt')
    port = 80
    debug = False
    refresh=30

tickerList = file.read().split(',')


################################################################################################
#### Create Flask Server
################################################################################################

server = Flask(__name__)

server.config.update(
    SECRET_KEY = 'secret_xxx'
)

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = os.environ['app_user']
        self.password = os.environ['app_pw']
    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "login"
users = [User(os.environ['app_user'])]

@server.route("/", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(id)
        login_user(user)
        if password == os.environ['app_pw']:
            return redirect('/app')
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')

@login_manager.user_loader
def load_user(userid):
    return User(userid)

################################################################################################
#### Create Dashboard App
################################################################################################

app = dash.Dash(name='app',server=server,url_base_pathname='/app/')

app.layout = html.Div([
        dcc.Dropdown(
                id='ticker_select',
                options=[{'label': v, 'value': v} for v in tickerList],
                multi=True,
                value='Tickers',
            ),
        dcc.Graph(id='live-graph'),
        dcc.Interval(
            id='graph-update',
            interval=refresh*1000
        ),
    ])


def addAttributes(inDF,tick):
    df = inDF[inDF['ticker'] == tick].copy()
    df.loc[:,'bb_m'] = df['idx_price'].rolling(20).mean()
    df.loc[:,'std_20'] = df['idx_price'].rolling(20).std()
    df.loc[:,'bb_u'] = df['bb_m'] + (2*df['std_20'])
    df.loc[:,'bb_l'] = df['bb_m'] - (2*df['std_20'])
    df.loc[:,'ema_12'] = df['idx_price'].ewm(span=24,adjust=False).mean()
    df.loc[:,'ema_26'] = df['idx_price'].ewm(span=52,adjust=False).mean()
    df.loc[:,'ema_12_'] = df['close'].ewm(span=24,adjust=False).mean()
    df.loc[:,'ema_26_'] = df['close'].ewm(span=52,adjust=False).mean()
    df.loc[:,'macd'] = df['ema_12_'] - df['ema_26_']
    df.loc[:,'signal_line'] = df['macd'].ewm(span=18,adjust=False).mean()
    df.loc[:,'macd_hist'] = (df['macd'] - df['signal_line'])
    inc_macd = df['macd_hist'] > 0
    dec_macd = df['macd_hist'] < 0
    df.loc[:,'delta'] = df['close'].diff()
    df.loc[:,'up'] = df['delta'].copy()
    df.loc[:,'down'] = df['delta'].copy()
    df.loc[:,'up'] = np.where(df['up'] < 0,0.0,df['up'])
    df.loc[:,'down'] = np.where(df['up'] > 0,0.0,np.abs(df['down']))
    df.loc[:,'rs_temp'] = df['up'].ewm(span=28,adjust=False).mean() / df['down'].ewm(span=28,adjust=False).mean()
    df.loc[:,'rsi'] = 100 - 100/(1 + df['rs_temp'])
    df.loc[:,'macd_hist'] = 100* (df['macd_hist'] / np.abs(df['macd_hist']).max())
    return(df)

@server.route("/app", methods=["GET", "POST"])
@app.callback(Output('live-graph', 'figure'),[Input('graph-update', 'n_intervals'),Input('ticker_select', 'value')])
@login_required
def update_graph_scatter(input_data,input_ticker):
    conn = sqlite3.connect('/Users/pnakaz/Documents/Python/fin_app.db')
    df = pd.read_sql_query("select distinct date,ticker,price as close,idx_price,pct_chg_today from rb_chart_data ",conn)
    df['date'] = pd.to_datetime(df['date'])
    df['idx_price'] = pd.to_numeric(df['idx_price'])
    df['close'] = pd.to_numeric(df['close'])
    tmp = df[df['ticker'] != 'SPY'].groupby(['date'])['idx_price'].mean().reset_index()
    tmp['ticker'] = 'composite'
    tmp['close'] = tmp['idx_price']
    tmp['pct_chg_today'] = np.nan
    tmp = tmp[list(df.columns)]
    df = pd.concat([df,tmp])
    tickerList = list(df['ticker'].drop_duplicates())
    cols = ['blue','green','red','orange','gray','purple','brown']
    col_Dict = dict(zip(tickerList,cols))

    data = []
    trace1 = []
    trace2 = []
    trace3 = []
    trace4 = []
    df_attr = pd.DataFrame(columns = ['date','ticker','close','idx_price','bb_m','bb_l','bb_u','macd','signal_line','macd_hist','rsi'])
    for i in tickerList:
        tmp = addAttributes(df,i)
        tmp = tmp[['date','ticker','close','idx_price','bb_m','bb_l','bb_u','macd','signal_line','macd_hist','rsi']]
        df_attr = pd.concat([df_attr,tmp])
    x_axis = [tmp['date'].min(),datetime(tmp['date'].max().year,tmp['date'].max().month,tmp['date'].max().day,16,0)]
    
    rsi_df = df_attr[['date','ticker','rsi']].drop_duplicates()
    rsi_df = pd.pivot_table(rsi_df,index='date',columns='ticker',values='rsi').reset_index()
    rsi_df = rsi_df[rsi_df['date'].dt.hour >= 10]
    rsi_df['baseline_rsi'] = (rsi_df['composite'] + rsi_df['SPY']) / 2

    macd_df = df_attr[['date','ticker','macd_hist']].drop_duplicates()
    macd_df = pd.pivot_table(macd_df,index='date',columns='ticker',values='macd_hist').reset_index()
    macd_df = macd_df[macd_df['date'].dt.hour >= 10]
    macd_df['baseline_macd'] = (macd_df['composite'] + macd_df['SPY']) / 2
        
    tickerList = [i for i in tickerList if i not in input_ticker]
    for i in tickerList:
        rsi_df[i+'_rel'] = (rsi_df[i] / rsi_df['baseline_rsi']) - 1
        rsi_df[i+'_rel'] = 100 * np.abs(rsi_df[i+'_rel'])
        trace1.append(
            go.Scatter(
                x = df_attr[df_attr['ticker'] == i]['date'], 
                y=df_attr[df_attr['ticker'] == i]['idx_price'],
                name=i,
                mode= 'lines',
                line = {'color':col_Dict[i]}
            )
        )
        trace1.append(
            go.Scatter(
                x = df_attr[df_attr['ticker'] == i]['date'], 
                y=df_attr[df_attr['ticker'] == i]['bb_m'],
                name=i+'_BBM',
                mode= 'lines',
                line = {'color':col_Dict[i],'dash':'dash'},
                showlegend=False,
                hoverinfo='skip'
            )
        )
        trace1.append(
            go.Scatter(
                x = df_attr[df_attr['ticker'] == i]['date'], 
                y=df_attr[df_attr['ticker'] == i]['bb_l'],
                name=i+'_BBL',
                mode= 'lines',
                line = {'color':col_Dict[i],'dash':'dashdot','width':1},
                showlegend=False,
                hoverinfo='skip'
            )
        )
        trace1.append(
            go.Scatter(
                x = df_attr[df_attr['ticker'] == i]['date'], 
                y=df_attr[df_attr['ticker'] == i]['bb_u'],
                name=i+'_BBU',
                mode= 'lines',
                line = {'color':col_Dict[i],'dash':'dashdot','width':1},
                showlegend=False,
                hoverinfo='skip'
            )
        )
        trace2.append(
            go.Scatter(
                x = df_attr[df_attr['ticker'] == i]['date'], 
                y=df_attr[df_attr['ticker'] == i]['rsi'],
                name=i + '_RSI',
                xaxis='x2',
                yaxis='y2',
                mode= 'lines',
                line = {'color':col_Dict[i]},
                showlegend=False
            )
        )
        trace3.append(
            go.Scatter(
                x = df_attr[df_attr['ticker'] == i]['date'], 
                y=df_attr[df_attr['ticker'] == i]['macd_hist'],
                name=i + '_MACD',
                xaxis='x3',
                yaxis='y3',
                mode= 'lines',
                line = {'color':col_Dict[i]},
                showlegend=False
            )
        )
        if i not in ['SPY','composite']:
            trace4.append(
                go.Scatter(
                    x = rsi_df['date'], 
                    y=rsi_df[i+'_rel'],
                    name=i + '_rel_rsi',
                    xaxis='x4',
                    yaxis='y4',
                    mode= 'lines',
                    line = {'color':col_Dict[i]},
                    showlegend=False
                )
            )
    trace2.append(go.Scatter(
                    x=x_axis,
                    y=70*np.ones(len(tmp['date'])),
                    mode= 'lines',
                    name='over_bought',
                    xaxis='x2',
                    yaxis='y2',
                    line = {'color':'red','dash':'dash'},
                    showlegend=False
                    ))
    trace2.append(go.Scatter(
                    x=x_axis,
                    y=30*np.ones(len(tmp['date'])),
                    mode= 'lines',
                    name='over_sold',
                    xaxis='x2',
                    yaxis='y2',
                    line = {'color':'green','dash':'dash'},
                    showlegend=False
                    ))  
    trace2.append(go.Scatter(
                    x=rsi_df['date'],
                    y=rsi_df['baseline_rsi'],
                    mode= 'lines',
                    name='baseline_rsi',
                    xaxis='x2',
                    yaxis='y2',
                    line = {'color':'black','dash':'dashdot','width':6},
                    showlegend=False
                    )) 
    trace3.append(go.Scatter(
                    x=macd_df['date'],
                    y=macd_df['baseline_macd'],
                    mode= 'lines',
                    name='baseline_macd',
                    xaxis='x3',
                    yaxis='y3',
                    line = {'color':'black','dash':'dashdot','width':6},
                    showlegend=False
                    )) 
    trace3.append(go.Scatter(
                    x=x_axis,
                    y=0*np.ones(len(tmp['date'])),
                    mode= 'lines',
                    name='cross_over',
                    xaxis='x3',
                    yaxis='y3',
                    line = {'color':'black','dash':'dash'},
                    showlegend=False
                    ))  
    trace4.append(go.Scatter(
                    x=x_axis,
                    y=35*np.ones(len(df_attr['date'])),
                    mode= 'lines',
                    name='signal',
                    xaxis='x4',
                    yaxis='y4',
                    line = {'color':'black','dash':'dash'},
                    showlegend=False
                    ))

    layout = go.Layout(
        legend=dict(
            x=0,
            y=0,
            orientation="h"
        ),
        xaxis=dict(
            domain=[0, 1],
            range=x_axis,
            ticks='',
            showticklabels=False
        ),
        yaxis=dict(
            domain=[0.60, 1],
            showticklabels=False
        ),
        xaxis2=dict(
            domain=[0, 1],
            range=x_axis,
            ticks='',
            showticklabels=False
        ),
        yaxis2=dict(
            domain=[0.40, 0.58],
            range=[0,100],
            showticklabels=False,
            anchor='x2'
        ),
        xaxis3=dict(
            domain=[0, 1],
            range=x_axis,
            ticks='',
            showticklabels=False
        ),
        yaxis3=dict(
            domain=[0.20, 0.38],
            range=[-105,105],
            showticklabels=False,
            anchor='x3'
        ),
        xaxis4=dict(
            domain=[0, 1],
            range=x_axis,
            ticks='',
            showticklabels=False
        ),
        yaxis4=dict(
            domain=[0, 0.15],
            range=[0,60],
            showticklabels=False,
            anchor='x3'
        ),
        height=975,
        margin={'t':0,'b':0}
    )

    data = trace1 + trace2 + trace3 + trace4

    return {'data': data,'layout' : layout}



if __name__ == '__main__':
    server.run(debug=True, port=port)
