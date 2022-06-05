from utils.utils import *
from config.config import *
from topo.topo import Topo
from db.db import DBInterface
from fault.fault_range import FaultRange


class BaseFault():

    def __init__(self, fault_item=None):
        if fault_item is None:
            fault_item = {
                k: None for k in ['id', 'number', 'name', 'time', 'flag', 'position', 'description', 'level']
            }
        self.fault_hash = str(hash((fault_item['id'], fault_item['number'])))
        self.id = fault_item['id']
        self.name = fault_item['name']
        self.number = fault_item['number']
        self.time = fault_item['time']
        self.flag = fault_item['flag']
        self.position = fault_item['position']
        self.description = fault_item['description']
        self.level = fault_item['level']
        if not hasattr(self, 'classification'):
            self.classification = None
        self.range = None
        self.error = None

    # def __del__(self):
    #     print("Delete" + " " + str(self.name) + "_" + str(self.number) + " id:" + str(self.id))

    def __eq__(self, other):
        return self.name == other.name and self.number == other.number

    def __hash__(self):
        if not self.fault_hash:
            self.fault_hash = hash((self.name, self.number))
        return self.fault_hash

    def __str__(self):
        return "Fault id:" + str(self.id) + " and fault name: " + str(self.name) + " " + "and fault number: " + str(
            self.number) + " and flag: " + str(self.flag)

    def get_key(self):
        assert self.name is not None and self.number is not None
        return str(self.name) + str(self.number)

    def get_range(self, topo: Topo, dbif: DBInterface, fault_range: FaultRange):
        pass

    def get_error(self):
        self.error = {
            self.fault_hash:{
                "type": self.classification,
                "code": self.name,
                "name": FAULT_DESC_TABLE[self.name],
                "level": SEVERITY[self.level],
                "time": self.time
            }
        }

    def get_lasting_time(self, old):
        assert isinstance(old, BaseFault)
        return str(self.time - old.time)

    def format_output(self, loc=None, fault=None, app=None, proto=None, flow=None, hdr=None):
        print("************************************************************************")
        print("*" + '{:^67}'.format('出现故障：' + '{}'.format(str(fault))) + '*')
        print("*" + '{:^67}'.format('发生位置：' + '{}'.format(str(loc))) + '*')
        print("************************************************************************")
        print("-" + '应用层面影响：' + str(app))
        print("-" + '协议层面影响：' + str(proto))
        print("-" + '流量层面影响：' + str(flow))
        print("-" + '硬件层面影响：' + str(hdr))
        print("************************************************************************")


