import os
import sys
import re
import configparser
import time
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import format_cell_range, CellFormat, Color
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from ebaysdk.trading import Connection

# ============================
# 初期設定の読み込み
# ============================
base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
settings_path = os.path.join(base_path, "settings.ini")

appsetting = configparser.ConfigParser()
with open(settings_path, 'r', encoding='utf-8') as f:
    appsetting.read_file(f)

prd = appsetting['prd']
sheet_name = prd.get('sheet_name').replace("'", '')
json_name = prd.get('json_name').replace("'", '')
spread_key = prd.get('spread_key').replace("'", '')

# ============================
# Google Sheets 認証
# ============================
json_path = os.path.join(base_path, json_name)
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
gc = gspread.authorize(credentials)
worksheet = gc.open_by_key(spread_key).worksheet(sheet_name)

# ============================
# URLリストの取得
# ============================
product_url_list = worksheet.col_values(9)[1:]  # 1行目はヘッダーとしてスキップ

# ============================
# 在庫チェック関数
# ============================
def extract_and_convert_to_int(s):
    digits = ''.join(filter(str.isdigit, s))
    return int(digits) if digits else None

def serch_stock(url_list):
    stock_status_list = []
    stock_price_list = []

    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(20)

    for url in url_list:
        stock_check = 2  # 初期状態
        stock_price = '不明'
        print(f"チェック中: {url}")

        while True:
            try:
                driver.get(url)
                WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)
                time.sleep(3)
                break
            except:
                driver.quit()
                time.sleep(30)
                driver = webdriver.Chrome(options=chrome_options)
                driver.implicitly_wait(20)

        soup = BeautifulSoup(driver.page_source, 'lxml')
        html = soup.text

        if 'mercari' in url:
            price = soup.select_one('div[data-testid="price"]')
            if price:
                stock_price = extract_and_convert_to_int(price.text.strip())
                if '購入手続きへ' not in html:
                    stock_check = 0
        elif 'amazon.co.jp' in url:
            price = soup.select_one('span.a-price-whole')
            if price:
                stock_price = extract_and_convert_to_int(price.text.strip())
                if 'カートに入れる' not in html:
                    stock_check = 0
        elif 'page.auctions' in url:
            price = soup.select_one('dd.Price__value')
            if price:
                stock_price = extract_and_convert_to_int(price.text.strip())
                if 'このオークションは終了しています' in html:
                    stock_check = 0
        else:
            print('未対応のショップURL')

        stock_status = '在庫あり' if stock_check == 1 else '在庫なし' if stock_check == 0 else 'データが取れません'
        stock_status_list.append(stock_status)
        stock_price_list.append(stock_price)

    driver.quit()
    return stock_status_list, stock_price_list

# ============================
# 在庫チェック実行
# ============================
stock_status_list, stock_price_list = serch_stock(product_url_list)

# ============================
# Google Sheets への書き込み
# ============================
start_row = 2
cell_updates_status = []
cell_updates_price = []

for i, (status, price) in enumerate(zip(stock_status_list, stock_price_list)):
    time.sleep(4)
    status_cell = worksheet.cell(start_row + i, 5)
    price_cell = worksheet.cell(start_row + i, 12)

    status_cell.value = status or ""
    price_cell.value = price or ""

    # 背景色設定
    if status == '在庫なし':
        format_cell_range(worksheet, f'C{start_row + i}', CellFormat(backgroundColor=Color(0.8, 0.8, 0.8)))
        format_cell_range(worksheet, f'D{start_row + i}', CellFormat(backgroundColor=Color(0.8, 0.8, 0.8)))
    else:
        format_cell_range(worksheet, f'C{start_row + i}', CellFormat(backgroundColor=Color(1, 1, 1)))
        format_cell_range(worksheet, f'D{start_row + i}', CellFormat(backgroundColor=Color(1, 1, 1)))

    cell_updates_status.append(status_cell)
    cell_updates_price.append(price_cell)

worksheet.update_cells(cell_updates_status)
worksheet.update_cells(cell_updates_price)

# ============================
# eBay ID の抽出と在庫終了処理
# ============================
product_id_urls = worksheet.col_values(1)[1:]  # ヘッダー除外
product_ids = []
for url in product_id_urls:
    match = re.search(r'/itm/(\d+)(?:\?|$)', url)
    product_ids.append(match.group(1) if match else None)

api = Connection(config_file="ebay.yaml", domain="api.ebay.com", debug=True)
product_api_status_list = []

for status, item_id in zip(stock_status_list, product_ids):
    if not item_id:
        product_api_status_list.append('ID不明')
        continue

    try:
        if status == '在庫なし':
            api.execute("EndItem", {"ItemID": item_id, "EndingReason": "NotAvailable"})
            print(f"{item_id} 出品終了")

        response = api.execute('GetItem', {'ItemID': item_id})
        item_status = response.dict()['Item']['SellingStatus']['ListingStatus']
        product_api_status_list.append(item_status)
    except:
        product_api_status_list.append('取得不能')

# ============================
# eBay API ステータス書き込み
# ============================
cell_updates_api = []
for i, api_status in enumerate(product_api_status_list):
    time.sleep(4)
    cell = worksheet.cell(start_row + i, 6)
    cell.value = api_status
    cell_updates_api.append(cell)

worksheet.update_cells(cell_updates_api)
print('動作終了')
