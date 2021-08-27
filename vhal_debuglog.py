import re, os
# import pandas as pd
# from openpyxl import load_workbook

def parse_vhal(file):
    with open(file,mode="r",encoding='utf-8') as f:
        content = f.readlines()
        for line in content:
            re_result = re.search('current SPI can data size:(\d)+summation SPI Can data size(\d)+SPICanInvokedCount=(\d)',line)
            if re_result != None:
                print(re_result)

def main():
    parse_vhal(r'D:\github\python\test.log')


main()