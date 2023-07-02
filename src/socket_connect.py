import socket
import threading
import multiprocessing
from datetime import datetime
from src.save_sql import Mysql
from src.util import find_config

"""全局配置"""
queue = multiprocessing.Queue()
sql = Mysql()

cf, config = find_config()
cf.read(config, encoding='utf-8')


class SocketConnect(threading.Thread):
    def __init__(self, conn, addr):
        super().__init__()
        self.conn = conn
        self.addr = addr

    def run(self):
        print('\n * access successfully! ', self.addr)
        received = False
        while True:

            try:
                msg = self.conn.recv(1024).decode('utf-8')
            except ConnectionResetError or ConnectionAbortedError:
                print(' * Reconnection...')
                self.conn.close()

            now = datetime.now()
            if len(msg) == 0:
                print(f'{self.addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] "disconnected"\n')
                break

            # 当接收的信息中含有英文逗号，则断开连接并通过’queue‘传递参数，最后将正确的值发送到数据库
            elif ',' in msg:
                print(f'{self.addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] received correct msg: '
                      f'"{msg}"\n')
                received = True
                break

            print(f'{self.addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] received wrong msg: "{msg}"')
            self.conn.send(f"[server] received message\n".encode('utf-8'))
        if reversed:
            queue.put(msg)
        self.conn.close()


def socket_server():
    # 建立TCP嵌套字
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostbyname(socket.gethostname())
    port = 5001
    record_id = ''

    sock.bind((host, port))
    print(f'\n * Socket server start... {(socket.gethostbyname(socket.gethostname()), port)}\n')
    sock.listen(5)
    while True:
        conn, addr = sock.accept()

        dataset = sql.fetch_data()
        for data in dataset:
            #如果数据库不为空，并且数据库中有报警信息，且这个报警信息没有被记录，则发送信息给正常车
            if dataset != [] and data[1] == 'accident' and data[3] not in record_id:
                record_id += data[3] + ','
                conn.send(f"1".encode('utf-8'))
                break

        try:
            thread = SocketConnect(conn, addr)
            thread.start()
            received = queue.get()                         # 23,100231,N,21,665445,E,Car-mac:1231321

            # 如果收到数据则开始处理数据
            if received:
                # 转换成列表
                if type(received) is str:
                    received = received.split(',')

                for i in received:
                    if i in ('N', 'E'):
                        received.remove(i)                 # 删掉无用数据

                # 重新赋值
                long = received[0] + '.' + received[1].replace('.', '')
                lan = received[2] + '.' + received[3].replace('.', '')
                vid = received[-1].split(':')[1]

                received = [long, lan, vid]

                received.reverse()

                # type, conditions, vid, time, longitude, latitude, AcX, AcY, AcZ, Gyx, Gyy, Gyz, temp, GForce
                result = []
                received_index = 0
                keys = cf.get('general setting', 'vehicle_key').split(',')
                for index in range(len(keys)):
                    if index == 0:                       # type
                        result.append('normal')
                        continue
                    if index == 1:                       # conditions
                        result.append('no problem')
                        continue
                    elif index == 3:                     # time
                        now = datetime.now()
                        result.append(now.strftime("%d/%m/%Y %H:%M:%S"))
                        continue
                    # 正常车只传输车辆id，经度和纬度
                    elif index in (2,4,5):               # vid, longitude, latitude
                        result.append(received[received_index])
                        received_index += 1
                        continue
                    result.append(None)

                sql.save_data(tuple(result))             # 保存数据到数据库
                continue
        except threading.ThreadError:
            print(' * Reconnection...')
            continue
