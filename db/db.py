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
                                " level VARCHAR(255),"\
                                "primary key (id))".format(MYSQL_FAULT_TABLE_NAME)
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


    # 仅在测试时使用
    def insert_test_items(self):
        log.info("Insert test items................")
        test_items1 = [(1, 'FL_BLK_HOLE', 0, '2022-05-05 20:27:37', '1', '(aa:bb:cc:dd:ee:ff,AA:BB:CC:DD:EE:FF)', 'normal'), (2, 'FL_BLK_HOLE', 0, '2022-05-05 20:27:44', '0', '(aa:bb:cc:dd:ee:ff,AA:BB:CC:DD:EE:FF)', 'normal'), (3, 'FL_PT_SCAN', 0, '2022-05-05 20:38:22', '1', '(10.0.0.1,8080,10.0.0.2)', 'fatal'), (4, 'FL_PT_SCAN', 0, '2022-05-05 20:41:36', '0', '(10.0.0.1,8080,10.0.0.2)', 'fatal')]
        test_items2 = [(5, 'FL_BLK_HOLE', 1, '2022-05-05 20:37:37', '1', '(aa:bb:cc:dd:ee:ff,AA:BB:CC:DD:EE:FF)', 'normal'), (6, 'FL_BLK_HOLE', 2, '2022-05-05 20:47:44', '1', '(aa:bb:cc:dd:ee:ff,AA:BB:CC:DD:EE:FF)', 'normal'), (7, 'FL_PT_SCAN', 1, '2022-05-05 20:48:22', '1', '(10.0.0.1,8080,10.0.0.2)', 'fatal'), (8, 'FL_PT_SCAN', 1, '2022-05-05 20:51:36', '0', '(10.0.0.1,8080,10.0.0.2)', 'fatal')]
        sql_insert_test_items = "INSERT INTO {} (id, name, number, time, flag, position, level)"\
                                "VALUES(%s, %s, %s, %s, %s, %s, %s)".format(MYSQL_FAULT_TABLE_NAME)
        self._mutex.acquire()
        try:
            self.connect()
            cur = self.dbconn.cursor()
            cur.executemany(sql_insert_test_items, test_items1)
            self.dbconn.commit()
            cur.executemany(sql_insert_test_items, test_items2)
            self.dbconn.commit()
            cur.close()
        except Exception as e:
            log.error(e)
            log.error("Error inserting test fault items")
        finally:
            self._mutex.release()
            self.disconnect()
    
    def create_topo_and_insert_test_items(self):
        conn = mysql.connect(**MYSQL_CONFIG)
        cur = conn.cursor()
        sql_drop_topo_table = "DROP TABLE IF EXISTS {}".format(MYSQL_TOPO_TABLE_NAME)
        cur.execute(sql_drop_topo_table)
        sql_create_topo_table = "CREATE TABLE IF NOT EXISTS {}("\
                                " mac1 VARCHAR(255), "\
                                " mac2 VARCHAR(255),"\
                                " port1 VARCHAR(255),"\
                                " port2 VARCHAR(255))".format(MYSQL_TOPO_TABLE_NAME)
        cur.execute(sql_create_topo_table)
        log.info("Initialize topo table....................")

        test_items = [("t1", "t2", "0", "1"), ("t1", "t4", "1", "2"), ("t2", "t3", "0", "0"), ("t2", "t4", "2", "1"), ("t2", "t5", "3", "0"), ("t4", "t5", "0", "1")]
        sql_insert_test_items = "INSERT INTO {} (mac1, mac2, port1, port2)"\
                                "VALUES(%s, %s, %s, %s)".format(MYSQL_TOPO_TABLE_NAME)
        self._mutex.acquire()
        try:
            self.connect()
            cur = self.dbconn.cursor()
            cur.executemany(sql_insert_test_items, test_items)
            self.dbconn.commit()
        except Exception as e:
            log.error(e)
            log.error("Error inserting test topo items")
        finally:
            self._mutex.release()
            self.disconnect()
        


    def read_db_by_id(self, id=0, table_name=MYSQL_FAULT_TABLE_NAME):
        self._mutex.acquire()
        try:
            self.connect()
            cur = self.dbconn.cursor()
            sql_read_db_by_id = "SELECT * FROM {} WHERE id>={} and id<=(SELECT ceiling(count(*)) from fault)".format(table_name, id)
            cur.execute(sql_read_db_by_id)
            fault_list = cur.fetchall()
            cur.close()
        except Exception as e:
            log.error(e)
            log.error("Error reading fault table")
        finally:
            self._mutex.release()
            self.disconnect()
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



if __name__ == "__main__":
    db = DBInterface()
    db.init()
    db.insert_test_items()
    db.create_topo_and_insert_test_items()
    res = db.read_db_by_id(2, 'fault')
    print(res)






