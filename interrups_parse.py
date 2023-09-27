import csv, os

# path = os.path.normpath('D:/wangwei1/work/x01/资源开销/irq_begin3.txt')
# filename = 'irq_begin3.txt'
path = r'D:\wangwei1\work\x01\资源开销\irq'


# f = open("irq_begin3.txt",'r',encoding='GB2312')
# print(path)
# f = open(os.path.join(path, file_name),'r',encoding='GB2312')

for file_name in os.listdir(path):
    if os.path.splitext(file_name)[-1] == '.txt':
        outfile = os.path.splitext(file_name)[0] + ".csv"
        csvFile = open( os.path.join(path, outfile),'w',newline='',encoding='utf-8')
        csvRow = []
        writer = csv.writer(csvFile)
        filepath = os.path.join(path, file_name)
        f = open(filepath,'r',encoding='GB2312')
        for line in f:
            csvRow = line.replace(":"," ").split()
            if(csvRow[0] == "CPU0"):
                csvRow.insert(0,' ')
            writer.writerow(csvRow) 
        f.close