class TrafficFault(BaseFault):

    classification = '流量故障'

    def get_range(self, topo: Topo, dbif: DBInterface, fault_range: FaultRange):

        if self.name == FAULT_TRAFFIC_BLACK_HOLE:
            '''
            故障名称：路由黑洞	
            故障描述：某两台交换机之间发生路由黑洞，导致流量从一端进入，经过一系列交换机之后流量在出口端消失
            故障表description字段：null
                                可通过position字段推导得出
            故障表position字段：(MAC1, MAC2, ..., MACn)
                              其中，MAC1表示路由黑洞交换机开始的MAC地址，MACn表示结束地址，中间是流量经过的交换机
            故障范围计算：devices:MAC1以及MACn为severe，中间节点以及MACn可达的端节点为moderate
                       links：由MAC1->MAC2->...->MACn的链路为severe
            返回前端的描述信息：
            '''
            
            pos = transfer_bracket_str_to_list(self.position)
            in_mac = pos[0]
            in_name = topo.mac_name_table[in_mac]
            in_port = topo.G_MAC[in_mac][pos[1]]['port']
            out_mac = pos[-1]
            out_name = topo.mac_name_table[out_mac]
            out_port = topo.G_MAC[out_mac][pos[-2]]['port']

            mid_mac = pos[1:-1]  # mid_mac在len(pos)>2的条件下不为空
            desc_in_mac = ['发生路由黑洞', '入口位置：{}的{}端口'.format(in_name, in_port)]
            desc_out_mac = ['发生路由黑洞', '出口位置：{}的{}端口'.format(out_name, out_port)]
            desc_mid_mac = ['处于路由黑洞的链路中']

            # affected_server_mac_list contains leaf node that out_mac can reach
            # list be like [[mac1, mac2], [mac3], [mac4, mac5]]
            # affected_server_mac_list_raw = [mac_list for mac_list in topo.node_table[out_mac].reach_node.values()]
            # affected_server_mac_list = []
            # # get affected leaf node like [mac1, mac2, ...]
            # [affected_server_mac_list.append(item) for element in affected_server_mac_list_raw for item in element]
            desc_leaf_node = ['由于{}与{}之间的路由黑洞，通讯可能受阻'.format(in_name, out_name)]
            out_mac_reach_node_list = topo.node_table[out_mac].reach_node_list

            # generate device_list here
            device_list = []
            device_list.append(get_device_list_item(in_mac, self.level, desc_in_mac))
            device_list.append(get_device_list_item(out_mac, self.level, desc_out_mac))
            if mid_mac is not None:
                [device_list.append(get_device_list_item(i, LEVEL_MODERATE, desc_mid_mac)) for i in mid_mac]
            if out_mac_reach_node_list is not None:
                [device_list.append(get_device_list_item(i, LEVEL_MODERATE, desc_leaf_node)) for i in
                 out_mac_reach_node_list]

            # generate link_list here
            desc_link = ['路由黑洞链路']
            link_list = []
            for i in range(len(pos) - 1):
                link_list.append(get_link_list_item([pos[i], pos[i+1]], self.level, desc_link))
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_TRAFFIC_PACKET_LOSS:
            '''
            故障名称：大量丢包	
            故障描述：某两台交换机之间发生大量丢包，导致流量从一端进入，经过一系列交换机之后流量在出口端大量丢失
            故障表description字段：(A, B)
                                A表示该链路上理论应该传送A字节
                                B表示该链路丢包率
            故障表position字段：(MAC1, MAC2, ..., MACn)
                              其中，MAC1表示路由大量丢包开始的MAC地址，MACn表示结束地址，中间是流量经过的交换机
            故障范围计算：devices:MAC1以及MACn为severe，中间节点以及MACn可达的端节点为moderate
                       links：由MAC1->MAC2->...->MACn的链路为severe
            返回前端的描述信息：
            '''
            
            # 丢包率
            pkt_loss_rate = get_bracket_str_by_sub(self.description, 1)
            pos = transfer_bracket_str_to_list(self.position)
            in_mac = pos[0]
            in_port = topo.G_MAC[in_mac][pos[1]]['port']

            out_mac = pos[-1]
            out_port = topo.G_MAC[out_mac][pos[-2]]['port']

            mid_mac = pos[1:-1]  # mid_mac在len(pos)>2的条件下不为空
            desc_in_mac = ['发生大量丢包', '入口位置：{}的{}端口'.format(topo.mac_name_table[in_mac], in_port), '丢包率：{}'.format(pkt_loss_rate)]
            desc_out_mac = ['发生大量丢包', '出口位置：{}的{}端口'.format(topo.mac_name_table[out_mac], out_port), '丢包率：{}'.format(pkt_loss_rate)]
            desc_mid_mac = ['处于大量丢包的链路中', '丢包率：{}'.format(pkt_loss_rate)]

            # affected_server_mac_list contains leaf node that out_mac can reach
            # list be like [[mac1, mac2], [mac3], [mac4, mac5]]
            affected_server_mac_list_raw = [mac_list for mac_list in topo.node_table[out_mac].reach_node.values()]
            affected_server_mac_list = []
            # get affected leaf node like [mac1, mac2, ...]
            [affected_server_mac_list.append(item) for element in affected_server_mac_list_raw for item in element]
            desc_leaf_node = ['由于{}与{}之间大量丢包，通讯可能受阻'.format(topo.mac_name_table[in_mac], topo.mac_name_table[out_mac])]

            # generate device_list here
            device_list = []
            device_list.append(get_device_list_item(in_mac, self.level, desc_in_mac))
            device_list.append(get_device_list_item(out_mac, self.level, desc_out_mac))
            if mid_mac is not None:
                [device_list.append(get_device_list_item(i, self.level, desc_mid_mac)) for i in mid_mac]
            if affected_server_mac_list is not None:
                [device_list.append(get_device_list_item(i, self.level, desc_leaf_node)) for i in
                 affected_server_mac_list]

            # generate link_list here
            desc_link = ['链路大量丢包，丢包率为{}'.format(pkt_loss_rate)]
            link_list = []
            for i in range(len(pos) - 1):
                link_list.append(get_link_list_item([pos[i], pos[i + 1]], self.level, desc_link))
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_TRAFFIC_PORT_SCAN:
            '''
            故障名称：端口扫描	
            故障描述：某两台端主机之间发生端口扫描
            故障表description字段：percentage
                                表示异常端口占比
            故障表position字段：(IP1, IP2)
                              表示IP1所在主机向IP2所在主机发起端口扫描
            故障范围计算：devices: IP1和IP2所在主机
                       links: 无
            返回前端的描述信息：
            '''

            ip1 = get_bracket_str_by_sub(self.position, 0)
            ip2 = get_bracket_str_by_sub(self.position, 1)
            percentage = self.description
            mac1 = [node for node in topo.node_table.values() if node.ip == ip1][0].mac
            mac2 = [node for node in topo.node_table.values() if node.ip == ip2][0].mac
            desc_mac1 = ['向{}设备发送端口扫描'.format(topo.mac_name_table[mac2])]
            desc_mac2 = ['被{}设备进行端口扫描'.format(topo.mac_name_table[mac1]), '异常端口占比达到{}'.format(percentage)]

            # generate device_list here
            device_list = []
            device_list.append(get_device_list_item(mac1, self.level, desc_mac1))
            device_list.append(get_device_list_item(mac2, self.level, desc_mac2))

            link_list = []
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_TRAFFIC_LOAD_BURST:
            '''
            故障名称：负载激增	
            故障描述：某两台交换机之间流量负载激增，且影响中间一系列交换机
            故障表description字段：amount
                                表示负载激增量，字节/秒
            故障表position字段：(MAC1, MAC2, ..., MACn)
                              MAC1->MAC2->...->MACn之间负载激增
            故障范围计算：devices: MAC1, MAC2, ..., MACn
                       links: MAC1->MAC2->...->MACn
            返回前端的描述信息：
            '''
            
            pos = transfer_bracket_str_to_list(self.position)
            amount = self.description
            desc_mac = ['链路激增节点']
            # generate device_list here
            device_list = []
            [device_list.append(get_device_list_item(mac, self.level, desc_mac)) for mac in pos]

            # generate link_list here
            desc_link = ['链路负载激增', '增加量：{}B/s'.format(amount)]
            link_list = []
            for i in range(len(pos) - 1):
                link_list.append(get_link_list_item([pos[i], pos[i + 1]], self.level, desc_link))
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_TRAFFIC_BROADCAST_STORM:
            '''
            故障名称：广播风暴
            故障描述：网络中出现广播风暴
            故障表description字段：Percentage
                                Percentage表示故障主机发送的ARP风暴包占ARP总数的百分比
            故障表position字段：(MAC1)
                              MAC1主机发送的ARP风暴包占ARP总数的百分比最多
            故障范围计算：devices: 所有的节点，其中MAC1是severe，其余为moderate
                       links: 所有的链路
            返回前端的描述信息：
            '''

            
            severe_mac = get_bracket_str_by_sub(self.position, 0)
            other_mac_list = [mac for mac in topo.node_table.keys() if mac != severe_mac]
            percentage = self.description
            desc_severe = ['网络发生广播风暴', '节点{}发送的ARP包占比最大，为{}'.format(topo.mac_name_table[severe_mac], percentage)]
            desc_other = ['网络风暴节点']

            device_list = []
            device_list.append(get_device_list_item(severe_mac, self.level, desc_severe))
            [device_list.append(get_device_list_item(i, LEVEL_MODERATE, desc_other)) for i in other_mac_list]

            link_list = []
            desc_link = ['网络风暴链路']
            links = topo.G_MAC.to_undirected().edges
            [link_list.append(get_link_list_item(node_pair, self.level, desc_link)) for node_pair in links]

            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_TRAFFIC_STP_CIRCLE:
            '''
            故障名称：转发环路
            故障描述：网络中出现转发环路
            故障表description字段：null
                                无
            故障表position字段：(MAC1, MAC2, ..., MACn)
                              这些MAC可能不两两相邻但整体能组成环路
            故障范围计算：devices: MAC1, MAC2, ..., MACn
                       links: 由这些设备组成的环路
            返回前端的描述信息：
            '''
            
            mac_list = transfer_bracket_str_to_list(self.position)
            desc_mac = ['转发环路节点']
            device_list = []
            [device_list.append(get_device_list_item(mac, self.level, desc_mac)) for mac in mac_list]

            desc_link = ['转发环路链路']
            links = topo.G_MAC.to_undirected().edges
            link_list = []
            # TODO: 检查这里的逻辑，若有多个环？
            for i in range(len(mac_list) - 1):
                for j in range(i+1, len(mac_list)):
                    pair = (mac_list[i], mac_list[j])
                    if pair in links:
                        link_list.append(get_link_list_item(pair, self.level, desc_link))
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)


