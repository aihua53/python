import re
from datetime import datetime

file_name = "temp.txt"  # 替换为您想要读取的文件名
output_file = "out.txt"

#获取dvmlocklog的文件行数
f=open(file_name)
length=len(f.readlines())

preline = ""

#获取第一行内容
with open(file_name) as f:
    first_line = f.readline()
    preline = first_line
    pattern = r"\d{2}:\d{2}:\d{2}.\d{3}"
    match = re.search(pattern, first_line)
    if match:
        print(match.group())
        time_format = "%H:%M:%S.%f"
        time1 = datetime.strptime(match.group(), time_format)



#打开文件dvmlocklog，打印前10行内容
with open(file_name) as f, open(output_file, "w") as out_file:
    for line in f.readlines()[1:length]:
        pattern = r"\d{2}:\d{2}:\d{2}.\d{3}"
        match = re.search(pattern, line)    
        columns = line.split(",")


        if match:
            time_format = "%H:%M:%S.%f"
            time2 = datetime.strptime(match.group(), time_format)
            time_difference = time2 - time1
            #time_difference转换为字符串类型
            time_difference_ms = round(time_difference.total_seconds() * 1000)
            time_difference = str(time_difference)

            
            output_str = f"{time_difference_ms} time:{columns[3]} {preline}"
            out_file.write(output_str)  # 写入文件

            time1 = time2
            preline = line


# # 打开文件
# with open(output_file, "r") as file:
#     # 逐行读取文件内容
#     for line in file:
#         # 使用逗号作为分隔符，切割每行数据
#         elements = line.strip().split(",")
#         # 检查每行是否包含至少七个元素
#         if len(elements) >= 7:
#             # 提取第七个元素
#             seventh_element = elements[6]
#             # 打印第七个元素
#             print(seventh_element)
#         else:
#             print("行数据不足七个元素")      

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

# for name, count in name_counts.items():
#     print(f"Name: {name} - Count: {count}")