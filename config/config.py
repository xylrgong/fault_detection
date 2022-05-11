import logging

# 日志格式
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
log = logging.getLogger('fault_detection')


# 数据库配置
MYSQL_CONFIG = {
    'host': 'localhost',  # server: 192.168.123.233
    'port': 3306,
    'user': 'root',  # test: (archer, archerx) server: (host, 1)
    'password': '1',
    'charset': 'utf8',
    'use_unicode': True,
    'get_warnings': True,
    'auth_plugin': 'mysql_native_password',
    'database': 'hd_server_second'
}

MYSQL_DB_NAME = 'hd_server_second'
MYSQL_FAULT_TABLE_NAME = 'fault'
MYSQL_TOPO_TABLE_NAME = 'topo'

MYSQL_READ_PERIOD = 5