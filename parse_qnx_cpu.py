import re
import pandas as pd


def cpu_avg():
    with open("D:\wangwei1\Downloads\qnx\qnx5.txt", "r", encoding="utf-8") as f:
        data = f.read()
        f.close()

    findall_str = re.findall("CPU states:\s(.*?)%", data)
    # print(findall_str)
    df = pd.DataFrame({'col1': findall_str})
    df['col1'] = pd.to_numeric(df['col1'], errors='coerce')
    avg = df['col1'].mean()
    print("CPU states平均值是", avg)
    df.to_excel('D:\wangwei1\Downloads\qnx\data.xlsx')


if __name__ == '__main__':
    cpu_avg()
