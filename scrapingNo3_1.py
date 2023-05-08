from selenium import webdriver
from time import sleep

options = webdriver.ChromeOptions()
options.add_argument('--incognito')
options.add_argument('--headless')





driver = webdriver.Chrome(
    executable_path="C:/Users/shoug/python/sraping_lesson/tools/chromedriver.exe",
    options=options)

driver.implicitly_wait(10)

driver.get('https://atsumaru.jp/area/7/list?sagid=all')
sleep(3)

height = driver.execute_script('return document.body.scrollHeight')
new_height = 0
count = 0
while True:
    count += 1
    print(count)
  

    driver.execute_script(f'window.scrollTo(0,{height})')
    if count > 90:
        sleep(15)
    sleep(10)
    new_height = driver.execute_script('return document.body.scrollHeight')
    if height == new_height:
        break

    height = new_height
    





with open('ensyuu3.html','w',encoding='utf-8') as f:
        f.write(driver.page_source)

