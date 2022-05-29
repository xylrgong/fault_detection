import logging

# 日志格式
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
log = logging.getLogger('fault_detection')


# 数据库配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
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
MYSQL_FORWARD_TABLE_NAME = 'forward'
MYSQL_DEVICE_DETAILS_TABLE_NAME = 'device_details'

MYSQL_READ_FAULT_PERIOD = 5
MYSQL_READ_TOPO_PERIOD = 10

FAULT_NAME_HARDWARE = 'HW'
FAULT_NAME_TRAFFIC = 'TRAFFIC'
FAULT_NAME_PROTOCOL = 'PROTO'
FAULT_NAME_APPLICATION = 'APP'
FAULT_NAME_INTERFACE = 'IF'