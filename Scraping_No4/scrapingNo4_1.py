from time import sleep
import re
from selenium import webdriver
import os

options = webdriver.ChromeOptions()
options.add_argument('--incognito')
options.add_argument('--headless')

driver = webdriver.Chrome(
    executable_path="C:/Users/shoug/python/sraping_lesson/tools/chromedriver.exe",
    options=options)

driver.implicitly_wait(10)

driver.get('https://www.mizuhobank.co.jp/retail/takarakuji/check/numbers/backnumber/index.html')
sleep(3)

latest_links = driver.find_elements_by_css_selector('tr.js-backnumber-temp-a > td:first-of-type > a')
backnumber_links = driver.find_elements_by_css_selector('tr.js-backnumber-temp-b > td > a')

urls = [e.get_attribute('href') for e in latest_links + backnumber_links]

dir_name = os.path.dirname(os.path.abspath(__file__))


for i, url in enumerate(urls):
  
    
    print('=' *30, i, '='*30)
    print(url)
    driver.get(url)
    sleep(5)

    html = driver.page_source

    title = re.sub(r'[\\/:*?"<>|]+','',driver.title)
  
#    p = rf'C:/Users/shoug/python/scraping/html/{title}.html'
    p = os.path.join(dir_name,'html',f'{title}.html')
    with open(p, 'w', encoding='utf-8_sig') as f:
        f.write(html)

sleep(3)

driver.quit()