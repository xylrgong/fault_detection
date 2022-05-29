from utils import *
from fault_handler import *
from topo import *
import threading

class FaultMonitor(object):
    def __init__(self):
        self.read_id_num = 1
        self.fault_handled = dict()
        self.fault_key = []
        self.dbif = None
        self.topo = None
        self._work_thread = None
    
    def run(self):
        if not self.dbif:
            self.dbif = DBInterface()
        self.dbif.init()
        # only for testing purposes
        self.dbif.insert_test_items()

        if not self.topo:
            # only for testing purposes
            self.dbif.create_topo_and_insert_test_items()
            topo_res = self.dbif.read_topo()

            device_details = self.dbif.read_device_details()
            self.topo = Topo()
            self.topo.topo_table_construct(topo_res)
        
        self.fault_key = self.dbif.read_table_title()

        threading.Timer(MYSQL_READ_FAULT_PERIOD, self._read_db_and_handle_fault).start()
        threading.Timer(MYSQL_READ_TOPO_PERIOD, self._read_topo_and_update).start()


    def _compare_two_fault(self, fault_obj1, fault_obj2):
        pass
    
    # 将从数据库读到的故障表项list,形如[(fault1),(fault2),...]和表头list,形如['id','name',...]
    # 合并成一个字典的list,形如[(id:"",name:"",...)(id:"",name:""...),...]
    # TODO:这里的函数需要修改，最好挪到类外
    @staticmethod
    def zip_fault_list_to_fault_dict_list(key_list, fault_list):
        fault_dict_list = []
        for fault_item in fault_list:
            to_dict = dict(zip(key_list, fault_item))
            fault_item_dict_ts = trans_fault_dict_from_datetime_to_timestamp(to_dict)
            fault_dict_list.append(fault_item_dict_ts)
        return fault_dict_list

    def _read_db_and_handle_fault(self):
        fault_list_rd_from_db = self.dbif.read_db_by_id(id=self.read_id_num, table_name=MYSQL_FAULT_TABLE_NAME)
        assert self.fault_key
        fault_dict_list = self.zip_fault_list_to_fault_dict_list(self.fault_key, fault_list_rd_from_db)
        print(fault_dict_list)
        line_num = len(fault_dict_list)
        new_fault_cnt = 0
        old_fault_cnt = 0
        handled_fault_cnt = 0
        for fault_dict_item in fault_dict_list:
            # 对于每一个故障表中读取到的表项，构建一个fault类对象
            fault_obj = self.create_fault_obj(fault_dict_item)
            # 未处理过的故障
            if fault_obj not in self.fault_handled.values():
                new_fault_cnt += 1
                # assert fault_obj.fault_hash is not hash((None, None))
                self.fault_handled[fault_obj.fault_hash] = fault_obj
                # TODO: Add method for handling fault range here
                fault_obj.get_range(self.topo, self.dbif)
            # 已经出现过的故障
            else:
                # print(fault_obj)
                # old_fault_obj = self.fault_handled[self.fault_handled.index(fault_obj)]
                old_fault_obj = self.fault_handled[fault_obj.fault_hash]
                if fault_obj.time == old_fault_obj.time:
                     log.info("无新故障产生")
                     break
                old_fault_cnt += 1
                assert fault_obj.flag == str(0)
                assert fault_obj.time > old_fault_obj.time
                # TODO: Add method for lasting time
                log.info("lasting time for fault {}_{} is {}".format(fault_obj.name, fault_obj.number, fault_obj.get_lasting_time(old_fault_obj)))
                handled_fault_cnt += 1
                del self.fault_handled[old_fault_obj.fault_hash]
                # self.fault_handled.remove(old_fault_obj)
                del fault_obj
                del old_fault_obj
        self._update_read_line_num(line_num)
        log.info("出现新故障{}条，解除故障（包含新故障和原有故障）{}条".format(new_fault_cnt, handled_fault_cnt))
        threading.Timer(MYSQL_READ_FAULT_PERIOD, self._read_db_and_handle_fault).start()

    def create_fault_obj(self, fault_dict_item):
        type = re.search('^[A-Z]*', fault_dict_item['name']).group()
        if type == FAULT_NAME_HARDWARE:
            fault_obj = HardwareFault.construct(fault_dict_item)
        elif type == FAULT_NAME_TRAFFIC:
            fault_obj = TrafficFault.construct(fault_dict_item)
        elif type == FAULT_NAME_PROTOCOL:
            fault_obj = ProtocolFault.construct(fault_dict_item)
        elif type == FAULT_NAME_APPLICATION:
            fault_obj = ApplicationFault.construct(fault_dict_item)
        elif type == FAULT_NAME_INTERFACE:
            fault_obj = InterfaceFault.construct(fault_dict_item)
        else:
            log.error("Unknown type fault!")
            fault_obj = BaseFault.construct(fault_dict_item)
        return fault_obj

    def _update_read_line_num(self, add_num):
        self.read_id_num += add_num

    def _read_topo_and_update(self):
        topo_list = self.dbif.read_topo()
        self.topo.topo_table_construct(topo_list)
        log.info("更新系统拓扑图，现拓扑有{}个节点，{}条边".format(self.topo.G.number_of_nodes(), self.topo.G.number_of_edges()))
        print(self.topo.G)
        threading.Timer(MYSQL_READ_TOPO_PERIOD, self._read_topo_and_update).start()