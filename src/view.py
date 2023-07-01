#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, request
from flask_cors import CORS
from src.socket_connect import *
from src.util import find_config, generate_sql_json, analysis_data
import time
import signal

"""全局变量"""
cf, config = find_config()
cf.read(config, encoding='utf-8')

app = Flask(__name__)
CORS(app, resources=r'/*')  # 设置跨域

sql = Mysql()


@app.route('/')
def index():
    return 'hello client'


@app.route('/send', methods=['GET', 'POST'])
def receive_data():
    sql.init_table()
    keys   = cf.get('general setting', 'vehicle_key').split(',')
    result = []

    # 循环遍历配置文件中的值，并接收以此为参数的返回值，将其存进result列表中
    for i in keys:
        value = request.args.get(i)
        result.append(value)

    sql.save_data(tuple(analysis_data(result)))

    key_result = {}
    counter = 0
    while counter < len(keys):
        key_result.update({f'{keys[counter]}': f'{result[counter]}'})
        counter += 1

    return key_result


@app.route('/<type>/api')
def response(type):
    if type == 'vehicle':
        result      = sql.fetch_data()
        json_result = generate_sql_json(result)

        json_result.update({'info': {'recent upload': sql.fetch_latest_time(), 'sum': len(result)}})
        return json_result

    elif type == 'account':
        result      = sql.fetch_data(False)
        json_result = generate_sql_json(result, False)

        json_result.update({'info': {'recent upload': sql.fetch_latest_time(False), 'sum': len(result)}})
        return json_result
    else:
        return {'msg': 'bad request'}


def runserver():
    # 信号处理
    signal.signal(signal.SIGINT, signal.SIG_DFL)         # 注册对 SIGINT 信号的处理。
                                                         # SIGINT 信号通常是在用户按下Ctrl+C键时发送给程序的，
                                                         # 用于请求程序终止。

    signal.signal(signal.SIGTERM, signal.SIG_DFL)        # SIGTERM信号是由操作系统发送给进程，用于请求进程终止。

    #  创建线程
    main_thr        = threading.Thread(target=app.run, args=['192.168.0.100'])  # '192.168.0.100' '0.0.0.0'
    main_thr.daemon = True
    main_thr.start()
    time.sleep(0.5)

    comm_thr        = threading.Thread(target=socket_server)
    comm_thr.daemon = True
    comm_thr.start()

    while True:
        pass

if __name__ == '__main__':
    runserver()