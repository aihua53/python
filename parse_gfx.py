import re, os, numpy
import pandas as pd
from openpyxl import load_workbook
import argparse, sys

# dir_path = r'/home/wangwei1/wangwei1/work/performance/'#待分析目录

def parse(file):
    result = []
    with open(file, mode='r', encoding='utf-8') as f:
        # content = f.readlines()
        while(True):
            line = f.readline()
            if not line:
                break
            total_frames_rendered = re.search(r'Total frames rendered: (\d+)',line)
            if total_frames_rendered:
                total = total_frames_rendered.group(1)
                # result.append(dict({'total':int(total)}))
            Janky_frames = re.search(r'Janky frames: (\d+)',line)
            if Janky_frames:
                janky = Janky_frames.group(1)
                # result.append(dict({'janky':int(janky)}))
            Number_Missed_Vsync = re.search(r'Number Missed Vsync: (\d+)',line)
            if Number_Missed_Vsync:
                missed = Number_Missed_Vsync.group(1)
                result.append(dict({'total':int(total),'janky':janky,'missed':int(missed),'janky rate':int(janky)/int(total),'missed rate':int(missed)/int(total)}))
        return result

def get_args():
    parse = argparse.ArgumentParser()
    parse.add_argument("-p", "--path", help="Input the file path", required=True)
    return parse.parse_args();

def main(argv):
    print(get_args())
    dir_path = get_args().path
    result_path = os.path.join(dir_path, f'result.xlsx')
    if os.path.exists(result_path) == True:
        os.remove(result_path)
    for file_name in os.listdir(dir_path):
        if os.path.splitext(file_name)[-1] == '.txt':
            filepath = os.path.join(dir_path, file_name)
            if os.path.isfile(filepath):
                try:
                    parse_result = parse(filepath)
                    pf = pd.DataFrame(parse_result)
                    ds = pf.describe()
                except ValueError as e:
                    print(e)

                if  os.path.exists(result_path) != True:
                    pf.to_excel(result_path)
                    
                writer = pd.ExcelWriter(result_path, engine='openpyxl', mode='a')
                pf.fillna(' ', inplace=True)
                pf.to_excel(writer, sheet_name=os.path.splitext(file_name)[0], index_label='index')
                # ds.to_excel(writer, sheet_name=os.path.splitext(file_name)[0]+ '-ds', index_label='index')
                writer.save()

# main()
if __name__ == "__main__":
    	main(sys.argv)