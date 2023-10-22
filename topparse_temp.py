import csv
from collections import defaultdict

def extract_columns_to_csv(input_file1, input_file2, output_file):
    data = defaultdict(lambda: ['0', '0'])
  
    # 提取第一个文件的数据
    with open(input_file1, 'r') as in_file:
        lines = in_file.readlines()
        for line in lines:
            cols = line.split()
            if len(cols) > 11: 
                name = ' '.join(cols[11:])
                data[name][0] = cols[8]

    # 提取第二个文件的数据
    with open(input_file2, 'r') as in_file:
        lines = in_file.readlines()
        for line in lines:
            cols = line.split()
            if len(cols) > 11:
                name = ' '.join(cols[11:])
                data[name][1] = cols[8]

    # 将数据写入CSV文件
    with open(output_file, 'w', newline='') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(['name', 'value1', 'value2'])  # 写入表头
        for name, values in data.items():
            writer.writerow([name] + values)

extract_columns_to_csv('376_stop.txt', '277_run.txt', 'output_file.csv')

