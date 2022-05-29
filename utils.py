import datetime
import re
def get_timestamp(t):
    return t.timestamp()

def trans_fault_dict_from_datetime_to_timestamp(fault_dict, key='time'):
    fault_dict[key] = get_timestamp(fault_dict[key])
    return fault_dict

# transform "(mac1,mac2)" in to ['mac1', 'mac2']
def del_brackets(mac_pair):
    index = [mac.replace('(','').replace(')','') for mac in mac_pair.split(',')]
    return index

# transfer [{k1:[v1_1]}, {k1:[v1_2]}, {k2:[v2]}] into {k1:[v1_1, v1_2], k2:[v2]}
def transfer_list_dict2dict(l):
    res = dict()
    for item in l:  # item be like [1, 'A']
        if item[0] in res.keys():  # already has key, do append
            res[item[0]].append(item[1])
        else:
            res[item[0]] = list(item[1])
    return res

if __name__ == '__main__':
    l = [[1, 'F'], [1, 'G'], [2, 'E']]
    d = transfer_list_dict2dict(l)
    print(d)