import argparse
import os, re, sys, json, time
import pandas as pd
from openpyxl import load_workbook

file_path = r'D:\github\python\cpuMonitor'
log = os.path.join(file_path, 'cpu_jason.log')

def parse_cpu(log):
    print(log)
    
    with open(log,mode='r',encoding='utf-8') as f:
        content = f.readlines()

        parse_result = []
        for line in content:
            j = json.loads(line)

            dict = {}
            time_stamp = j['timestamp']
            loc_time = time.localtime(int(str(time_stamp)[0:10]))
            time1 = time.strftime("%Y-%m-%d %H:%M:%S",loc_time)
            dict['time'] = time1

            if j['cpu']['total']['total'] < 50:
                continue
            dict['total'] = j['cpu']['total']['total']

            for i in range(0,14):
                try:
                    dict[j['cpu']['processCpuInfoList'][i]['name']] = j['cpu']['processCpuInfoList'][i]['total']
                except:
                    break
            parse_result.append(dict)
        
        result_path = os.path.join(file_path, 'parse_result.csv')
        if os.path.exists(result_path) == True:
            os.remove(result_path)

        pf = pd.DataFrame(parse_result)
        pf.to_csv(result_path, mode='w', index=False)
        print("well done")

def get_args():
    parse = argparse.ArgumentParser()
    parse.add_argument("-p", "--path", help="Input the file path", required=True)
    return parse.parse_args();

def main(argv):
    file = get_args().path
    parse_cpu(file)

 main(sys.argv)   

# def main():
#     parse_cpu(log)

# main()

