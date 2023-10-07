import re
from datetime import datetime

file_name = "dvmlog"  # 替换为您想要读取的文件名
output_file = "out.txt"
longTimeConsume = "lognTimeConsume.txt"
timeConsume = 100

#获取文件行数
f=open(file_name)
length=len(f.readlines())

# print(length)

preline = ""

#获取第一行内容
with open(file_name) as f:
    first_line = f.readline()
    preline = first_line
    pattern = r"\d{2}:\d{2}:\d{2}.\d{3}"
    match = re.search(pattern, first_line)
    if match:
        time_format = "%H:%M:%S.%f"
        time1 = datetime.strptime(match.group(), time_format)



#计算持锁时间
with open(file_name) as f, open(output_file, "w") as out_file:
    for line in f.readlines()[1:length]:
        pattern = r"\d{2}:\d{2}:\d{2}.\d{3}"
        match = re.search(pattern, line)    
        columns = line.split(",")


        if match:
            time_format = "%H:%M:%S.%f"
            time2 = datetime.strptime(match.group(), time_format)
            time_difference = time2 - time1

            time_difference_ms = round(time_difference.total_seconds() * 1000)
            # time_difference = str(time_difference)

            
            
            output_str = f"{time_difference_ms} time:{columns[3]} {preline}"
            out_file.write(output_str)  # 写入文件

            time1 = time2
            preline = line


# 按迟锁函数出现的次数降序输出
name_counts = {}

with open(output_file, "r") as file:
    for line in file:
        elements = line.strip().split(",")
        if len(elements) >= 7:
            name = elements[6].strip()
            if name in name_counts:
                name_counts[name] += 1
            else:
                name_counts[name] = 1

sorted_name_counts = sorted(name_counts.items(), key=lambda x: x[1], reverse=True)
for name, count in sorted_name_counts:
    print(f"Name: {name} - Count: {count}")




#过滤耗时大于100ms的数据
def filter_log(line):
        first_element = line.split(' ')[0] 
        # 有些日志行可能不以数字开头，我们需要处理这些情况
        if first_element.isdigit() and int(first_element) > timeConsume:
            return line
    

with open(output_file, "r") as file, open(longTimeConsume, "w") as out_file:
    for line in file:
        filtered_lines = filter_log(line)
        if(filtered_lines != None):
            out_file.write(filtered_lines)  # 写入文件




# 耗时大于100ms的数据按迟锁函数出现的次数降序输出
name_counts = {}

with open(longTimeConsume, "r") as file:
    for line in file:
        elements = line.strip().split(",")
        if len(elements) >= 7:
            name = elements[6].strip()
            if name in name_counts:
                name_counts[name] += 1
            else:
                name_counts[name] = 1

sorted_name_counts = sorted(name_counts.items(), key=lambda x: x[1], reverse=True)
for name, count in sorted_name_counts:
    print(f"Name: {name} - Count: {count}")