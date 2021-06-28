import re, os, numpy
import pandas as pd
from openpyxl import load_workbook

""""
分析目录下所有txt文件，分析结果cpu-result.xlsx保存在指定目录下
每次运行前，记得删除cpu-result.xlsx，不然sheet会不断累加
sheet页名称为文件名
"""
#需要监控的进程
# bilibili
# pid_bilibili = ['com.bilibili.bilithings', 'com.bilibili.bilithings:ijkservice','surfaceflinger','android.hardware.graphics.composer@2.1-service']#除系统user\sys等之外，需要监控的进程

# tencent
pid_tencent = ['com.tencent.wecarnavi','com.tencent.wecarspeech','com.tencent.wecarspeech:coreService', 'com.tencent.wecarflow:coreService','com.tencent.wecarflow','com.tencent.taiservice:coreService']

# other background
pid_others = ['com.chehejia.ssp.edge', 'com.liauto.lanenavi','com.chehejia.fapa','zadas_services','com.chehejia.car.svm','cnss_diag -q -f','com.android.car']

dir_path = r'Z:\performance\voice\0628\data_analysis'#待分析目录
# dir_path = r'Z:\performance\bilibili'#待分析目录

pids = pid_tencent + pid_others

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
                                  'total': numpy.sum([int(user), int(nice), int(sys),int(idle), int(iow), int(irq), int(sirq),int(host)])}, **dict_pid))
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
                          'total': numpy.sum([int(user), int(nice), int(sys), int(idle),int(iow), int(irq), int(sirq),int(host)])}, **dict_pid))
                break
    return result


def main():
    result_path = os.path.join(dir_path, f'cpu-result.xlsx')
    #文件已存在，删除文件
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
    print('数据处理结果', result_path)
                
                
main()








