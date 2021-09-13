import os, datetime, time
import pandas as pd
from openpyxl import load_workbook

file_path = r'D:\github\python\vhal'#待分析目录
file_name = []
list_obj = []

# to be parsed file
file_name.append("system_cpu")
file_name.append("vhal_cpu")
file_name.append("spi_count")
file_name.append("spi_size")
file_name.append("eth_count")
file_name.append("eth_size")

#parse time
start_time = '17:29:05'
end_time = '18:49:54'

class To_be_analysed:
    def __init__(self,name,file):
        self.name = name
        self.file = file
        self.dict = {}

    def create_dict(self):
        with open(self.file,mode='r',encoding='utf-8') as f:
            content = f.readlines()
            self.dict.clear()
            for line in content:
                self.dict.update({line.split()[0]:line.split()[1]})


def main():
    for fn in file_name: 
        obj = To_be_analysed(fn,os.path.join(file_path,fn+".txt"))
        obj.create_dict()
        list_obj.append(obj)

    time1 = datetime.datetime.strptime(start_time,'%H:%M:%S')
    cur_time = start_time
    parse_result = []

    while(cur_time != end_time):
        dict_result = {}
        for obj in list_obj:
            if({cur_time}.issubset(obj.dict.keys())):
                dict_result['time'] = cur_time
                dict_result[obj.name] = obj.dict[cur_time]
        if (dict_result != {}):
            parse_result.append(dict_result)
        time1 = time1 + datetime.timedelta(seconds=1)
        cur_time = time1.strftime("%H:%M:%S")

    result_path = os.path.join(file_path, f'parse_result.csv')
    if os.path.exists(result_path) == True:
        os.remove(result_path)

    pf = pd.DataFrame(parse_result)
    pf.to_csv(result_path, mode='w', index=False)
    # pf.to_excel(result_path,sheet_name="test",index=False)
    print("well done")

main()