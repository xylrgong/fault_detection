import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))
from config.config import *
import mysql.connector as mysql
import threading

class DBInterface(object):
    def __init__(self):
        self.dbconn = None
        self._mutex = threading.Lock()
    
    def init(self):
        log.info("Initialize datebase................")
        conn = mysql.connect(**MYSQL_CONFIG)
        cur = conn.cursor()

        sql_create_db = 'CREATE DATABASE IF NOT EXISTS {}'.format(MYSQL_DB_NAME)
        cur.execute(sql_create_db)
        log.info("Create database:" + MYSQL_DB_NAME)

        conn.cmd_init_db(MYSQL_DB_NAME)

        # 创建故障表
        sql_drop_fault_table = "DROP TABLE IF EXISTS {}".format(MYSQL_FAULT_TABLE_NAME)
        cur.execute(sql_drop_fault_table)
        sql_create_fault_table = "CREATE TABLE IF NOT EXISTS {}("\
                                " id INT UNSIGNED NOT NULL AUTO_INCREMENT, "\
                                " name VARCHAR(255),"\
                                " number INT,"\
                                " time datetime,"\
                                " flag VARCHAR(255),"\
                                " position VARCHAR(255),"\
                                " scope VARCHAR(255),"\
                                " level VARCHAR(255),"\
                                " primary key (id))".format(MYSQL_FAULT_TABLE_NAME)
        cur.execute(sql_create_fault_table)
        log.info("Initialize fault table....................")
        cur.close()
        conn.disconnect()

    def connect(self):
        if not self.dbconn:
            log.info('Trying to connect to database (addr:{}:{}, user:{})'.format(
                MYSQL_CONFIG['host'], MYSQL_CONFIG['port'], MYSQL_CONFIG['user']))
            self.dbconn = mysql.connect(**MYSQL_CONFIG)
        if not self.dbconn.is_connected():
            log.info('Reconnect to database(addr:{}:{}, user:{})'.format(
                MYSQL_CONFIG['host'], MYSQL_CONFIG['port'], MYSQL_CONFIG['user']))
            self.dbconn.reconnect()
            self.dbconn.cmd_init_db(MYSQL_DB_NAME)

    def disconnect(self):
        if self.dbconn:
            log.info('Disconnect to database (addr:{}:{}, user:{})'.format(
                MYSQL_CONFIG['host'], MYSQL_CONFIG['port'], MYSQL_CONFIG['user']))
            self.dbconn.disconnect()

    def mysql_query(self, query):
        self._mutex.acquire()
        try:
            self.connect()
            cur = self.dbconn.cursor()
            cur.execute(query)
            result = cur.fetchall()
            cur.close()
        except Exception as e:
            log.error(e)
            log.error("Error when do " + query)
        finally:
            self._mutex.release()
            return result

    def mysql_insert_many(self, insert_sql, insert_items:list):
        self._mutex.acquire()
        try:
            self.connect()
            cur = self.dbconn.cursor()
            cur.executemany(insert_sql, insert_items)
            self.dbconn.commit()
        except Exception as e:
            log.error(e)
            log.error("Error when do" + insert_sql)
        finally:
            self._mutex.release()


    # 仅在测试时使用
    def insert_test_items(self):
        log.info("Insert test items................")
        test_items1 = [(1, 'TRAFFIC_BLK_HOLE', 0, '2022-05-05 20:27:37', '1', '(A,B)','A,B', 'normal'), (2, 'TRAFFIC_BLK_HOLE', 0, '2022-05-05 20:27:44', '0', '(A,B)','A,B', 'normal'), (3, 'TRAFFIC_PT_SCAN', 0, '2022-05-05 20:38:22', '1', '(A,B)','A,B', 'fatal'), (4, 'TRAFFIC_PT_SCAN', 0, '2022-05-05 20:41:36', '0', '(A,B)','A,B', 'fatal')]
        test_items2 = [(5, 'TRAFFIC_BLK_HOLE', 1, '2022-05-05 20:37:37', '1', '(A,B)','A,B', 'normal'), (6, 'TRAFFIC_BLK_HOLE', 2, '2022-05-05 20:47:44', '1', '(A,B)','A,B', 'normal'), (7, 'TRAFFIC_PT_SCAN', 1, '2022-05-05 20:48:22', '1', '(B,D)','B,D', 'fatal'), (8, 'TRAFFIC_PT_SCAN', 1, '2022-05-05 20:51:36', '0', '(B,D)','B,D', 'fatal')]
        test_items3 = [(9, 'APP_MAL_FUNC', 0, '2022-05-06 00:00:00', '1', 'E', '', 'normal'), (10, 'HW_SW_OFFLINE', 0, '2022-05-06 01:00:00', '1', 'D', '', 'fatal')]
        test_items = test_items1 + test_items2 + test_items3
        sql_insert_test_items = "INSERT INTO {} (id, name, number, time, flag, position, scope, level)"\
                                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)".format(MYSQL_FAULT_TABLE_NAME)
        self.mysql_insert_many(sql_insert_test_items, test_items)
    
    def create_topo_and_insert_test_items(self):
        conn = mysql.connect(**MYSQL_CONFIG)
        cur = conn.cursor()
        '''
        sql_drop_topo_table = "DROP TABLE IF EXISTS {}".format(MYSQL_TOPO_TABLE_NAME)
        cur.execute(sql_drop_topo_table)
        '''
        sql_create_topo_table = "CREATE TABLE IF NOT EXISTS {}("\
                                " mac1 VARCHAR(255), "\
                                " mac2 VARCHAR(255),"\
                                " port1 VARCHAR(255),"\
                                " port2 VARCHAR(255))".format(MYSQL_TOPO_TABLE_NAME)
        cur.execute(sql_create_topo_table)
        log.info("Initialize topo table....................")

        '''
        test_items = [("t1", "t2", "0", "1"), ("t1", "t4", "1", "2"), ("t2", "t3", "0", "0"), ("t2", "t4", "2", "1"), ("t2", "t5", "3", "0"), ("t4", "t5", "0", "1"), ("h1", "t1", "0", "2"), ("h2", "t5", "0", "3")]
        sql_insert_test_items = "INSERT INTO {} (mac1, mac2, port1, port2)"\
                                "VALUES(%s, %s, %s, %s)".format(MYSQL_TOPO_TABLE_NAME)
        self.mysql_insert_many(sql_insert_test_items, test_items)
        '''

    def create_forward_table_and_insert_items(self):
        conn = mysql.connect(**MYSQL_CONFIG)
        cur = conn.cursor()
        sql_drop_forward_table = "DROP TABLE IF EXISTS {}".format(MYSQL_FORWARD_TABLE_NAME)
        cur.execute(sql_drop_forward_table)
        sql_create_forward_table = "CREATE TABLE IF NOT EXISTS {}(" \
                                " vlan_id INT, " \
                                " type VARCHAR(255)," \
                                " device_mac VARCHAR(255)," \
                                " dst_mac VARCHAR(255),"\
                                " outport INT)".format(MYSQL_FORWARD_TABLE_NAME)
        cur.execute(sql_create_forward_table)
        log.info("Initialize forward table....................")

        test_items = [(1, "dynamic", "A", "F", 1), (1, "dynamic", "A", "G", 1), (1, "dynamic", "A", "E", 2), (1, "dynamic", "D", "H", 3), (1, "dynamic", "D", "F", 5), (1, "dynamic", "C", "H", 1), (1, "dynamic", "B", "G", 1)]
        sql_insert_test_items = "INSERT INTO {} (vlan_id, type, device_mac, dst_mac, outport)" \
                                "VALUES(%s, %s, %s, %s, %s)".format(MYSQL_FORWARD_TABLE_NAME)
        self.mysql_insert_many(sql_insert_test_items, test_items)

    def read_db_by_id(self, id=0, table_name=MYSQL_FAULT_TABLE_NAME):
        sql_read_db_by_id = "SELECT * FROM {} WHERE id>={} and id<=(SELECT ceiling(count(*)) from fault)".format(table_name, id)
        fault_list = self.mysql_query(query=sql_read_db_by_id)
        return fault_list

    def read_table_title(self, table_name=MYSQL_FAULT_TABLE_NAME):
        self._mutex.acquire()
        try:
            self.connect()
            cur = self.dbconn.cursor()
            sql_read_table_title = "SELECT * FROM {}".format(table_name)
            cur.execute(sql_read_table_title)
            cur.fetchall()
            raw_title = list(cur.description)
            title = [item[0] for item in raw_title]
            cur.close()
        except Exception as e:
            log.error(e)
            log.error("Error reading fault table title")
        finally:
            self._mutex.release()
            self.disconnect()
            return title

    def read_topo(self):
        sql_read_topo = "SELECT * FROM {}".format(MYSQL_TOPO_TABLE_NAME)
        topo_list = self.mysql_query(sql_read_topo)
        return topo_list

    def read_device_details(self):
        sql_read_device = "SELECT  mac, device_name, ip, type FROM {}".format(MYSQL_DEVICE_DETAILS_TABLE_NAME)
        device_details_list = self.mysql_query(sql_read_device)
        return device_details_list

    def read_forward(self):
        sql_read_forward = "SELECT device_mac, dst_mac, outport FROM {}".format(MYSQL_FORWARD_TABLE_NAME)
        forward_list = self.mysql_query(sql_read_forward)
        return forward_list

    def read_forward_by_dev_and_dst(self, dev_mac, outport):
        sql_read_dst_mac = "SELECT dst_mac FROM forward WHERE outport={} AND device_mac='{}';".format(outport, dev_mac)
        dst_mac = self.mysql_query(sql_read_dst_mac)
        return dst_mac

if __name__ == "__main__":
    db = DBInterface()
    db.init()
    db.insert_test_items()
    db.create_topo_and_insert_test_items()
    db.create_forward_table_and_insert_items()
    res = db.read_db_by_id(2, 'fault')
    topo_res = db.read_topo()
    device_details_res = db.read_device_details()
    print(res)
    print(topo_res)
    print(device_details_res)
