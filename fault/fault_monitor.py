from fault_handler import *
from fault_range import *
from topo.topo import *
from fastapi import Request
import threading


class FaultMonitor(object):

    def __call__(self, request: Request):
        request.state.fault_range = self.fault_range.get_full_range()

    def __init__(self):
        self.read_id_num = 1
        self.fault_handled = dict()
        self.fault_key = []
        self.dbif = None
        self.topo = None
        self.fault_range = None
        self._work_thread = None
        self.run()

    def run(self):
        if not self.dbif:
            self.dbif = DBInterface()
        self.dbif.init()
        # only for testing purposes
        self.dbif.insert_test_items()

        if not self.fault_range:
            self.fault_range = FaultRange()

        if not self.topo:
            # only for testing purposes
            self.dbif.create_topo_and_insert_test_items()
            topo_res = self.dbif.read_topo()
            forward_res = self.dbif.read_forward()
            device_details = self.dbif.read_device_details()
            self.topo = Topo()
            self.topo.init_node(device_details_list=device_details, forward_list=forward_res)
            self.topo.topo_table_construct(topo_res)

        self.fault_key = self.dbif.read_table_title()

        threading.Timer(MYSQL_READ_FAULT_PERIOD, self._read_db_and_handle_fault).start()
        threading.Timer(MYSQL_READ_TOPO_PERIOD, self._read_topo_and_update).start()

    def _compare_two_fault(self, fault_obj1, fault_obj2):
        pass

    @staticmethod
    def create_fault_obj(fault_dict_item):
        keyword = re.search('^[A-Z]*', fault_dict_item['name']).group()
        fault_cls = FAULT_NAME_TO_CLASS[keyword]
        fault_obj = eval(fault_cls)(fault_dict_item)
        return fault_obj

    # 将从数据库读到的故障表项list,形如[(fault1),(fault2),...]和表头list,形如['id','name',...]
    # 合并成一个字典的list,形如[(id:"",name:"",...)(id:"",name:""...),...]
    @staticmethod
    def zip_fault_list_to_fault_dict_list(key_list, fault_list):
        fault_dict_list = []
        for fault_item in fault_list:
            to_dict = dict(zip(key_list, fault_item))
            fault_item_dict_ts = trans_fault_dict_from_datetime_to_timestamp(to_dict)
            fault_dict_list.append(fault_item_dict_ts)
        return fault_dict_list

    def _update_fault(self, new_fault:BaseFault):
        pass


    def _read_db_and_handle_fault(self):
        fault_list_rd_from_db = self.dbif.read_db_by_id(id=self.read_id_num, table_name=MYSQL_FAULT_TABLE_NAME)
        assert self.fault_key
        fault_dict_list = self.zip_fault_list_to_fault_dict_list(self.fault_key, fault_list_rd_from_db)
        print(fault_dict_list)
        line_num = len(fault_dict_list)
        new_fault_cnt = 0
        handled_fault_cnt = 0
        for fault_dict_item in fault_dict_list:
            # 对于每一个故障表中读取到的表项，构建一个fault类对象
            fault_obj = self.create_fault_obj(fault_dict_item)
            # 未处理过的故障
            if fault_obj not in self.fault_handled.values():
                new_fault_cnt += 1
                # assert fault_obj.fault_hash is not hash((None, None))
                self.fault_handled[fault_obj.fault_hash] = fault_obj
                self._handle_fault_range(fault_obj)
            # 已经出现过的故障
            else:
                old_fault_obj = self.fault_handled[fault_obj.fault_hash]
                if fault_obj.time == old_fault_obj.time:
                    log.info("无新故障产生")
                    break

                # assert fault_obj.flag == str(0)
                if fault_obj.flag == str(0):  # 旧故障被解决
                    assert fault_obj.time > old_fault_obj.time
                    # TODO: Add method for lasting time
                    log.info("lasting time for fault {}_{} is {}".format(fault_obj.name, fault_obj.number,
                                                                         fault_obj.get_lasting_time(old_fault_obj)))
                    handled_fault_cnt += 1
                    del self.fault_handled[old_fault_obj.fault_hash]

                    # self.fault_handled.remove(old_fault_obj)
                else:  # 旧故障升级/降级
                    assert fault_obj.level != old_fault_obj.level
                    if SEVERITY[fault_obj.level] < SEVERITY[old_fault_obj.level]:
                        log.warning("旧故障{}升级".format(old_fault_obj))
                    else:
                        log.warning("旧故障{}降级".format(old_fault_obj))
                    self._handle_fault_range(fault_obj)
                del fault_obj
                del old_fault_obj
        self._update_read_line_num(line_num)
        log.info("出现新故障{}条，解除故障（包含新故障和原有故障）{}条".format(new_fault_cnt, handled_fault_cnt))
        threading.Timer(MYSQL_READ_FAULT_PERIOD, self._read_db_and_handle_fault).start()

    def _handle_fault_range(self, fault_obj):
        fault_obj.get_range(self.topo, self.dbif, self.fault_range)
        fault_obj.get_error()
        if isinstance(fault_obj, TrafficFault):
            self.fault_range.traffic_range.update(fault_obj.range)
        elif isinstance(fault_obj, HardwareFault):
            self.fault_range.hw_range.update(fault_obj.range)
        elif isinstance(fault_obj, ProtocolFault):
            self.fault_range.proto_range.update(fault_obj.range)
        elif isinstance(fault_obj, ApplicationFault):
            self.fault_range.app_range.update(fault_obj.range)
        elif isinstance(fault_obj, InterfaceFault):
            self.fault_range.if_range.update(fault_obj.range)
        self.fault_range.errors.update(fault_obj.error)

    def _update_read_line_num(self, add_num):
        self.read_id_num += add_num

    def _read_topo_and_update(self):
        topo_list = self.dbif.read_topo()
        self.topo.topo_table_construct(topo_list)
        log.info("更新系统拓扑图，现拓扑有{}个节点，{}条边".format(self.topo.G.number_of_nodes(), self.topo.G.number_of_edges()))
        print(self.topo.G)
        threading.Timer(MYSQL_READ_TOPO_PERIOD, self._read_topo_and_update).start()
