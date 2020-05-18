import pandas as pd
import os
import requests
import sqlite3
import time

file = open('./tickers.txt')
tickers = file.read().split('\n')
tickers = [i for i in tickers if i != '']

for i in tickers:
    AV_KEY = os.environ['av_key']
    conn = sqlite3.connect('./fin_app.db')
    url = ('https://www.alphavantage.co/query?'
                    'function=TIME_SERIES_DAILY&'
                    'symbol={0}&'
                    'apikey={1}'.format(i,AV_KEY))
    response = requests.get(url).json()
    df = pd.DataFrame(response['Time Series (Daily)']).transpose()
    df['symbol'] = response['Meta Data']['2. Symbol']
    df = df.reset_index()
    df = df.sort_values('index')
    df.columns = ['date','open','high','low','close','volume','ticker']
    df.to_sql("daily_data",conn,if_exists="append",index=False)
    time.sleep(15)
    
conn.close()
