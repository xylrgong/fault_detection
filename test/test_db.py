import logging
import time

import mysql.connector as mysql
import threading
MYSQL_FAULT_TABLE_NAME = 'fault'
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

mutex = threading.Lock()

test_insert_sql = [(0, 'PROTO_STP_STATUS_ERR', 0, '2022-05-06 00:00:00', '1', '(C, 0)', '(InterfaceState.DESIGNATED,InterfaceState.ROOT)', 'severe'),]

sql_insert_test_items = "INSERT INTO {} (id, name, number, time, flag, position, description, level)" \
                        "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)".format(MYSQL_FAULT_TABLE_NAME)
mutex.acquire()
try:
    print("in try")
    conn = mysql.connect(**MYSQL_CONFIG)
    cur = conn.cursor()
    cur.executemany(sql_insert_test_items, test_insert_sql)
    conn.commit()
    print("success")
except:
    print("in except")
    logging.error("!!!!")

for i in range(1, 100000):
    time.sleep(1)
    if i % 100 ==0:
        print(i)
# mutex.release()

