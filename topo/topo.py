import networkx as nx
from db.db import *
from utils.utils import transfer_list_dict2dict

class NetworkNode(object):
    name = 'Default'
    ip = 'Default'
    mac = 'Default'
    info = 'Default'
    is_switch = False
    is_server = False
    reach_node = None  # reach_node is a table like {1:[MAC1, MAC2], 2:[MAC3]}
    reach_node_list = None  # a list like [MAC1, MAC2, MAC3]

    def __init__(self, name=None, ip=None, mac=None, is_switch=False, is_server=False, reach_node=None, info=None, reach_node_list=None):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.is_switch = is_switch
        self.is_server = is_server
        self.reach_node = reach_node
        self.info = info
        self.reach_node_list = reach_node_list

    def __repr__(self):
        return "mac=" + self.mac + " name=" + str(self.name) + " ip=" + str(self.ip) + " type=" + (lambda x, y: "None" if (not x and not y) else "SERVER" if x else "SWITCH")(self.is_server, self.is_switch)

    def __str__(self):
        return "Node mac:" + str(self.mac)

    def __eq__(self, other):
        return self.mac == other.mac

    def __hash__(self):
        return hash(self.mac)

    # def __del__(self):
    #     print("DEL " + self.mac)


class NodeList(object):
    nodelist = {}
    nodelist_server = []
    node_list_switch = []

    def __contains__(self, item):
        try:
            return item in self.nodelist
        except TypeError:
            return False


