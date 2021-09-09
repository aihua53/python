import argparse
import os
import re
import sys

import pandas as pd
from openpyxl import load_workbook


def parse_vhal(file):
    parse_result = []
    with open(file,mode="r",encoding='utf-8') as f:
        while True:
            dict_result = {}
            try:
                line = f.readline()
            except UnicodeDecodeError:
                f.seek(f.tell()+1)
            if not line:
                break
            re_result = re.search('current SPI can data size:(\d+),\s+summation SPI Can data size:(\d+),\s+SPICanInvokedCount=(\d+),\s+timediff=(\d+)',line)
            if re_result != None:
                (spi_data_size,spi_accumulate,spi_count,spi_time)=re_result.groups()
                data = line.split()[0]
                time = line.split()[1]
                dict_result['data'] = data
                dict_result['time'] = time
                dict_result['spi_data_size'] = spi_data_size
                dict_result['spi_accumulate'] = spi_accumulate
                dict_result['spi_count'] = spi_count
                dict_result['spi_time'] = spi_time
                parse_result.append(dict_result)
    return parse_result


def get_args():
    parse = argparse.ArgumentParser()
    parse.add_argument("-p", "--path", help="Input the file path", required=True)
    return parse.parse_args();

def main(argv):
    dir_path = get_args().path
    print(dir_path)
    # result_path = os.path.join(dir_path, f'vhal_debuglog.xlsx')
    result_path = os.path.join(dir_path, f'vhal_debuglog.csv')
    if os.path.exists(result_path) == True:
        os.remove(result_path)
    
    df_rows = 0
    for file_name in os.listdir(dir_path):
        if os.path.splitext(file_name)[-1] == '.log':
            filepath = os.path.join(dir_path, file_name)
            result = parse_vhal(filepath)
            pf = pd.DataFrame(result)
            pf.to_csv(result_path, mode='a', index=False, header=False)
    print("done")


main(sys.argv)
