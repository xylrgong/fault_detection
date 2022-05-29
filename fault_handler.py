from utils import *

class BaseFault():

    def __init__(self, id=-1, name=None, number=None, time=-1, flag=-1, position=None, scope=None, level=None):
        self.fault_hash = hash((name, number))
        self.id = id
        self.name = name
        self.number = number
        self.time = time
        self.flag = flag
        self.position = position
        self.scope = scope
        self.level = level
    
    # def __del__(self):
    #     print("Delete" + " " + str(self.name) + "_" + str(self.number) + " id:" + str(self.id))

    def __eq__(self, other):
        return self.name == other.name and self.number == other.number

    def __gt__(self, other):
        assert isinstance(other,BaseFault)
        return self.time > other.time and self==other

    def __hash__(self):
        if not self.fault_hash:
            self.fault_hash = hash((self.name, self.number))
        return self.fault_hash

    def __str__(self):
        return "Fault id:" + str(self.id) + " and fault name: " + str(self.name) + " " + "and fault number: " + str(self.number) + " and flag: " + str(self.flag)

    def get_key(self):
        assert self.name is not None and self.number is not None
        return str(self.name) + str(self.number)

    @staticmethod
    def construct(fault_item):
        return BaseFault(fault_item['id'],fault_item['name'], fault_item['number'],fault_item['time'],
        fault_item['flag'],fault_item['position'],fault_item['scope'], fault_item['level'])

    def get_range(self, topo, dbif):
        pass
        # if re.findall('FL_', self.name):
        #     self.get_flow_range(topo, dbif)
        # if re.findall('APP_', self.name):
        #     pass
        # if re.findall('HDR_', self.name):
        #     pass
            # target = topo.find_node_by_attr('mac', self.position)
            # node = [l.mac for l in topo.G.neighbors(target)]
            # print("出现一条硬件故障，该故障名称为{},影响范围为若干交换机,为{}，该故障还可能会引起端主机的应用故障，端主机MAC为t3".format(self.name, str(node)))


    def get_lasting_time(self, old):
        assert isinstance(old, BaseFault)
        return str(self.time - old.time)

    def format_output(self, loc=None, fault=None, app=None, proto=None, flow=None, hdr=None):
        # fault = "FL_BLK_HOLE"
        # loc = "(AA:BB:CC:DD:EE:FF->aa:bb:cc:dd:ee:ff)"
        # app = "Any Active Application in (T1, T3)"
        # proto = "STP failure in (S3, S4)"
        # flow = "Flow disappear in switch:(S3, S4)\n\t\t\tAffect server in (T1, T3, T5)"
        print("************************************************************************")
        print("*" + '{:^67}'.format('出现故障：'+'{}'.format(str(fault))) + '*')
        print("*" + '{:^67}'.format('发生位置：'+'{}'.format(str(loc))) + '*')
        print("************************************************************************")
        print("-" + '应用层面影响：'+str(app))
        print("-" + '协议层面影响：'+str(proto))
        print("-" + '流量层面影响：'+str(flow))
        print("-" + '硬件层面影响：'+str(hdr))
        print("************************************************************************")


class TrafficFault(BaseFault):

    @staticmethod
    def construct(fault_item):
        return TrafficFault(fault_item['id'],fault_item['name'], fault_item['number'],fault_item['time'],
        fault_item['flag'],fault_item['position'],fault_item['scope'], fault_item['level'])


    def get_range(self, topo, dbif):
        if self.name == "TRAFFIC_BLK_HOLE":
            # self.position be like (mac1, mac2), need to find the outport of mac1 to mac2
            # 计算流量影响范围
            index = del_brackets(self.position)
            index_src = index[0]
            index_dst = index[1]
            outport = topo.topo_table[index_src, index_dst]
            server_affected = dbif.read_forward_by_dev_and_dst(dev_mac=index_src, outport=outport)
            server_affected = [mac[0] for mac in server_affected]
            switch_affected = index
            flow_range_str = "交换机："+ str(switch_affected) + "\t服务器：" + str(server_affected)

            # 计算应用影响范围
            app_range_str = "所有" + str(server_affected) + "上的应用"

            #计算协议影响范围
            self.format_output(loc=str(self.position), \
                               fault=self.name, \
                               app=app_range_str, \
                               flow=flow_range_str)


class ApplicationFault(BaseFault):

    @staticmethod
    def construct(fault_item):
        return ApplicationFault(fault_item['id'],fault_item['name'], fault_item['number'],fault_item['time'],
                            fault_item['flag'],fault_item['position'],fault_item['scope'], fault_item['level'])


class InterfaceFault(BaseFault):

    @staticmethod
    def construct(fault_item):
        return InterfaceFault(fault_item['id'],fault_item['name'], fault_item['number'],fault_item['time'],
                            fault_item['flag'],fault_item['position'],fault_item['scope'], fault_item['level'])


class HardwareFault(BaseFault):

    @staticmethod
    def construct(fault_item):
        return HardwareFault(fault_item['id'],fault_item['name'], fault_item['number'],fault_item['time'],
                            fault_item['flag'],fault_item['position'],fault_item['scope'], fault_item['level'])


class ProtocolFault(BaseFault):

    @staticmethod
    def construct(fault_item):
        return ProtocolFault(fault_item['id'],fault_item['name'], fault_item['number'],fault_item['time'],
                            fault_item['flag'],fault_item['position'],fault_item['scope'], fault_item['level'])


if __name__ == '__main__':
    test_print = BaseFault()
    test_print.format_output()
