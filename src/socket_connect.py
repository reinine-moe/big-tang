import socket
from multiprocessing import Process, Manager
from datetime import datetime
from src.save_sql import Mysql
from src.util import find_config

"""全局配置"""
sql = Mysql()
sql.init_table()

cf, config = find_config()
cf.read(config, encoding='utf-8')


class ServerProcess:
    def __init__(self, ipaddr, port, num):
        self.ipaddr = ipaddr
        self.port = port
        self.num = num

    @staticmethod
    def handle_recv(datas, client, record_id):
        """
        处理接收到的数据
        :param datas: 接收到的数据
        :param client: 请求的套接字类
        :param record_id: 数据互通的共享列表，用于记录事故车辆id
        """
        # 提取关键值
        datas = datas.split(',')
        datas = [i.split(':')[-1] for i in datas]

        # 如果数据为正常车并且事故车有被记录
        if 'normal' in datas and record_id:
            client.send(f"{record_id.pop()}".encode('utf-8'))

        # 如果数据为事故车并且当前数据没有被记录
        elif 'accident' in datas and datas[2] not in record_id:
            record_id.append(datas[2])  # data[2] = vid

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

    def server_link(self, conn, addr, record_id):
        """服务端的数据接收，在调用时使用多进程"""
        while True:
            received = False
            try:
                msg = conn.recv(1024).decode('utf-8')
            except ConnectionResetError or ConnectionAbortedError or UnicodeDecodeError:
                print(' * Reconnection...')
                break

            now = datetime.now()
            if len(msg) == 0:
                print(f'{addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] "disconnected"\n')
                break
            elif ',' in msg and type(msg) is str:
                print(f'{addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] data correct msg: '
                      f'"{msg}"\n')
                received = True
            else:
                print(f'{addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] data wrong msg: '
                      f'"{msg}"')

            if received:
                self.handle_recv(msg, conn, record_id)
        conn.close()


    def run(self, record_id):
        """服务端的启动程序"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 操作系统会在服务器socket被关闭或服务器进程终止后马上释放该服务器的端口

        sock.bind((self.ipaddr, self.port))
        sock.listen(self.num)
        print(f'\n * Socket server start... {(socket.gethostbyname(socket.gethostname()), self.port)}\n')
        while True:
            conn, addr = sock.accept()
            print('\n * access successfully! ', addr)
            # 启动多进程实现多连接
            p = Process(target=self.server_link, args=(conn, addr, record_id))
            p.start()


def server_start(host='0.0.0.0', port=5001, listen=5):
    """
    :param host: 目标ip
    :param port: 端口号
    :param listen: 监听数
    """
    manager = Manager()
    record_id = manager.list()  # 创建子进程之间可以进行共享的列表
    server = ServerProcess(host, port, listen)
    server.run(record_id)


if __name__ == '__main__':
    server_start()