class ApplicationFault(BaseFault):

    classification = '应用故障'

    def get_range_for_two_leaf_node(self, mac1: str, mac2:str, desc1: list[str], desc2: list[str]):
        
        device_list = []
        action = self.description
        if action != '':
            action = '连接行为：' + action
            desc1.append(action)
            desc2.append(action)
        device_list.append(get_device_list_item(mac1, self.level, desc1))
        device_list.append(get_device_list_item(mac2, self.level, desc2))

        link_list = []
        self.range = zip_fault_range(device_list, link_list, self.fault_hash)
        print(self.range)

    def get_range_fail(self, topo:Topo):
        mac1 = get_bracket_str_by_sub(self.position, 0)
        mac2 = get_bracket_str_by_sub(self.position, 1)
        desc_mac1 = ['向{}发送连接请求，但失败'.format(topo.mac_name_table[mac2])]
        desc_mac2 = ['无法成功回应{}发起的连接请求'.format(topo.mac_name_table[mac1])]
        self.get_range_for_two_leaf_node(mac1, mac2, desc_mac1, desc_mac2)

    def get_range_timeout(self, topo:Topo):
        mac1 = get_bracket_str_by_sub(self.position, 0)
        mac2 = get_bracket_str_by_sub(self.position, 1)
        desc_mac1 = ['向{}发送连接请求，但超时'.format(topo.mac_name_table[mac2])]
        desc_mac2 = ['无法成功回应{}发起的连接请求'.format(topo.mac_name_table[mac1])]
        self.get_range_for_two_leaf_node(mac1, mac2, desc_mac1, desc_mac2)

    def get_range(self, topo: Topo, dbif: DBInterface, fault_range: FaultRange):

        if self.name == FAULT_APPLICATION_CONNECTION_ERROR:
            '''
            故障名称：连接错误
            故障描述：两台端主机通信出现连接错误
            故障表description字段：action
                                表示两台主机的应用行为
                                如：192.168.69.101通过CFR发送指令，修改165设备值为95
            故障表position字段：(MAC1, MAC2)
                              MAC1向MAC2发起连接请求，但连接错误
            故障范围计算：devices: MAC1, MAC2
                       links: 无
            返回前端的描述信息：
            '''
            self.get_range_fail(topo)


        elif self.name == FAULT_APPLICATION_CONNECTION_TIMEOUT:
            '''
            故障名称：连接超时
            故障描述：两台端主机通信出现连接超时
            故障表description字段：action
                                表示两台主机的应用行为
                                如：192.168.69.101通过CFR发送指令，修改165设备值为95
            故障表position字段：(MAC1, MAC2)
                              MAC1向MAC2发起连接请求，但连接超时
            故障范围计算：devices: MAC1, MAC2
                       links: 无
            返回前端的描述信息：
            '''
            self.get_range_timeout(topo)