class Topo(object):
    # node_set = set()
    circle_node = set()
    device_details = None
    topo_table = {}
    node_table = {}
    mac_name_table = {}
    circle_list = None
    update_time = -1

    G = nx.DiGraph()
    G_MAC = nx.DiGraph()

    def init_node(self, device_details_list, forward_list):
        cnt = 0
        for detail in device_details_list:  # detail be like ('mac', 'name', 'ip', 'type', 'info')
            mac = detail[0]
            name = detail[1]
            ip = detail[2]
            # forward be like ['device_mac', 'dst_mac', 'outport']
            is_switch = (lambda x: True if x == 'switch' else False)(detail[3])
            is_host = (lambda x: True if x == 'host' else False)(detail[3])
            info = detail[4]
            # reach_node_list can give dict-list like [ [mac1,outport1], [mac2,outport2], [mac,outport1], ...] for current mac
            # reach_node is only for switch node!
            if is_switch:
                # port_mac_list like [ [1, MAC1], [1, 'MAC2'], [2, 'MAC3']]
                # node is a list like ['device_mac', 'dst_mac', outport]
                port_mac_list = []
                reach_node_list = []
                for node in forward_list:
                    if node[0] == mac:
                        port_mac_list.append([node[2],node[1]])
                        if node[1] not in reach_node_list:
                            reach_node_list.append(node[1])
                # port_mac_list = [[node[2],node[1]] for node in forward_list if node[0] == mac]
                # reach_node_list = [node[1] for node in forward_list if node[1] not in reach_node_list]
                reach_node_dict = transfer_list_dict2dict(port_mac_list)

            else:
                reach_node_dict = None
                reach_node_list = None
            node = NetworkNode(mac=mac, name=name, ip=ip, is_switch=is_switch, is_server=is_host, reach_node=reach_node_dict, info=info, reach_node_list=reach_node_list)
            # self.node_set.add(node)
            self.node_table[mac] = node
            self.mac_name_table[mac] = name
            cnt += 1
        log.info("初始化拓扑节点数量{}个".format(cnt))

    def calculate_circle(self):
        self.circle_list = nx.cycle_basis(self.G.to_undirected())
        circle_node_list = [node for circle in self.circle_list for node in circle]
        self.circle_node = set(circle_node_list)

    def topo_table_construct(self, topo_list):
        # topo_list be like ['src_mac', 'dst_mac', port_s2d, port_d2s]
        for topo_item in topo_list:
            node_src_mac = topo_item[0]
            node_dst_mac = topo_item[1]
            node_pt_src2dst = topo_item[2]
            node_pt_dst2src = topo_item[3]
            node_src = NetworkNode(mac=node_src_mac)
            if node_src in self.node_table.values():
                node_src = self.node_table[node_src_mac]
            node_dst = NetworkNode(mac=node_dst_mac)
            if node_dst in self.node_table.values():
                node_dst = self.node_table[node_dst_mac]

            self.G.add_edge(node_src, node_dst, port=list[node_pt_src2dst, node_pt_dst2src])
            self.G.add_edge(node_dst, node_src, port=list[node_pt_dst2src, node_pt_src2dst])
            self.G_MAC.add_edge(node_src_mac, node_dst_mac, port=node_pt_src2dst)
            self.G_MAC.add_edge(node_dst_mac, node_src_mac, port=node_pt_dst2src)

            self.topo_table[(node_src.mac, node_dst.mac)] = node_pt_src2dst
            self.topo_table[(node_dst.mac, node_src.mac)] = node_pt_dst2src

            self.node_table[node_src_mac] = node_src
            self.node_table[node_dst_mac] = node_dst

        print(self.node_table)

        # print(self.G)
        # print(self.node_set)

        # length = dict(nx.all_pairs_shortest_path_length(self.G))
        # # 计算可达性矩阵
        # R = np.array([[length.get(m, {}).get(n, 0) > 0 for m in self.G.nodes] for n in self.G.nodes], dtype=np.int32)
        # print(R)
        # print(self.topo_table)
        # print(self.G.number_of_nodes())
        # selected_data = dict( (n,d['mac']) for n,d in self.G.nodes().items() if d['mac'] == 't1')
        # print(type(selected_data))
        # print(f'Node found : {len (selected_data)} : {selected_data}')
        # for i in selected_data.keys():
        #     self.G.remove_node(i)
        #
        # R = np.array([[length.get(m, {}).get(n, 0) > 0 for m in self.G.nodes] for n in self.G.nodes], dtype=np.int32)
        # print(R)
        # print(self.topo_table)
        # print(self.G.nodes())
        # nx.draw(self.G)
        # plt.show()
        # # self.G.remove_node(selected_data.keys())

    # def find_node_by_attr(self, attr, value):
    #     selected_data = dict((n, d[attr]) for n, d in self.G.nodes().items() if d[attr] == value)
    #     for i in selected_data.keys():
    #         return i
    # aborted function
    '''
    def get_node_in_nodeset(self, node_mac):
        nodelist = list(self.node_set)
        for node in nodelist:
            try:
                if node.mac == node_mac:
                    return node
            except Exception as e:
                log.error(e)
                return None
    '''

    # aborted
    '''
    def get_node_by_mac(self, mac):
        node_list = list(self.node_set)
        try:
            node = [i for i in node_list if i.mac==mac]
            return node[0]
        except Exception as e:
            log.error(e)
            log.error("No such node in topo!")
    '''


if __name__ == "__main__":
    db = DBInterface()
    db.init()
    db.insert_test_items()
    db.create_topo_and_insert_test_items()
    topo_res = db.read_topo()
    device_details_res = db.read_device_details()
    forward_res = db.read_forward()
    print(topo_res)
    print(device_details_res)
    print(forward_res)
    topo = Topo()
    topo.init_node(device_details_res, forward_res)
    topo.topo_table_construct(topo_res)
    topo.calculate_circle()
    # p = topo.get_node_by_mac(mac='A')
    # print(p)
    print(topo.topo_table['A', 'B'])
    # reach_node_list = [x for x in topo.node_table['A'].reach_node.values()]
    # # l = []
    # # for node_list in t:
    # #     for item in node_list:
    # #         if item not in l:
    # #             l.append(item)
    # # print(l)
    # l = []
    # [l.append(item) for element in reach_node_list for item in element]
    # print(l)

    print(topo.node_table.values())
    print(topo.node_table['A'].reach_node_list)

