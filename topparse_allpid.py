import re, os, numpy
import pandas as pd
from openpyxl import load_workbook

""""
分析目录下所有txt文件，分析结果cpu-result.xlsx保存在指定目录下
每次运行前，记得删除cpu-result.xlsx，不然sheet会不断累加
sheet页名称为文件名
"""


# 待分析目录,根据实际情况修改
dir_path = r'Z:\issues\x01\0620-master\cpu\1'#待分析目录
# dir_path = r'D:\wangwei1\codes\github\python' #待分析目录



def parse_top(cpu_path):
    result = []  # 存储数据
    tasks = user = nice = sys = idle = iow = irq = sirq = host = 0
    dict_allpid = dict()
    isStart = False
  
    with open(cpu_path, mode='r', encoding='utf-8') as f:
        line = f.readline()
        while True:
            if line.strip().startswith('Tasks'):
                tasks = line.split()[1]
                try:
                    if user:
                        result.append(
                            dict({'time':sampling_time,'tasks': int(tasks), 'user': int(user), 'nice': int(nice), 'sys': int(sys),'idle': int(idle), 'iow': int(iow), 'irq': int(irq), 'sirq': int(sirq), 'host': int(host),
                                  'total': numpy.sum([int(user), int(nice), int(sys),int(idle), int(iow), int(irq), int(sirq),int(host)])}, **dict_allpid))
                        user = nice = sys = idle = iow = irq = sirq = host = 0
                        dict_allpid.clear()
                except ValueError:
                    print(user, type(user))

            if(re.match(r'2022-',line))!=None:
                sampling_time = line
                isStart = False

            sys_result = re.search(r'(\d+)%cpu\s+(\d+)%user\s+(\d+)%nice\s+(\d+)%sys\s+(\d+)%idle\s+(\d+)%iow\s+(\d+)%irq\s+(\d+)%sirq\s+(\d+)%host.*', line)
            if sys_result:
                (total_ps, user, nice, sys, idle, iow, irq, sirq, host) = sys_result.groups()

            if isStart and line != '\n':
                dict_allpid[line.split()[-1]] = float(line.split()[8])

            if line.strip().startswith("PID"):
                isStart = True
            
            line = f.readline()
            if not line:
                #添加最后一次数据
                result.append(
                    dict({'time':sampling_time, 'tasks': int(tasks), 'user': int(user), 'nice': int(nice), 'sys': int(sys), 'idle': int(idle), 'iow': int(iow), 'irq': int(irq), 'sirq': int(sirq), 'host': int(host),
                          'total': numpy.sum([int(user), int(nice), int(sys), int(idle),int(iow), int(irq), int(sirq),int(host)])}, **dict_allpid))
                break
    return result


def main():
    result_path = os.path.join(dir_path, f'cpu-result.xlsx')
    #文件已存在，删除文件
    if os.path.exists(result_path) == True:
        os.remove(result_path)
    for file_name in os.listdir(dir_path):
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

                pf.fillna(' ', inplace=True)
                pf.to_excel(writer, sheet_name=os.path.splitext(file_name)[0], index_label='index')
                ds.to_excel(writer, sheet_name=os.path.splitext(file_name)[0]+ '-ds', index_label='index')
                writer.save()
    print('done!!!', result_path)
                
                
main()








