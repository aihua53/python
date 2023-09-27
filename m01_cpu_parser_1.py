import json

def read_txt(inputpath, outputpath):
    with open(outputpath, 'w', encoding='utf-8') as file:
        with open(inputpath, 'r', encoding='utf-8') as infile:
            output_lines=[]
            for line in infile:
                data_line = line.strip("\n").split()
                jsondata=json.loads(data_line[7])
                cpu_use=str(jsondata["cpu"]["total"]["total"])
                if jsondata["cpu"]["total"]["total"]>90:
                    print_line=[]
                    print_line.append(data_line[0]+"-"+data_line[1])
                    print_line.append(cpu_use)
                    for data in jsondata["cpu"]["processCpuInfoList"][0:5]:
                        print_line.append(data["name"]+"--"+str(data["total"]))
                    output_lines.append(print_line)
            
            # 写入方法
            for line in output_lines:
                data = '' + '    '.join(str(i) for i in line) + '\n'  # 用\t隔开
                file.write(data)
if __name__ == "__main__":
    input_path = 'cpu20221029.txt'
    output_path = 'cpu20221029.csv'
    read_txt(input_path, output_path)

