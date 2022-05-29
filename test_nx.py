import networkx as nx
from topo import NetworkNode

G = nx.DiGraph()

n1 = NetworkNode(mac="mac1")
n2 = NetworkNode(mac="mac2")

# G.add_nodes_from([
#     (n1, {"mac":n1.mac}),
#     (n2, {"mac":n2.mac})
# ])

G.add_node("n1", name="n1.mac")
G.add_edge("n1", "n2", port=[0,1])
G.add_edge("n2", "n1", port=[1,0])
G.add_edge("n1", "n4", port=[1,2])
G.add_edge("n4", "n1", port=[2,1])
G.add_edge("n2", "n4", port=[2,1])
G.add_edge("n4", "n2", port=[1,2])
G.add_edge("n2", "n5", port=[3,0])
G.add_edge("n5", "n3", port=[0,3])
G.add_edge("n4", "n5", port=[0,1])
G.add_edge("n5", "n4", port=[1,0])

print("图的节点为：", G.nodes)
print("图的边为", G.edges)
print("n1节点的邻居为", G.adj["n1"])
print("n1->n2边的属性", G["n1"]["n2"])
print("n2->n1边的属性", G["n2"]["n1"])
# print(list(G.nodes)[0].mac)
print("取出图的节点和节点data", list(G.nodes(data=True)))
# print(G["n1"]["n2"]['port'][::-1])
print("图的节点的度", G.degree)

print("`````````````")
print("打印出边节点以及属性")
for i in G.edges.data("port"):
    print(i)
print("获取n1 n2节点对应边属性", G.get_edge_data("n1","n2"))
print("获取节点以及其对应邻居节点和属性", [(n, nbrattr) for n, nbrattr in G.adjacency()])

print(nx.cycle_basis(G.to_undirected()))
print(nx.find_cycle(G.to_undirected()))

test = [['n2', 'n5', 'n4'], ['n1', 'n2', 'n4']]
print([node for circle in test for node in circle])
