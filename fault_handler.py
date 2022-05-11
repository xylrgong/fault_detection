import threading

class BaseFault():

    def __init__(self, id=-1, name=None, number=None, time=-1, flag=-1, position=None, level=None):
        self.id = id
        self.name = name
        self.number = number
        self.time = time
        self.flag = flag        
        self.position = position
        self.level = level

        self.fault_hash = None
    
    def __del__(self):
        print("Delete" + " " + str(self.name) + "_" + str(self.number) + " id:" + str(self.id))

    def __eq__(self, other):
        return self.name == other.name and self.number == other.number

    def __gt__(self, other):
        assert isinstance(other,BaseFault)
        return self.time > other.time and self==other

    def __hash__(self):
        if not self.fault_hash:
            hash_list = [self.name, self.number]
            self.fault_hash = hash(tuple(hash_list))
        return self.fault_hash

    def __str__(self):
        return "Fault id:" + str(self.id) + " and fault name: " + str(self.name) + " " + "and fault number: " + str(self.number) + " and flag: " + str(self.flag)

    def get_key(self):
        assert self.name is not None and self.number is not None
        return str(self.name) + str(self.number)
    
    def get_lasting_time(self, old):
        assert isinstance(old, BaseFault)
        return str(self.time - old.time)

    @staticmethod
    def construct(fault_item):
        return BaseFault(fault_item['id'],fault_item['name'], fault_item['number'],fault_item['time'], 
        fault_item['flag'],fault_item['position'],fault_item['level'])

    def get_range(self):
        print(str(self) + "has influenced XXX!!!")

class FlowFault(BaseFault):
    pass

class AppFault(BaseFault):
    pass

class ItfFault(BaseFault):
    pass

class HdwFault(BaseFault):
    pass
