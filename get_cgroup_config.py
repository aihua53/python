
import os
from collections import defaultdict
import pandas as pd

PATH = r'D:\wangwei1\work\issue\x01\cgroup\cgroup'
BG_PROCS = "bg_procs"
BG_TASKS = "bg_tasks"
FG_PROCS = "fg_procs"
FG_TASKS = "fg_tasks"
SYS_BG_PROCS = "sys_bg_procs"
SYS_BG_TASKS = "sys_bg_tasks"
TOP_PROCS = "top_procs"
TOP_TASKS = "top_tasks"
VIP_PROCS = "vip_procs"
VIP_TASKS = "vip_tasks"
CAMERA_PROCS = "camera-daemon_procs"
CAMERA_TASKS = "camera-daemon_tasks"
THREAD = "thread"
PROCESS = "process"
TOP = "top"

def parseThread(name,dd_thread,dd_process):
    filepath = os.path.join(PATH, name + ".txt")
    with open(filepath, mode='r', encoding='utf-8') as f:
        line = f.readline()
        while True:
            line = f.readline()       
            if not line:
                break
            dd_thread[line.split()[2]].append(line.split()[9]) # thread name
            dd_thread[line.split()[2]].append(line.split()[1]) # pid
            dd_thread[line.split()[2]].append(dd_process[line.split()[1]]) # process name
            

def parseProcs(name,dd):
    filepath = os.path.join(PATH, name + ".txt")
    with open(filepath, mode='r', encoding='utf-8') as f:
        while True:
            line = f.readline()
            if not line:
                break
            dd[line.split()[1]].append(line.split()[8]) # pid name
    # print(dd)

def parseCpusetProcs(name,dd_process,dd_top):
    filepath = os.path.join(PATH, name + ".txt")
    result = []
    result.append(['PID','processName','TOP'])
    with open(filepath, mode='r', encoding='utf-8') as f:
        while True:
            line = f.readline()
            if not line:
                break
            if(dd_top[line.strip()]):
                result.append([line.strip(), dd_process[line.strip()][0],dd_top[line.strip()][0]])
            else:
                result.append([line.strip(), dd_process[line.strip()][0],''])
    result_path = os.path.join(PATH, f'result.xlsx')
    pf = pd.DataFrame(result)
    if  os.path.exists(result_path) != True:
        pf.to_excel(result_path,name)
    else:
        writer = pd.ExcelWriter(result_path, engine='openpyxl', mode='a')
        pf.to_excel(writer, sheet_name=name)
        writer.save()

def parseCpusetTask(name,dd_thead):
    filepath = os.path.join(PATH, name + ".txt")
    result = []
    result.append(['TID','threadName','PID','processName'])
    with open(filepath, mode='r', encoding='utf-8') as f:
        while True:
            line = f.readline()
            if not line:
                break
            result.append([line.strip(), dd_thead[line.strip()][0],dd_thead[line.strip()][1],dd_thead[line.strip()][2]])

    result_path = os.path.join(PATH, f'result.xlsx')
    pf = pd.DataFrame(result)
    if  os.path.exists(result_path) != True:
        pf.to_excel(result_path,name)
    else:
        writer = pd.ExcelWriter(result_path, engine='openpyxl', mode='a')
        pf.to_excel(writer, sheet_name=name)
        writer.save()

def parseTop(name,dd_top):
    filepath = os.path.join(PATH, name + ".txt")
    with open(filepath, mode='r', encoding='utf-8') as f:
        for i in range(6):
            line = f.readline()
        while True:
            line = f.readline()
            if not line:
                break
            dd_top[line.split()[0]].append(line.split()[8])


def main():
    dd_process = defaultdict(list)
    dd_thread = defaultdict(list)
    dd_top = defaultdict(list)
    parseProcs(PROCESS,dd_process)
    parseThread(THREAD, dd_thread, dd_process)
    parseTop(TOP,dd_top)
    
    # pare cpuset process
    # parseCpusetProcs(BG_PROCS,dd_process,dd_top)
    # parseCpusetProcs(FG_PROCS,dd_process)
    # parseCpusetProcs(SYS_BG_PROCS,dd_process)
    # parseCpusetProcs(TOP_PROCS,dd_process)
    # parseCpusetProcs(VIP_PROCS,dd_process)
    # parseCpusetProcs(CAMERA_PROCS,dd_process)

    # pare cpuset task
    # parseCpusetTask(BG_TASKS,dd_thread)
    # parseCpusetTask(FG_TASKS,dd_thread)
    # parseCpusetTask(SYS_BG_TASKS,dd_thread)
    # parseCpusetTask(TOP_TASKS,dd_thread)
    # parseCpusetTask(VIP_TASKS,dd_thread)
    # parseCpusetTask(CAMERA_TASKS,dd_thread)


main()


# prettytable demo
# from prettytable import PrettyTable
# tb = PrettyTable()
# tb.field_names = ["City name", "Area", "Population", "Annual Rainfall"]
# tb.add_row(["Adelaide",1295, 1158259, 600.5])
# tb.add_row(["Brisbane",5905, 1857594, 1146.4])
# tb.add_row(["Darwin", 112, 120900, 1714.7])
# tb.add_row(["Hobart", 1357, 205556,619.5])
# print(tb)

# defaultdict demo
# from collections import defaultdict
# d = defaultdict(list)
# d['one'].append(1)
# d['one'].append(2)
# d['two'].append(3)
# d['two'].append(4)
# print(d)
# print(d['one'][1])


