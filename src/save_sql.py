#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pymysql
from src.util import find_config, generate_sql_statement, generate_repr_statement

"""全局变量"""
cf, config = find_config()
cf.read(config, encoding='utf-8')


class Mysql:
    db_name = 'vehicledb'
    vehicle_table = 'vehicle_table'
    account_table = 'account_table'

    def __init__(self):

        self.host = cf.get('sql setting', 'host')
        self.user = cf.get('sql setting', 'user')
        self.password = cf.get('sql setting', 'passwd')
        self.port = int(cf.get('sql setting', 'port'))

        create_db = f"CREATE DATABASE IF NOT EXISTS {self.db_name} character set utf8;"

        con = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port,
        )

        db_cur = con.cursor()
        db_cur.execute(create_db)

        db_cur.close()
        con.close()

    def connect(self):
        con = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port,
            database=self.db_name
        )
        return con

    def init_table(self, is_vehicle=True):
        if is_vehicle:
            vehicle_keys = cf.get('general setting', 'vehicle_key').split(',')
            key_str = ''

            # 生成语句
            for index in range(len(vehicle_keys)):
                if index == 0:
                    key_str += f'\n{" " * 16}{vehicle_keys[index]} CHAR(10),\n'
                    continue
                elif index == len(vehicle_keys) - 1:
                    key_str += f'{" " * 16}{vehicle_keys[index]} VARCHAR(20)\n'
                    break
                key_str += f'{" " * 16}{vehicle_keys[index]} VARCHAR(20),\n'

            create_table = f'''
            CREATE TABLE IF NOT EXISTS {self.vehicle_table}
            (
                id INT auto_increment primary key ,{key_str}
            );
        '''
        else:
            account_keys = cf.get('general setting', 'account_key').split(',')
            create_table = f'''
            CREATE TABLE IF NOT EXISTS {self.account_table}
            (
                id INT auto_increment primary key ,
                {account_keys[0]} CHAR(20),
                {account_keys[1]} VARCHAR(10),
                {account_keys[2]} VARCHAR(20)

            );
        '''

        con = self.connect()
        cursor = con.cursor()
        cursor.execute(create_table)

        cursor.close()
        con.close()

    def save_data(self, dataset: tuple or list, is_vehicle=True):

        assert isinstance(dataset, tuple or list) \
               and len(cf.get('general setting', 'vehicle_key' if is_vehicle else 'account_key')), '不符合长度或类型要求'

        def commit():
            con.commit()
            table_cur.close()
            con.close()
            print('record inserted\n')

        con = self.connect()
        table_cur = con.cursor()

        # 判断数据属于哪个表
        if is_vehicle:
            keys = cf.get('general setting', 'vehicle_key').split(',')
            dbResult = self.fetch_data()

            # 若数据库里没有数据则直接添加一条新数据
            if len(dbResult) == 0:
                symbol_str = '%s,' * len(keys)                   # 根据配置文件生成与之对应值的插入语句
                key_str = generate_sql_statement(keys)           # 根据配置文件生成插入语句

                handle = f"INSERT INTO {self.vehicle_table}({key_str}) VALUES({symbol_str[:-1]});"
                table_cur.execute(handle, tuple(i for i in dataset))
                commit()
                return

            for data in dbResult:
                if data[1] == 'accident' and data[3] == dataset[2]:
                    repr_str = generate_repr_statement(keys)     # 根据配置文件生成替换语句
                    replace = f"UPDATE {self.vehicle_table} SET {repr_str} WHERE type = 'accident' AND vid = {dataset[2]}"
                    table_cur.execute(
                        replace, tuple(i for i in dataset if i not in ('normal', 'accident'))
                    )                                            # 不管当前传入的数据是正常车还是事故车，只要之前存入数据库中的vid被判定为事故车的话，
                                                                 # 就不会再改变此vid的类型，只更新其他参数
                    commit()
                    return

                elif data[1] == 'normal' and data[3] == dataset[2]:
                    repr_str = generate_repr_statement(keys, not_normal=False)
                    replace = f"UPDATE {self.vehicle_table} SET {repr_str} WHERE type = 'normal' AND vid = {dataset[2]}"
                    table_cur.execute(
                        replace,tuple(i for i in dataset)
                    )
                    commit()
                    return

        symbol_str = '%s,' * len(keys)                          # 根据配置文件生成与之对应值的插入语句
        key_str = generate_sql_statement(keys)                  # 根据配置文件生成插入语句

        handle = f"INSERT INTO {self.vehicle_table}({key_str}) VALUES({symbol_str[:-1]});"
        table_cur.execute(handle, tuple(i for i in dataset))

        commit()

    def fetch_data(self, is_vehicle=True):
        con = self.connect()
        cursor = con.cursor()

        query_data = f'select * from {self.vehicle_table if is_vehicle else self.account_table}; '
        cursor.execute(query_data)

        result = cursor.fetchall()

        cursor.close()
        con.close()

        return result

    def fetch_latest_time(self, is_vehicle=True):
        con = self.connect()
        cursor = con.cursor()

        table = 'vehicle_table' if is_vehicle else 'account_table'
        fetch_time = "SELECT `TABLE_NAME`, `UPDATE_TIME` FROM `information_schema`.`TABLES` " \
                     f"WHERE `information_schema`.`TABLES`.`TABLE_SCHEMA` = '{self.db_name}' " \
                     f"AND`information_schema`.`TABLES`.`TABLE_NAME` = '{table}';"

        cursor.execute(fetch_time)
        result = cursor.fetchone()

        cursor.close()
        con.close()

        return result[1]
