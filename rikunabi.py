import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 定数定義
BASE_LIST_URL = (
    'https://next.rikunabi.com/rnc/docs/cp_s00700.jsp?jb_type_long_cd=0100000000'
    '&wrk_plc_long_cd=0313000000&wrk_plc_long_cd=0313100000&wrk_plc_long_cd=0314000000'
    '&curnum={}'
)
MAX_PAGE_COUNT = 3
SLEEP_INTERVAL = 3

# 結果格納用リスト
company_data_list = []

def fetch_html(url):
    """指定URLのHTMLを取得"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None

def extract_company_links(html):
    """リストページから企業詳細ページへのリンクを抽出"""
    soup = BeautifulSoup(html, 'lxml')
    links = []
    for a in soup.select('a[href]'):
        if '企業ページ' in a.text:
            href = a.get('href')
            if href and href.startswith('/cp/'):
                links.append('https://next.rikunabi.com' + href)
    return links

def extract_company_info(detail_url):
    """企業詳細ページから会社名と企業URLを抽出"""
    html = fetch_html(detail_url)
    if not html:
        return None, None

    soup = BeautifulSoup(html, 'lxml')
    try:
        # パンくずリストから会社名を取得
        company_name_elem = soup.select_one('.rnn-breadcrumb > li:last-of-type')
        company_name = company_name_elem.text.strip() if company_name_elem else '不明'

        # 企業公式URL（リンク）を取得
        url_link_elem = soup.select_one('.rnn-col-11:last-of-type a')
        company_url = url_link_elem.get('href') if url_link_elem else None

        return company_name, company_url
    except Exception as e:
        print(f"[ERROR] Failed to parse {detail_url}: {e}")
        return None, None

def scrape_rikunabi():
    """Rikunabi NEXTから企業情報をスクレイピング"""
    for i in range(MAX_PAGE_COUNT):
        list_url = BASE_LIST_URL.format(1 + 50 * i)
        print(f"Fetching listing page: {list_url}")
        list_html = fetch_html(list_url)
        if not list_html:
            continue

        company_links = extract_company_links(list_html)
        print(f"  Found {len(company_links)} company links")

        for link in company_links:
            time.sleep(SLEEP_INTERVAL)
            company_name, company_url = extract_company_info(link)
            if not company_name:
                continue

            print("=" * 60)
            print(f"Company: {company_name}")
            print(f"URL: {company_url}")
            company_data_list.append({
                'company_name': company_name,
                'company_url': company_url
            })
        time.sleep(SLEEP_INTERVAL)

def save_to_csv(data_list, filename='rikunabi_scraped_companies.csv'):
    """企業データをCSV形式で保存"""
    df = pd.DataFrame(data_list)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"\n✅ Data saved to {filename}")

if __name__ == '__main__':
    scrape_rikunabi()
    save_to_csv(company_data_list)
