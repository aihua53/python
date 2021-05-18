import re, os, numpy
import pandas as pd
from openpyxl import load_workbook

path = r'/home/wangwei1/wangwei1/work/performance/'
file_path =path + 'dump_car.txt'#待分析文件
parse_result = []

def parse(file_path):
    result = []
    d_callback_cout = {}
    d_registered_signal = {}
    with open(file_path, mode='r', encoding='utf-8') as f:
        # content = f.readlines()
        # p = re.compile(r"Package Name:(.*)\s+Total Callback:(\d+)")
        # line = list(filter(lambda x: re.search(p, x), content))
        # items = [[re.search(p, x).group(1), re.search(p, x).group(2)] for x in line]
        while True:
            line = f.readline()
            match_result = re.search(r'Package Name:(.*)\s+Total Callback:(\d+)',line)
            match_result_2 = re.search(r'package: \[(.*)\] Actions:',line)
            if match_result:
                process = match_result.group(1)
                count = match_result.group(2)
                d_callback_cout[process] = count
            if match_result_2:
                process = match_result_2.group(1)
                line = f.readline()
                count = re.search(r'Buffer Size:(\d+)',line).group(1)
                d_registered_signal[process] = count            
            if not line:
                break
        for key in d_callback_cout.keys():
            result.append(dict({'process_name':key,'callback_count':d_callback_cout[key],'registered_count':d_registered_signal[key]}))
        print(result)
        return result


def main():
    result_path = os.path.join(path, f'cpu-result.xlsx')
    if os.path.exists(result_path) == True:
        os.remove(result_path)
    try:
        parse_result = parse(file_path)
        pf = pd.DataFrame(parse_result)
    except ValueError as e:
        print(e)

    if  os.path.exists(result_path) != True:
        print('excel file is not exist,create it')
        pf.to_excel(result_path)
    writer = pd.ExcelWriter(result_path, engine='openpyxl', mode='a')


main()