import pandas as pd
import requests
import json
import numpy as np
import telegram
import time
token='6093876602:AAE8CmMExRiztkyphqXIelWTr4qfBeQwp60'
id='-1001889177532'
bot = telegram.Bot(token=token)
list=['BTCUSDT','APTUSDT','ETHUSDT','OPUSDT','SOLUSDT','BNBUSDT','FTMUSDT','ETCUSDT','MATICUSDT','DYDXUSDT','MASKUSDT','GALAUSDT','DOTUSDT','AVAXUSDT','WAVESUSDT','ATOMUSDT']
def get_data(symbol):
    interval='1m'
    limit=1000
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        df=pd.DataFrame(data)
        df.columns=['time','Open','High','Low','Close','volume','time1','qv','count','buy_volume','gh','jk']
        df=df.loc[:,['time','Open','High','Low','Close']]
        df=df.astype(float)
        df['time']=pd.to_datetime(df['time'],unit='ms')
        df.set_index('time',inplace=True)
        df['MA']=df.Close.rolling(990).mean()
        df['std']=(df.Close.rolling(990).std())*0.15
        df['uc']=df['MA']+df['std']
        df['lc']=df['MA']-df['std']
        df_30m = df.resample('30T').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
        df_30m['ema12'] = df_30m['Close'].ewm(span=12).mean()
        df_30m['ema26'] = df_30m['Close'].ewm(span=26).mean()
        df_30m['macd_line'] = df_30m['ema12'] - df_30m['ema26']
        df_30m['signal_line'] = df_30m['macd_line'].ewm(span=9).mean()
        df_30m['macd_histogram'] = df_30m['macd_line'] - df_30m['signal_line']
        df = df.join(df_30m[['macd_line', 'signal_line', 'macd_histogram']], how='left')
        df.fillna(method='ffill', inplace=True)
        df['buy'] = np.where((df['Close'] > df['uc']) & (df['Close'].shift(1) < df['uc'].shift(1)) & (df['macd_line'] > df['signal_line']), 1, 0)
        df['sell'] = np.where((df['Close'] < df['lc']) & (df['Close'].shift(1) > df['lc'].shift(1)) & (df['macd_line'] < df['signal_line']), 1, 0)
    else:
        print(f"Request for {symbol} failed with status code {response.status_code}")
        
    return df
i=0
while True:
    for l in list:
        df=get_data(l)
        price=df.Close[-1]
        if df.buy[-2]==1:
            message = f'🟢BUY {l} PRICE: {price}'
            bot.send_message(chat_id=id, text=message)
        if df.sell[-2]==1:
            message= f'🔴SELL {l} PRICE: {price}'
            bot.send_message(chat_id=id, text=message)
    
    print(i)
    i=i+1
    time.sleep(60)
