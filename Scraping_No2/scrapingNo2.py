from bs4 import BeautifulSoup
import requests
import pandas as pd
from time import sleep

base_url = 'https://next.rikunabi.com/rnc/docs/cp_s00700.jsp?jb_type_long_cd=0100000000&wrk_plc_long_cd=0313000000&wrk_plc_long_cd=0313100000&wrk_plc_long_cd=0314000000&curnum={}'

d_list = []
for i in range(3):
    url = base_url.format(1+50*i)
    sleep(3)
    r = requests.get(url,timeout=10)
    r.raise_for_status()


    soup = BeautifulSoup(r.content,'lxml')
    page_urls = soup.select('a:-soup-contains(企業ページ)')

    for page_url in page_urls:
        page_url = 'https://next.rikunabi.com' + page_url.get('href')
        
        sleep(3)

        page_r = requests.get(page_url,timeout=10)
        page_r.raise_for_status()

        page_soup = BeautifulSoup(page_r.content,'lxml')

        company_name = page_soup.select_one('.rnn-breadcrumb > li:last-of-type').text
        url_in_tag =  page_soup.select_one('.rnn-col-11:last-of-type a')
        company_url = url_in_tag.get('href') if url_in_tag else None
        print('='*50)
        d_list.append({
            'company_name': company_name,
            'company_url': company_url,
        })
        print(company_name)
        print(company_url)

        print(d_list[-1])

df = pd.DataFrame(d_list)
df.to_csv('scrapingNo2.csv',index=None,encoding='utf-8-sig')