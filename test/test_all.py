from fault.fault_handler import *
from utils.utils import *

def zip_fault_list_to_fault_dict_list(key_list, fault_list):
    fault_dict_list = []
    for fault_item in fault_list:
        to_dict = dict(zip(key_list, fault_item))
        fault_item_dict_ts = trans_fault_dict_from_datetime_to_timestamp(to_dict) 
        fault_dict_list.append(fault_item_dict_ts)
    return fault_dict_list

if __name__ == '__main__':
    read_id = 0
    keys = ['id', 'name', 'number', 'time', 'flag', 'position', 'level']
    fault_list = []
    fault_obj_done = []
    database = DBInterface()
    fault_rd_from_db = database.read_db_by_id(read_id, MYSQL_FAULT_TABLE_NAME)
    fault_list = zip_fault_list_to_fault_dict_list(key_list=keys,fault_list=fault_rd_from_db)
    print(fault_list)
    for i in range(len(fault_list)):
        fault_obj = BaseFault.construct(fault_list[i])
        if fault_obj not in fault_obj_done:
            print("add "+str(fault_obj))
            fault_obj_done.append(fault_obj)
            print(fault_obj_done)
        else:
            old_fault_obj = fault_obj_done[fault_obj_done.index(fault_obj)]
            # print("!!!!!!!!!!!!!!!!!!!!")
            # print(fault_obj)
            # print(old_fault_obj)
            # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # print("!!!!!!!!!!!!!!!!"+ fault_obj.flag)
            # print("!!!!!!!!!!!!!!!!"+str(old_fault_obj.time)+"sss"+str(fault_obj.time))
            # print(fault_obj.flag==0)
            if(fault_obj.flag==str(0)):
                if(fault_obj.time>old_fault_obj.time):
                    # print("!!!!!!!!!!!!!!!!")
                    print("lasting time:"+fault_obj.get_lasting_time(old_fault_obj))
                    print("remove "+str(fault_obj))
                    fault_obj_done.remove(old_fault_obj)
                    del old_fault_obj
                    del fault_obj
    print(fault_obj_done)
    print(len(fault_obj_done))
    title_rd_from_db = database.read_table_title()
    print(title_rd_from_db)

    
    

