from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import requests
import time
import json

app = Flask(__name__)
CORS(app)  # 允許所有來源的跨域請求

@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    # 定義股票代碼列表
    stock_list_tse = ['0050', '0056', '2330', '2317', '1216']
    stock_list_otc = ['6547', '6180']
    
    # 組合API需要的股票清單字串
    stock_list1 = '|'.join('tse_{}.tw'.format(stock) for stock in stock_list_tse)
    stock_list2 = '|'.join('otc_{}.tw'.format(stock) for stock in stock_list_otc)
    stock_list = stock_list1 + '|' + stock_list2

    # 組合完整的 URL
    query_url = f'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_list}'

    # 呼叫股票資訊 API
    response = requests.get(query_url)

    # 判斷該 API 呼叫是否成功
    if response.status_code != 200:
        return jsonify({"error": "無法取得股票資訊"}), response.status_code

    # 將回傳的 JSON 格式資料轉成 Python 的 dictionary
    data = json.loads(response.text)

    # 過濾出有用到的欄位
    columns = ['c', 'n', 'z', 'tv', 'v', 'o', 'h', 'l', 'y', 'tlong']
    df = pd.DataFrame(data['msgArray'], columns=columns)
    df.columns = ['股票代號', '公司簡稱', '成交價', '成交量', '累積成交量', '開盤價', '最高價', '最低價', '昨收價', '資料更新時間']

    # 自行新增漲跌百分比欄位
    df.insert(9, "漲跌百分比", ((pd.to_numeric(df['成交價'], errors='coerce') - 
                               pd.to_numeric(df['昨收價'], errors='coerce')) / 
                               pd.to_numeric(df['昨收價'], errors='coerce') * 100).fillna(0))

    # 紀錄更新時間
    df['資料更新時間'] = (pd.to_numeric(df['資料更新時間']) / 1000).apply(
        lambda x: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x))
    )

    # 返回 JSON 格式的股票數據
    return jsonify(df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)
