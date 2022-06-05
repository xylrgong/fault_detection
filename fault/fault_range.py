import json


class FaultRange(object):
    hw_range = {}
    proto_range = {}
    traffic_range = {}
    app_range = {}
    if_range = {}
    errors = {}

    def get_full_range(self):
        full_json = {
            "hw": self.hw_range,
            "proto": self.proto_range,
            "if": self.if_range,
            "app": self.app_range,
            "traffic": self.traffic_range,
            "errors": self.errors
        }
        return json.dumps(full_json, ensure_ascii=False)


if __name__ == '__main__':
    t = FaultRange()
    t1 = t.get_full_range()
    print(t1)
    print(type(hash(("FL_BLK_HOLE", 1))))

    j = {
        "-5491666964808633865": {
            "devices": [{
                "mac": "C",
                "color": 2,
                "details": ["硬件故障引起的链路异常"]
            }, {
                "mac": "D",
                "color": 2,
                "details": ["硬件故障引起的链路异常"]
            }, {
                "mac": "H",
                "color": 2,
                "details": ["由于C_name与D_name之间的链路异常，通信可能受影响"]
            }, {
                "mac": "F",
                "color": 2,
                "details": ["由于C_name与D_name之间的链路异常，通信可能受影响"]
            }],
            "links": [{
                "srcMac": "C",
                "dstMac": "D",
                "color": 2,
                "details": ["链路异常", "链路传输数据的错误率:20"]
            }]
        }
    }

    print(j)

    t.hw_range.update(j)
    print(t.get_full_range())