class InterfaceFault(ApplicationFault):

    classification = '接口故障'

    def get_range(self, topo: Topo, dbif: DBInterface, fault_range: FaultRange):

        if self.name == FAULT_INTERFACE_CONNECTION_ERROR:
            '''
            故障名称：连接错误
            故障描述：两台端主机通信出现连接错误
            故障表description字段：action
                                表示两台主机的应用行为
                                如：192.168.69.101通过CFR发送指令，修改165设备值为95
            故障表position字段：(MAC1, MAC2)
                              MAC1向MAC2发起连接请求，但连接错误
            故障范围计算：devices: MAC1, MAC2
                       links: 无
            返回前端的描述信息：
            '''
            self.get_range_fail(topo)

        elif self.name == FAULT_INTERFACE_CONNECTION_TIMEOUT:
            '''
            故障名称：连接超时
            故障描述：两台端主机通信出现连接超时
            故障表description字段：action
                                表示两台主机的应用行为
                                如：192.168.69.101通过CFR发送指令，修改165设备值为95
            故障表position字段：(MAC1, MAC2)
                              MAC1向MAC2发起连接请求，但连接超时
            故障范围计算：devices: MAC1, MAC2
                       links: 无
            返回前端的描述信息：
            '''
            self.get_range_timeout(topo)

        elif self.name == FAULT_INTERFACE_STATUS_CODE_ERROR:
            '''
            故障名称：状态码错误
            故障描述：两台端主机访问发生状态码错误
            故障表description字段：null
                                无
            故障表position字段：(MAC1, MAC2)
                              MAC1向MAC2发起连接请求，但连接超时
            故障范围计算：devices: MAC1, MAC2
                       links: 无
            返回前端的描述信息：
            '''
            mac1 = get_bracket_str_by_sub(self.position, 0)
            mac2 = get_bracket_str_by_sub(self.position, 1)
            desc_mac1 = ['访问{}，得到状态码404'.format(topo.mac_name_table[mac2])]
            desc_mac2 = ['拒绝了{}的访问请求，返回状态码404'.format(topo.mac_name_table[mac1])]
            self.get_range_for_two_leaf_node(mac1, mac2, desc_mac1, desc_mac2)


