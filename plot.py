from datetime import datetime
import dash
from dash.dependencies import Output, Input
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

app = dash.Dash(__name__)
app.layout = html.Div([
        dcc.Dropdown(
                id='ticker_select',
                options=[{'label': v, 'value': v} for v in tickerList],
                multi=True,
                value='Tickers',
            ),
        dcc.Graph(id='graph')
    ])


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
    app.run_server(host='0.0.0.0',port=port,debug=debug)
