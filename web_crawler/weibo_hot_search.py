import requests
from lxml import etree
import time
url='https://s.weibo.com/top/summary?Refer=top_hot&topnav=1&wvr='
header={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'}
resp = requests.get (url,headers=header)
resp1 = resp.content.decode(encoding='utf-8',errors='ignore')
resp2=etree.HTML(resp1)
title = resp2.xpath('//*[@id="pl_top_realtimehot"]/table/tbody/tr/td/a/text()')
print (time.strftime("%F,%R")+'微博热搜\n')
for i in range(51):
    print ('  '.join([title[i]]),'\n')
    time.sleep(1)