class HardwareFault(BaseFault):

    classification = '硬件故障'

    def get_range_single_with_detail_attr(self, db:DBInterface, topo:Topo, attr:str):
        # attr can be "cpu", or "mem" or "disk"
        # TODO: 这里是否需要获取最新的CPU等状态信息
        
        mac = get_bracket_str_by_sub(self.position, 0)
        sql_get_details = 'SELECT info FROM {} WHERE mac = "{}"'.format(MYSQL_DEVICE_DETAILS_TABLE_NAME, mac)
        details = db.mysql_query(sql_get_details)[0][0]
        details_dict = eval(details)
        try:
            attr_value = details_dict[attr]
        except Exception as e:
            log.error(e)
            log.error("In hardware fault:{}, cannot get attr {}".format(self, attr))
            attr_value = "NULL"
        interval = '5' if self.level == 'mild' else '10'
        desc_mac = ['设备{}的{}占用过高'.format(topo.mac_name_table[mac], attr), '超过{}周期达到{}以上'.format(interval, attr_value)]
        device_list = [get_device_list_item(mac, self.level, desc_mac)]
        link_list = []
        self.range = zip_fault_range(device_list, link_list, self.fault_hash)
        print(self.range)

    def get_range(self, topo: Topo, dbif: DBInterface, fault_range: FaultRange):

        if self.name == FAULT_HARDWARE_DEVICE_OFFLINE:
            '''
            故障名称：设备掉线
            故障描述：网络中某台设备（交换机或端主机掉线）
            故障表description字段：null
                                可通过position字段推算
            故障表position字段：(MAC)
                              MAC表示故障设备地址
            故障范围计算：devices:如果MAC是端主机，则只影响自己，若是交换机，则该交换机为severe，该交换机的邻接节电以及可达主机为moderate
                       links：如果MAC是端主机，则影响其连接的链路，若是交换机，则影响与其连接的多个链路
            返回前端的描述信息：
            '''
            
            mac = get_bracket_str_by_sub(self.position, 0)
            device_list = []
            if topo.node_table[mac].is_server:
                desc_mac = ['端节点{}掉线'.format(mac)]
                device_list = [get_device_list_item(mac, self.level, desc_mac)]

            elif topo.node_table[mac].is_switch:
                switch_neighbor = [i for i in topo.G_MAC.adj[mac] if topo.node_table[i].is_switch]
                desc_switch = ['交换机{}掉线'.format(mac)]
                desc_switch_neighbor = ['与掉线的交换机直连，可能受较大影响']
                mac_reach_node_list = topo.node_table[mac].reach_node_list
                desc_reach_node = ['由于交换机{}掉线，本设备通信可能受影响'.format(mac)]
                device_list.append(get_device_list_item(mac, self.level, desc_switch))
                [device_list.append(get_device_list_item(node, LEVEL_MODERATE, desc_switch_neighbor)) for node in switch_neighbor]
                [device_list.append(get_device_list_item(node, LEVEL_MODERATE, desc_reach_node)) for node in mac_reach_node_list]

            link_desc = ['设备{}掉线引起的链路中断'.format(mac)]
            link_list = []
            [link_list.append(get_link_list_item(pair, self.level, link_desc)) for pair in [(mac, adj) for adj in topo.G_MAC.to_undirected().adj[mac]]]

            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_HARDWARE_CONFIGURATION_ERROR:
            '''
            故障名称：代理配置故障
            故障描述：网络中某台交换机无法获取代理配置
            故障表description字段：null
            故障表position字段：(MAC)
                              MAC表示故障设备地址
            故障范围计算：devices:故障交换机MAC
                       links：无
            返回前端的描述信息：
            '''
            
            mac = get_bracket_str_by_sub(self.position, 0)
            desc_mac = ['交换机{}无法获取代理配置'.format(mac)]
            device_list = [get_device_list_item(mac, self.level, desc_mac)]
            link_list = []
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_HARDWARE_CPU_HIGH:
            '''
            故障名称：CPU高占用
            故障描述：网络中某台设备CPU占用过高
            故障表description字段：null
            故障表position字段：(MAC)
                              MAC表示故障设备地址
            故障范围计算：devices:故障设备MAC
                       links：无
            返回前端的描述信息：
            '''
            self.get_range_single_with_detail_attr(dbif, topo, 'cpu')

        elif self.name == FAULT_HARDWARE_MEM_HIGH:
            '''
            故障名称：内存高占用
            故障描述：网络中某台设备内存占用过高
            故障表description字段：null
            故障表position字段：(MAC)
                              MAC表示故障设备地址
            故障范围计算：devices:故障设备MAC
                       links：无
            返回前端的描述信息：
            '''
            self.get_range_single_with_detail_attr(dbif, topo, 'mem')

        elif self.name == FAULT_HARDWARE_DISK_HIGH:
            '''
            故障名称：硬盘高占用
            故障描述：网络中某台设备硬盘占用过高
            故障表description字段：null
            故障表position字段：(MAC)
                              MAC表示故障设备地址
            故障范围计算：devices:故障设备MAC
                       links：无
            返回前端的描述信息：
            '''
            self.get_range_single_with_detail_attr(dbif, topo, 'disk')

        elif self.name == FAULT_HARDWARE_LINK_ERROR:
            '''
            故障名称：链路异常
            故障描述：网络中某条链路出现丢包或数据错误传输等问题
            故障表description字段：(pkt_loss, err_rate)
                                 pkt_loss表示链路丢包率，如20%，若为空则表示无这项详细描述
                                 err_rate表示链路传输数据的错误率，如10%，同上可为空
            故障表position字段：(MAC1, MAC2)
                              发生故障的链路MAC地址
            故障范围计算：devices:故障设备MAC
                       links：(MAC1, MAC2)
            返回前端的描述信息：
            '''
            
            mac1 = get_bracket_str_by_sub(self.position, 0)
            mac2 = get_bracket_str_by_sub(self.position, 1)
            reach_server_list = topo.node_table[mac2].reach_node_list
            pkt_loss = get_bracket_str_by_sub(self.description, 0)
            err_rate = get_bracket_str_by_sub(self.description, 1)
            desc_pkt_loss = ['链路丢包率:{}'.format(pkt_loss) if pkt_loss != '' else '']
            desc_err_rate = ['链路传输数据的错误率:{}'.format(err_rate) if err_rate != '' else '']
            desc_mac = ['硬件故障引起的链路异常']
            desc_reach_server = ['由于{}与{}之间的链路异常，通信可能受影响'.format(topo.mac_name_table[mac1], topo.mac_name_table[mac2])]
            device_list = []
            device_list.append(get_device_list_item(mac1, self.level, desc_mac))
            device_list.append(get_device_list_item(mac2, self.level, desc_mac))
            for mac in reach_server_list:
                device_list.append(get_device_list_item(mac, LEVEL_MODERATE, desc_reach_server))
            link_list = []
            desc_link = ['链路异常']
            if desc_err_rate != ['']:
                desc_link += desc_err_rate
            if desc_pkt_loss != ['']:
                desc_link += desc_pkt_loss
            link_list.append(get_link_list_item((mac1, mac2), self.level, desc_link))
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_HARDWARE_LINK_ERROR:
            '''
            故障名称：链路中断
            故障描述：网络中某条链路由于物理链路断开或其他硬件原因中断
            故障表description字段：null
            故障表position字段：(MAC1, MAC2)
                              发生故障的链路MAC地址
            故障范围计算：devices:故障设备MAC
                       links：(MAC1, MAC2)
            返回前端的描述信息：
            '''
            
            mac1 = get_bracket_str_by_sub(self.position, 0)
            mac2 = get_bracket_str_by_sub(self.position, 1)
            reach_server_list = topo.node_table[mac2].reach_node_list
            desc_mac = ['硬件故障引起的链路异常']
            desc_reach_server = ['由于{}与{}之间的链路中断，通信可能受影响'.format(topo.mac_name_table[mac1], topo.mac_name_table[mac2])]
            device_list = []
            device_list.append(get_device_list_item(mac1, self.level, desc_mac))
            device_list.append(get_device_list_item(mac2, self.level, desc_mac))
            for mac in reach_server_list:
                device_list.append(get_device_list_item(mac, LEVEL_MODERATE, desc_reach_server))
            link_list = []
            desc_link = ['链路中断']
            link_list.append(get_link_list_item((mac1, mac2), self.level, desc_link))
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)


