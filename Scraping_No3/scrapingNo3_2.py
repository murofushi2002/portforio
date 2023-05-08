from bs4 import BeautifulSoup
import requests
import pandas as pd
from time import sleep
with open('ensyuu3.html','r',encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html,'lxml')

a_tags = soup.select('div#jobList.jobList > div > div > div > div > div > div > h2 > span > a')
d_list = []
for a_tag in a_tags:
    
    url =  'https://atsumaru.jp' + a_tag.get('href')

    r = requests.get(url,timeout=10)
    r.raise_for_status()
    sleep(3)
    page_soup = BeautifulSoup(r.content,'lxml')

    address = page_soup.select('td:-soup-contains("地図はこちら") > p:first-of-type')
    tel = page_soup.select('div.telNo > p > strong > a')
    if tel:
        tel_number = tel[0].text
    else:
        tel_number = 'no number'

    if address:
        address_number = address[0].text
    else:
        address_number = 'no address'
    d_list.append({
        'company_address': address_number,
        'company_telephone': tel_number,
    })
    print(1)
df = pd.DataFrame(d_list)
df.to_csv('scrapingNo3.csv',index=None,encoding='utf-8-sig')