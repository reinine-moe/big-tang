# 部署文档
**时间：2023-06-14**

**负责人：深圳职业技术学院 - 激流勇进 - 叶兆杰**

### 项目目录

```
📁python server
├─ 📄README.md
├─ 📄requirement.txt
├─ 📄runserver.py                     # 项目启动文件
├─ 📁.idea
├─ 📁src
│  ├─ 📄config.ini                    # 项目配置文件
│  ├─ 📄save_sql.py                   # 操作数据库
│  ├─ 📄socket_connect.py             # 接收正常车的TCP连接
│  ├─ 📄util.py                       # 存放可复用代码及工具
│  ├─ 📄view.py                       # 视图组件
│  └─ 📁__pycache__
└─ 📁venv
```

### 开发环境
pycharm下载：[PyCharm - The Python IDE
for Professional Developers](https://www.jetbrains.com/pycharm/download/)

python下载：[Download Python | Python.org](https://www.python.org/downloads/)

| 解释器    |  版本   |
|--------|:-----:|
| python | v3.11 |

| IDE     |               版本                |
|---------|:-------------------------------:|
| PyCharm | v2022.3.3<br>Community Edition  |

**项目框架：**

| 框架    |    版本     |
|-------|:---------:|
| Flask | == v2.3.2 |

**第三方库：**

|     外部库      |     版本     |
|:------------:|:----------:|
|    Flask     | == v2.3.2  |
|  Flask-Cors  | == v3.0.10 |
|   PyMySQL    | == v1.0.3  |

### 启动项目

`$ cd Project/` - 进入项目根目录

`$ pip install -r requirement.txt` - 导入第三方库

`$ vim ./src/config.ini` - 更改项目配置文件

`$ python ./runserver.py` - 启动项目

