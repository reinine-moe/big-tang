#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os import path, getcwd
from datetime import datetime
import configparser


def generate_sql_json(dataset: tuple, is_vehicle=True):
    """
    封装数据库数据
    :param dataset: 数据库返回的数据组
    :param is_vehicle:  类型选择: True为车辆数据, False为账号数据
    :return: 封装好的字典(json)
    """

    # 读取配置文件
    cf, config = find_config()
    cf.read(config, encoding='utf-8')

    if is_vehicle:
        keys = cf.get('general setting', 'vehicle_key').split(',')
    else:
        keys = cf.get('general setting', 'account_key').split(',')

    # 生成json模板
    total_json = {}
    data_json = {}
    for key in keys:
        data_json.update({key: ''})
    for data in dataset:
        total_json.update({f'{data[3]}': data_json.copy()})

    # 导入数据
    dataset_index = 0                              # 嵌套元组下标

    for data in total_json:
        dataset_element_index = 1                  # 嵌套元组中每个子元组的下标
        for key in total_json[data]:
            total_json[data][key] = dataset[dataset_index][dataset_element_index]
            dataset_element_index += 1
        # 归零操作，并转到下一组数据
        dataset_index += 1

    result = {}
    result.update({'data': total_json})

    return result


def generate_sql_statement(handle):
    """
    生成数据库语句对应值
    :param handle: 根据配置文件生成的列表
    :return: 返回数据库需要的语句
    """
    key_str = ''
    for index in range(len(handle)):
        if index == len(handle) - 1:
            key_str += handle[index]
            continue
        key_str += handle[index] + ','

    return key_str


def generate_repr_statement(handle, not_normal=True):
    """
        生成数据库替换语句
        :param handle: 根据配置文件生成的列表
        :return: 返回数据库需要的语句
    """
    key_str = ''
    for index in range(len(handle)):
        if not_normal and handle[index] == 'type':
            continue
        elif index == len(handle) - 1:
            key_str += handle[index] + ' = %s'
            continue
        key_str += handle[index] + ' = %s,'

    return key_str


def find_config():
    """查找配置文件
    :return: 配置文件类容，配置文件路径
    """
    base_dir = getcwd().split('\\src')[0]
    config   = path.join(base_dir, 'src\\config.ini')
    cf = configparser.ConfigParser()

    return cf, config


def analysis_data(datas):
    """
    分析汽车数据
    :param datas: 车的各类信息
    :return: 分析好的数据
    """

    # type, conditions, vid, time, longitude, latitude, AcX, AcY, AcZ, Gyx, Gyy, Gyz, temp, GForce
    datas[0] = 'normal'
    datas[1] = 'no problem'
    if datas[3] is None:                                    # time
        now = datetime.now()
        datas[3] = now.strftime("%d/%m/%Y %H:%M:%S")

    if datas[6] == '0' or datas[7] == '0' or datas[8] == '0' or datas[2] == '0':
        datas[0] = 'normal'
        datas[1] = '分析数据丢失'
    if float(datas[6]) > 30:                                # AcX
        datas[0] = 'normal'
        datas[1] = '急停'
    if 70 < float(datas[-2]):                               # temp
        datas[0] = 'normal'
        datas[1] = '温度过热'
    if -30 > float(datas[7]) or float(datas[7]) > 30:       # AcY
        datas[0] = 'accident'
        if datas[1] != 'no problem':
            datas[1] += '侧翻'
        datas[1] = '侧翻'
    if 0 < float(datas[-1]) < 0.85:                          # GForce
        datas[0] = 'accident'
        if datas[1] != 'no problem':
            datas[1] += '碰撞'
        datas[1] = '碰撞'
    return datas
