from ast import keyword
from gettext import find
import json
import os
import pandas as pd
from openpyxl import load_workbook

path = r'D:\wangwei1\codes\github\python\temp'#待分析目录
keyword = 'reportPerformance: {"cpu"'


def read_log(file_path):
    result = []
    top_process = dict()
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.find(keyword) != -1:
                top_process.clear()
                data_line = line.strip("\n").split()
                time = data_line[0] + " " + data_line[1]
                jsondata = json.loads(data_line[7])
                total_cpu = jsondata["cpu"]["total"]["total"]
                if total_cpu > 90:
                    top_process["time"] = time.split('.')[0]
                    top_process["total"] = total_cpu
                    for data in jsondata["cpu"]["processCpuInfoList"][0:5]:
                        top_process[data["name"]] = str(data["total"])
                    result.append(dict(**top_process))
    return result
 

if __name__ == "__main__":  
    original_data = []
    for file_name in os.listdir(path):
        if os.path.splitext(file_name)[-1] == '.log':
            filepath = os.path.join(path, file_name)
            outfile = os.path.join(path, 'cpu.xlsx')
            if os.path.exists(outfile) == True:              
                original_data = pd.read_excel(outfile)
                save_data = original_data.append(read_log(filepath))
                pd.DataFrame(save_data).to_excel(outfile, index=False)
            else:
                pf = pd.DataFrame(read_log(filepath))
                pf.to_excel(outfile, index=False)







        

