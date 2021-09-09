import os, datetime, time
import pandas as pd
from openpyxl import load_workbook

file_path = r'D:\github\python\vhal'#待分析目录
cpu_file = os.path.join(file_path, f'cpu.txt')
spi_size_file = os.path.join(file_path, f'spi_size.txt')
spi_count_file = os.path.join(file_path, f'spi_count.txt')
eth_size_file = os.path.join(file_path, f'eth_size.txt')
eth_count_file = os.path.join(file_path, f'eth_count.txt')

valuefile = spi_count_file #parsed file

def main():
    with open(cpu_file,mode='r',encoding='utf-8') as f:
        content_cpu = f.readlines()
    cpu_dict = {}

    with open(valuefile,mode='r',encoding='utf-8') as f:
        content_value = f.readlines()
    value_dict = {}
    
    for line in content_cpu:
        cpu_dict.update({line.split()[0]:line.split()[1]})
 
    for line in content_value:
        value_dict.update({line.split()[0]:line.split()[1]})

    start_time = '21:20:51'
    end_time = '22:28:00'
    time1 = datetime.datetime.strptime(start_time,'%H:%M:%S')
    cur_time = start_time
    parse_result = []

    while(cur_time != end_time):
        dict_result = {}
        if({cur_time}.issubset(cpu_dict.keys())):
            dict_result['time'] = cur_time
            dict_result['cpu'] = cpu_dict[cur_time]

        if({cur_time}.issubset(value_dict.keys())):
            dict_result['time'] = cur_time
            dict_result['value'] = value_dict[cur_time]
        
        parse_result.append(dict_result)
        time1 = time1 + datetime.timedelta(seconds=1)
        cur_time = time1.strftime("%H:%M:%S")
    
    result_path = os.path.join(file_path, f'parse_result.csv')
    if os.path.exists(result_path) == True:
        os.remove(result_path)

    pf = pd.DataFrame(parse_result)
    pf.to_csv(result_path, mode='w', index=False)
    print("done")
main()