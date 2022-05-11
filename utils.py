import datetime
def get_timestamp(t):
    return t.timestamp()

def trans_fault_dict_from_datetime_to_timestamp(fault_dict, key='time'):
    fault_dict[key] = get_timestamp(fault_dict[key])
    return fault_dict