class ProtocolFault(BaseFault):

    classification = '协议故障'

    def get_range(self, topo: Topo, dbif: DBInterface, fault_range: FaultRange):

        if self.name == FAULT_PROTO_STP_STATUS_ERROR:
            '''
            故障名称：STP状态计算错误
            故障描述：故障交换机在某端口将STP状态计算错误
            故障表description字段：(now, correct)
                                其中，now表示当前端口计算状态，correct表示端口应该是什么状态
                                如(InterfaceState.DESIGNATED,InterfaceState.ROOT)
            故障表position字段：(MAC, port)
                              其中，MAC表示故障交换机MAC地址，port指故障端口
                              如(LSW2,Ethernet0/0/2)
            故障范围计算：devices:所有网络中主机和交换机，其中发生故障的交换机为severe，其余为moderate
                       links：所有网络链路，其中与severe节点连接的为severe，其余为moderate
            返回前端的描述信息：在MAC位置port端口发生STP状态计算错误，正确状态为correct，现为now
            '''
            
            # 故障影响所有网络节点，其中发生节点标为红色，其余节点标为黄色
            # generate device list[{}, {} ...]
            # self.position be like (MAC, port)
            severe_mac = get_bracket_str_by_sub(self.position, 0)
            severe_port = get_bracket_str_by_sub(self.position, 1)

            # self.description be like (now, correct)
            now_status = get_bracket_str_by_sub(self.description, 0)
            correct_status = get_bracket_str_by_sub(self.description, 1)

            # list(str) be like ['A', 'B', 'C', 'D', 'F', 'E', 'G', 'H']
            # each color should be 2
            other_mac_list = [mac for mac in topo.node_table.keys() if mac != severe_mac]

            desc_severe = ['在{}位置{}端口发生STP状态计算错误'.format(severe_mac, severe_port),
                           '正确状态为{}，现为{}'.format(correct_status, now_status)]
            desc_other = ['由于{}:{}的STP状态计算错误导致的设备异常'.format(severe_mac, severe_port)]
            desc_link = ['由于{}:{}的STP状态计算错误导致的链路异常'.format(severe_mac, severe_port)]
            # generate list like:
            # [
            #     { "mac": severe_mac, "color": 1, "details":["STP协议状态错误"] },
            #     { "mac": item in other_pos_mac, "color": 2, "details":["STP协议状态错误"] }
            # ]
            device_list = []
            severe_mac_dict = get_device_list_item(severe_mac, self.level, desc_severe)
            device_list.append(severe_mac_dict)

            # level of other device is set to 'moderate'
            other_list = get_device_list_from_list(other_mac_list, LEVEL_MODERATE, desc_other)
            device_list += other_list

            # links is a list filled with (mac1, mac2) which is undirected
            links = topo.G_MAC.to_undirected().edges
            link_list = []

            for node_pair in links:
                if severe_mac in node_pair:
                    d = get_link_list_item(node_pair, self.level, desc_link)
                else:
                    d = get_link_list_item(node_pair, LEVEL_MODERATE, desc_link)
                link_list.append(d)

            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_PROTO_MAC_ERROR:
            '''
            故障名称：交换机MAC表计算错误
            故障描述：故障交换机在将MAC表计算错误，会错误地将去往某个目的主机的数据从正确口转发至错误口
            故障表description字段：(port_now, port_correct)
                                其中，port_now表示计算错误的出端口号，port_correct表示正确的出端口号
            故障表position字段：(MAC1, MAC2)
                              其中，MAC1表示交换机地址，MAC2表示被计算错误的主机MAC
                              (LSW1,5489-9881-7a05)
            故障范围计算：devices:故障交换机即MAC1受影响为severe，目的主机MAC2为moderate
                       links：无
            返回前端的描述信息：{MAC1}设备MAC表计算错误，将去往{MAC2}的端口由{port_correct}计算成{port_now}
            '''
            
            severe_mac = get_bracket_str_by_sub(self.position, 0)
            moderate_mac = get_bracket_str_by_sub(self.position, 1)
            port_now = get_bracket_str_by_sub(self.description, 0)
            port_correct = get_bracket_str_by_sub(self.description, 1)
            desc_severe = ['MAC表计算错误',
                           '错误值：{}->{}'.format(moderate_mac, port_now),
                           '正确为：{}->{}'.format(moderate_mac, port_correct)
                           ]
            desc_moderate = ['由于{}的MAC表计算错误'.format(severe_mac),
                             '{}无法接收到来自{}转发的流量'.format(moderate_mac, severe_mac)]

            severe_mac_dict = get_device_list_item(severe_mac, self.level, desc_severe)
            moderate_mac_dict = get_device_list_item(moderate_mac, LEVEL_MODERATE, desc_moderate)
            device_list = [severe_mac_dict, moderate_mac_dict]
            link_list = []
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)

        elif self.name == FAULT_PROTO_ARP_ERROR:
            '''
            故障名称：端主机ARP表计算错误
            故障描述：故障主机的ARP表计算错误，原因是多个设备收到了相同的IP，导致ARP表中IP重复
            故障表description字段：null
                                可通过position字段推导得出
            故障表position字段：(PC_NAME, IP)
                              其中，PC_NAME表示故障主机的名称！，IP表示重复的IP项
                              如：(PC5,192.168.133.10)
            故障范围计算：devices: ARP表计算错误的主机和出现表中异常IP所指代的主机都是moderate
                       links：无
            返回前端的描述信息：{PC_NAME}设备从多个设备收到了相同的IP:{IP}
            '''
            
            device_list = []
            pc_name = get_bracket_str_by_sub(self.position, 0)
            ip = get_bracket_str_by_sub(self.position, 1)
            desc_pc = ['从多个设备收到了相同的IP:{}'.format(ip)]
            desc_ip = ['由于{}的ARP表计算错误，可能导致通信故障'.format(pc_name)]

            # node_table is a dict like {'node_mac': node_object}
            # node object has attr: name, mac, ip, etc.
            for node in topo.node_table.values():
                if node.name == pc_name:
                    device_list.append(get_device_list_item(node.mac, self.level, desc_pc))
                if node.ip == ip:
                    device_list.append(get_device_list_item(node.mac, self.level, desc_ip))
            link_list = []
            self.range = zip_fault_range(device_list, link_list, self.fault_hash)
            print(self.range)


if __name__ == '__main__':
    test_print = BaseFault()
    # test_print.format_output()
    print(test_print.__class__.__name__)
