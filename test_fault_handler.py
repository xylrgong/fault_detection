from traceback import print_tb
from fault_handler import *
import mysql.connector as mysql
fault_list_done = []
fault_list_duplicate = []
a = BaseFault(name='a', number=0, time='2000')
b = BaseFault(name='a', number=0, time='2001')
c = BaseFault(name='c', number=0, time='1000')
fault_list_duplicate.append(a)
fault_list_duplicate.append(b)

for i in fault_list_duplicate:
    if i not in fault_list_done:
        fault_list_done.append(i)
print(fault_list_done)
print(a>c)

print("++++++++++++++++++++++++++++++++++++++++")

test1 = {'id': 3, 'name': 'FL_PT_SCAN', 'number': 0, 'time': 1651754302.0, 'flag': '1', 'position': '(10.0.0.1,8080,10.0.0.2)', 'level': 'fatal'}
test2 = {'id': 4, 'name': 'FL_PT_SCAN', 'number': 0, 'time': 1651754496.0, 'flag': '0', 'position': '(10.0.0.1,8080,10.0.0.2)', 'level': 'fatal'}
t1 = BaseFault.construct(test1)
t2 = BaseFault.construct(test2)
print(a==b)
l = {}
l[t1.get_key()] = t1
print(t2.get_key() in l.keys())
if t2.get_key() in l.keys():
    del l[t2.get_key()]
print(t1)
print(l)
del t2

f1 = BaseFault.construct(test1)
f2 = AppFault.construct(test2)
print(isinstance(f1, BaseFault))
print(isinstance(f2, BaseFault))
print(f1==f2)




