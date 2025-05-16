import time
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 基本設定
BASE_URL = 'https://employment.en-japan.com'
LISTING_URL_TEMPLATE = (
    'https://employment.en-japan.com/wish/search_list/?companytype=0&worktype=0&areaid=23_24_21_50'
    '&occupation=101000_102500_103000_103500_104500_105000_105500'
    '&indexNoWishArea=0&sort=wish&pagenum={}'
)
MAX_PAGE_INDEX = 3

# データ格納用リスト
company_data_list = []

def fetch_html(url):
    """指定URLのHTMLを取得"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def extract_company_info(job_element):
    """求人要素から会社名と詳細ページのURLを抽出"""
    try:
        company_name = job_element.find('span', class_='company').text.strip()
        detail_path = job_element.find('a').get('href')
        detail_url = BASE_URL + detail_path

        # En-gage 形式への変換
        if 'fromSearch' in detail_url:
            company_id = detail_path.replace('/desc_eng_', '').split('/')[0]
            detail_url = f'https://en-gage.net/recruit/?getFromEmploy={company_id}'

        return company_name, detail_url
    except Exception as e:
        print(f"Error extracting job element: {e}")
        return None, None

def get_company_homepage(detail_url):
    """会社の詳細ページから企業公式URLを取得"""
    html = fetch_html(detail_url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')
    try:
        if 'PK' in detail_url:
            # employment.en-japan.com パターン
            h2_elements = [h2 for h2 in soup.find_all('h2', class_='text') if '会社概要' in h2.text]
            if not h2_elements:
                return None
            company_summary = h2_elements[0].find_parent('div').find_parent('div')
            for row in company_summary.find_all('tr'):
                if row.find('th').text.strip() == '企業ホームページ':
                    return row.find('td').find('a').text.strip()
        elif 'getFromEmploy' in detail_url:
            # en-gage.net パターン
            summary_table = soup.find('table', class_='companyTable')
            for row in summary_table.find_all('tr'):
                if row.find('th').text.strip() == '企業WEBサイト':
                    return row.find('td').find('a').get('href').strip()
    except Exception as e:
        print(f"Error parsing company homepage from {detail_url}: {e}")
    return None

def scrape_job_listings():
    """求人リストページから情報を収集"""
    for page_index in range(1, MAX_PAGE_INDEX + 1):
        page_url = LISTING_URL_TEMPLATE.format(page_index)
        print(f"Accessing: {page_url}")
        html = fetch_html(page_url)
        if not html:
            continue

        soup = BeautifulSoup(html, 'lxml')
        job_elements = soup.find_all('div', class_='jobNameArea')
        print(f"  Found {len(job_elements)} job listings on page {page_index}")

        for job_elem in job_elements:
            company_name, detail_url = extract_company_info(job_elem)
            if not company_name or not detail_url:
                continue

            time.sleep(3)  # polite delay before accessing detail page
            homepage_url = get_company_homepage(detail_url)
            print(f"  ✔ {company_name}: {homepage_url}")

            company_data_list.append({
                'company_name': company_name,
                'company_url': homepage_url
            })
        time.sleep(3)  # polite delay before next listing page

def save_to_csv(data_list, filename='en_job_scraped_companies.csv'):
    """収集データをCSVファイルに保存"""
    df = pd.DataFrame(data_list)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"\n✅ Data saved to {filename}")

if __name__ == '__main__':
    scrape_job_listings()
    save_to_csv(company_data_list)
