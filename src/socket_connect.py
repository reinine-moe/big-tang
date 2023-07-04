import socket
from multiprocessing import Process
from datetime import datetime
from src.save_sql import Mysql
from src.util import find_config

"""全局配置"""
sql = Mysql()
sql.init_table()

cf, config = find_config()
cf.read(config, encoding='utf-8')


class ServerProcess:
    record_id = ''

    def __init__(self, ipaddr, port, num):
        self.ipaddr = ipaddr
        self.port = port
        self.num = num

    def handle_data(self, datas, client):
        dataset = sql.fetch_data()

        if datas and type(datas) is str:
            # 提取关键值
            datas = datas.split(',')
            datas = [i.split(':')[-1] for i in datas]

            if 'normal' in datas:
                for value in dataset:
                    # 如果数据库不为空，并且数据库中有报警信息，且这个报警信息没有被记录，则发送信息给正常车
                    if dataset != [] and value[1] == 'accident' and value[3] not in self.record_id:
                        self.record_id += value[3] + ','
                        client.send(f"1".encode('utf-8'))
                        print('send message!')
                        break

            # type, conditions, vid, time, longitude, latitude
            result = []
            data_index = 0
            keys = cf.get('general setting', 'vehicle_key').split(',')
            for index in range(len(keys)):
                if index == 3:  # time
                    now = datetime.now()
                    result.append(now.strftime("%d/%m/%Y %H:%M:%S"))
                    continue
                result.append(datas[data_index])
                data_index += 1

            sql.save_data(tuple(result))  # 保存数据到数据库

    # 服务端的数据接收，在调用时使用多进程
    def server_link(self, conn, addr):
        while True:
            received = False

            try:
                msg = conn.recv(1024).decode('utf-8')
            except ConnectionResetError or ConnectionAbortedError:
                print(' * Reconnection...')
                break

            now = datetime.now()
            if len(msg) == 0:
                print(f'{addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] "disconnected"\n')
                break
            elif ',' in msg:
                print(f'{addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] data correct msg: '
                      f'"{msg}"\n')
                received = True
            else:
                print(f'{addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] data wrong msg: '
                      f'"{msg}"')

            if received:
                self.handle_data(msg, conn)
        conn.close()

    # 服务端的启动程序
    def server_start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 操作系统会在服务器socket被关闭或服务器进程终止后马上释放该服务器的端口

        sock.bind((self.ipaddr, self.port))
        sock.listen(self.num)
        print(f'\n * Socket server start... {(socket.gethostbyname(socket.gethostname()), self.port)}\n')
        while True:
            conn, addr = sock.accept()
            print('\n * access successfully! ', addr)
            # 启动多进程实现多连接
            p = Process(target=self.server_link, args=(conn, addr))
            p.start()


if __name__ == '__main__':
    server = ServerProcess('0.0.0.0', 5001, 2)
    server.server_start()
