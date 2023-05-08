import os 
from glob import glob
from bs4 import BeautifulSoup
import pandas as pd
import re



def parse(soup, f_name):
   
    if 'ナンバーズ3' in f_name:
        tables = soup.select('table.typeTK')
        for table in tables:
            time = table.select_one('thead > tr > th:nth-of-type(2)').text
            number = table.select_one('tbody > tr:nth-of-type(2) > td').text
            day = table.select_one('tbody > tr:first-of-type > td').text

            yield {
                'time': time,
                'day': day,
                'number': number
            }
      
    else:
        trs = soup.select('div.spTableScroll table.typeTK > tbody > tr')
        for tr in trs:
            time = tr.select_one('th').text
            day = tr.select_one('td:first-of-type').text
            number = tr.select_one('td:nth-of-type(2)').text

            yield {
                'time': time,
                'day': day,
                'number': number
            }
        


#path setting
dir_name = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(dir_name, 'html', '*')
print(html_path)

"""
print(glob(html_path)[0])
print(len(glob(html_path)))"""
d_list = []
for path in glob(html_path):
    with open(path, 'r',encoding='utf-8')as f:
        html = f.read()

    f_name = os.path.basename(path)
  
    soup = BeautifulSoup(html,'lxml')
    parsed_dicts = parse(soup, f_name)

    d_list += list(parsed_dicts)

    print(len(d_list))

df = pd.DataFrame(d_list)
df['no'] = df.time.map(lambda s: re.sub('第|回','',s)).astype(int)
df = df.sort_values('no').set_index('no')

df.to_csv('scrapingNo4.csv',index=None,encoding='utf-8-sig')