import socket
from multiprocessing import Queue
from concurrent.futures import ThreadPoolExecutor
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
        self.record_queues = {}  # 记录每个车辆套接字对应的队列

    def handle_recv(self, datas, client, address, record_queue):
        """
        处理接收到的数据
        :param datas: 接收到的数据
        :param client: 请求的套接字类
        :param address: 请求的地址
        :param record_queue: 数据互通的共享列表，用于记录事故车辆id
        """
        # 提取关键值
        datas = datas.split(',')
        datas = [i.split(':')[-1] for i in datas]
        record_list = []

        # 弹出当前队列
        while not record_queue.empty():
            record_list.append(record_queue.get())

        # 如果数据为正常车并且事故车有被记录
        if 'normal' in datas and record_list:
            client.send(f"{record_list.pop()}".encode('utf-8'))

        # 如果数据为事故车并且当前数据没有被记录
        elif 'accident' in datas and datas[2] not in record_list:
            # 遍历队列字典，如果当前车辆进程的套接字不等于线程池中的套接字，则把当前车辆id存入其他车辆的队列中
            for car_queue in list(self.record_queues.items()):
                print(address, car_queue[0])
                if address != car_queue[0]:
                    car_queue[1].put(datas[2])  # data[2] = vid, 将车辆id放入队列顶部

        # type, conditions, vid, time, longitude, latitude
        result = []
        data_index = 0
        keys = cf.get('general setting', 'vehicle_key').split(',')
        for index in range(len(keys)):
            if index == 3:  # time
                now = datetime.now()
                result.append(now.strftime("%d/%m/%Y %H:%M:%S"))
                continue
            # 当索引大于发送数据本身则传输空值
            if data_index >= len(datas):
                result.append(None)
                data_index += 1
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
                print(f'{addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] "disconnected"')
                break
            elif ',' in msg and type(msg) is str:
                print(f'{addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] data correct msg: '
                      f'"{msg}"')

                # 检测发送的数据中是否发送了多余的重复值，没有则跳过
                try:
                    key             = cf.get('general setting', 'vehicle_key').split(',')[0]
                    detect_msg_index = msg.index(key, msg.index(key) + 1)
                    msg              = msg[:detect_msg_index]
                except ValueError and IndexError:
                    pass
                received = True
            else:
                print(f'{addr[0]} - - [{now.strftime("%d/%m/%Y %H:%M:%S")}] [socket server] data wrong msg: '
                      f'"{msg}"')

            if received:
                self.handle_recv(msg, conn, addr, record_id)
        conn.close()

    def run(self):
        """服务端的启动程序"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 操作系统会在服务器socket被关闭或服务器进程终止后马上释放该服务器的端口

        sock.bind((self.ipaddr, self.port))
        sock.listen(self.num)
        print(f'\n * Socket server start... {(socket.gethostbyname(socket.gethostname()), self.port)}\n')
        # 使用线程池管理多个子线程
        with ThreadPoolExecutor(max_workers=self.num) as executor:

            while True:
                conn, addr = sock.accept()
                print('\n * access successfully! ', addr)

                # 如果是新的正常车辆链接，则创建对应的队列
                if addr[0] not in self.record_queues:
                    self.record_queues[addr] = Queue()
                # 启动子线程处理连接
                executor.submit(self.server_link, conn, addr, self.record_queues[addr])


def server_start(host='0.0.0.0', port=5001, listen=5):
    """
    :param host: 目标ip
    :param port: 端口号
    :param listen: 监听数
    """
    server = ServerProcess(host, port, listen)
    server.run()


if __name__ == '__main__':
    server_start()
