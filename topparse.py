import re, os, numpy
import pandas as pd
from openpyxl import load_workbook

""""
分析目录下所有txt文件，分析结果cpu-result.xlsx保存在指定目录下
每次运行前，记得删除cpu-result.xlsx，不然sheet会不断累加
sheet页名称为文件名
"""
# pids = ['com.bilibili.bilithings', 'com.bilibili.bilithings:ijkservice']#除系统user\sys等之外，需要监控的进程
pids = ['tv.danmaku.bili', 'tv.danmaku.bili:ijkservice']#除系统user\sys等之外，需要监控的进程
dir_path = r'/home/wangwei1/wangwei1/work/performance/bilibili/test'#待分析目录


def parse_top(cpu_path):
    result = []  # 存储数据
    tasks = user = nice = sys = idle = iow = irq = sirq = host = 0
    pid_values = [0 for i in range(len(pids))]
    dict_pid = dict(zip(pids, pid_values))
    with open(cpu_path, mode='r', encoding='utf-8') as f:
        line = f.readline()
        while True:
            if line.strip().startswith('Tasks'):
                tasks = line.split()[1]
                try:
                    if user and any(dict_pid.values()):
                        result.append(
                            dict({'tasks': int(tasks), 'user': int(user), 'nice': int(nice), 'sys': int(sys),'idle': int(idle), 'iow': int(iow), 'irq': int(irq), 'sirq': int(sirq), 'host': int(host),
                                  'usr+nice+sys+iow+irq+sirq': numpy.sum([int(user), int(nice), int(sys), int(iow), int(irq), int(sirq)])}, **dict_pid))
                        user = nice = sys = idle = iow = irq = sirq = host = 0
                        pid_values = [0 for i in range(len(pids))]
                        dict_pid = dict(zip(pids, pid_values))
                except ValueError:
                    print(user, type(user))
            
            sys_result = re.search(r'(\d+)%cpu\s+(\d+)%user\s+(\d+)%nice\s+(\d+)%sys\s+(\d+)%idle\s+(\d+)%iow\s+(\d+)%irq\s+(\d+)%sirq\s+(\d+)%host.*', line)
            if sys_result:
                (total, user, nice, sys, idle, iow, irq, sirq, host) = sys_result.groups()
            for pid in pids:
                if line.strip().endswith(pid):
                    dict_pid[pid] = float(line.split()[8])
            
            line = f.readline()
            if not line:
                #添加最后一次数据
                result.append(
                    dict({'tasks': int(tasks), 'user': int(user), 'nice': int(nice), 'sys': int(sys), 'idle': int(idle), 'iow': int(iow), 'irq': int(irq), 'sirq': int(sirq), 'host': int(host),
                          'usr+nice+sys+iow+irq+sirq': numpy.sum([int(user), int(nice), int(sys), int(iow), int(irq), int(sirq)])}, **dict_pid))
                break
    return result


def main():
    result_path = os.path.join(dir_path, f'cpu-result.xlsx')
    if os.path.exists(result_path) == True:
        os.remove(result_path)
    for file_name in os.listdir(dir_path):#case#loop
        if os.path.splitext(file_name)[-1] == '.txt':
            filepath = os.path.join(dir_path, file_name)
            print('parse', filepath)
            if os.path.isfile(filepath):
                try:
                    result = parse_top(filepath)
                    pf = pd.DataFrame(result)
                    ds = pf.describe()
                except ValueError as e:
                    print(file_name, e)
                    continue
                
                if  os.path.exists(result_path) != True:
                    print('excel file is not exist,create it')
                    pf.to_excel(result_path)
                writer = pd.ExcelWriter(result_path, engine='openpyxl', mode='a')
                # writer = pd.ExcelWriter(result_path, engine='openpyxl')
                # if os.path.exists(result_path):
                #     book = load_workbook(result_path)
                #     writer.book = book
                
                pf.fillna(' ', inplace=True)
                pf.to_excel(writer, sheet_name=os.path.splitext(file_name)[0], index_label='index')
                ds.to_excel(writer, sheet_name=os.path.splitext(file_name)[0]+ '-ds', index_label='index')
                writer.save()
    print('数据处理结果', result_path, '\n下次测试前，记得删除或者重命名，避免数据累加')
                
                
main()








