from datetime import datetime
import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
import requests
import pandas as pd
import numpy as np
import os 
import time

port = 8090
debug = True

app = dash.Dash(__name__)
app.layout = html.Div([
        dcc.Input(
            id='ticker_input',
            placeholder='Enter a ticker...',
            type='text',
            value='SPY'
        ),
        dcc.Graph(id='graph')
    ])


@app.callback(Output('graph', 'figure'),[Input('ticker_input', 'value')])
def update_graph_scatter(input_ticker):
    AV_KEY = os.environ['av_key']
    url = ('https://www.alphavantage.co/query?'
                    'function=TIME_SERIES_DAILY&'
                    'symbol={0}&'
                    'apikey={1}'.format(input_ticker,AV_KEY))
    response = requests.get(url).json()
    time.sleep(3)
    df = pd.DataFrame(response['Time Series (Daily)']).transpose()
    df['symbol'] = response['Meta Data']['2. Symbol']
    df = df.reset_index()
    df = df.sort_values('index')
    df.columns = ['date','open','high','low','close','volume','ticker']
    df['date'] = pd.to_datetime(df['date'])
    df['close'] = pd.to_numeric(df['close'])

    data = []
    trace1 = []
    
    for i in ['SPY']:
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
        height=975,
        margin={'t':0,'b':0}
    )

    data = trace1

    return {'data': data,'layout' : layout}


if __name__ == '__main__':
    app.run_server(host='0.0.0.0',port=port,debug=debug)
