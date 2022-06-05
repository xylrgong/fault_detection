import json

from config.config import *
import datetime
import re


def get_timestamp(t):
    return t.timestamp()


def trans_fault_dict_from_datetime_to_timestamp(fault_dict, key='time'):
    fault_dict[key] = get_timestamp(fault_dict[key])
    return fault_dict


# transform "(mac1,mac2)" in to ['mac1', 'mac2']
def del_brackets(mac_pair):
    index = [mac.replace('(', '').replace(')', '') for mac in mac_pair.split(',')]
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


# transfer str into list
# "(mac1, port1, ...)" into ["mac1", "port1", "..."]
def transfer_bracket_str_to_list(bracket_str):
    p = re.compile(r'[(](.*)[)]', re.S)
    try:
        no_bracket = re.findall(p, bracket_str)
        res = no_bracket[0].replace(" ", '').split(',')
    except Exception as e:
        print("Error when transfer str into list:" + str(e))
        res = bracket_str
    return res


def get_bracket_str_by_sub(bracket_str, pos):
    p = re.compile(r'[(](.*)[)]', re.S)
    try:
        no_bracket = re.findall(p, bracket_str)
        res = no_bracket[0].replace(" ", '').split(',')[pos]
    except Exception as e:
        print("Error when get str by sub:" + str(e))
        res = bracket_str
    return res


# return a dict in device_list
def get_device_list_item(mac, level, details):
    res = {
        "mac": mac,
        "color": SEVERITY[level],
        "details": details
    }
    return res


# return a list like [ {"mac": x, "color": y, "details": z}, ...]
def get_device_list_from_list(device_list, level, details):
    return [get_device_list_item(device, level, details) for device in device_list]


# zip devices and links
def zip_fault_range(device_list, links_list, flow_hash):
    res = {
        flow_hash: {
            "devices": device_list,
            "links": links_list
        }
    }

    return res


def get_link_list_item(node_pair, level, desc):
    res = {
        "srcMac": node_pair[0],
        "dstMac": node_pair[1],
        "color": SEVERITY[level],
        "details": desc
    }
    return res


if __name__ == '__main__':
    l = [[1, 'F'], [1, 'G'], [2, 'E']]
    d = transfer_list_dict2dict(l)
    print(d)

    t = "(mac1,ad-ad-24, mac3)"
    print(transfer_bracket_str_to_list(t))
    # print(transfer_bracket_str_to_list(t)[0].replace(' ','').split(','))
    t2 = ['A', 'B', 'C', 'D', 'F', 'E', 'G', 'H']
    print(get_device_list_from_list(t2, 'moderate', ['desc']))
    t3 = "(,)"
    x1 = get_bracket_str_by_sub(t3, 0)
    x2 = get_bracket_str_by_sub(t3, 1)
    print(x1 == '')
    print(x2 == '')
