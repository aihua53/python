import json, os
import pandas as pd

path = r'Z:\temp\dapan\LW433B126P1001333\0306'



def read_txt(inputpath, outputpath):
    df = pd.read_json(inputpath,lines=True,encoding='utf-8')
    #lines = true 表示把每一行都看成是一个字典
    #train.json是Jason类型的数据文件
    df.to_excel(output_path )


if __name__ == "__main__":
    input_path = os.path.join(path, "gfx.txt")
    output_path = os.path.join(path, "gfx.xlsx")
    read_txt(input_path, output_path)


