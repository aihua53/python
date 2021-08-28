import re, os
# import pandas as pd
# from openpyxl import load_workbook


def parse_vhal(file):
    with open(file,mode="r",encoding='utf-8') as f:
        while True:
            try:
                line = f.readline()
            except UnicodeDecodeError:
                # print("'utf-8' codec can't decode byte:",line)
                continue
            # if not line:
            if len(line) == 0:
                print("done")
                break
            re_result = re.search('current SPI can data size:(\d+),\s+summation SPI Can data size:(\d+),\s+SPICanInvokedCount=(\d+),\s+timediff=(\d+)',line)
            if re_result != None:
                (spi_data_size,spi_accumulate,spi_count,spi_time)=re_result.groups()
                data = line.split()[0]
                time = line.split()[1]
                print(data,time,spi_data_size,spi_accumulate,spi_count,spi_time)



def main():
    parse_vhal(r'D:\github\python\test.log')


main()