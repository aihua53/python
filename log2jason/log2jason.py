#!/usr/bin/python3
import sys, os, re
import datetime, math
import json

def main(argv):
    if len(argv) < 2:
        print("need log path")
        return
    fd1 = open(sys.argv[1])
    contents = fd1.readlines()
    fd1.close()
    # os.system("rm -f result.json")
    d = os.path.dirname(__file__)
    if(os.path.exists(os.path.join(d,"result.json"))):
        os.remove(os.path.join(d,"result.json"))
    fd2 = open("result.json", "w")

    for line in contents:
        line = line[len("[2021-08-04 23:20:03] [DEBUG] b\'"):]
        line = line.replace("\n", "")[:-1]
        line = line.replace("\\\\\"", "\'")
        json1 = json.loads(line)
        for event in json1["events"]:
            json_entity = json.loads(event["entity"].replace("\'", "\""))
            event["entity"] = json_entity

        json1_str = json.dumps(json1)
        json.dump(json1, fd2, indent=4, ensure_ascii=False)

    fd2.close()


if __name__=='__main__':
    main(sys.argv)
