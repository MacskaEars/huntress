import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

class HousingSearcher:
    def __init__(self, headers=None):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def scrape_craigslist(self, zip_code, distance=20):
        print(f"Scraping Craigslist within {distance} miles of {zip_code}...")
        # Note: Craigslist URLs are often subdomain-specific. Defaulting to binghamton for Norwich area, 
        # but a production version would need a mapping or dynamic subdomain detection.
        url = f"https://binghamton.craigslist.org/search/apa?postal={zip_code}&search_distance={distance}"
        results = []
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('li', class_='cl-static-search-result')

            if not listings:
                listings = soup.find_all('div', class_='result-info')

            for li in listings:
                title_elem = li.find('div', class_='title') or li.find('a', class_='result-title')
                price_elem = li.find('div', class_='price') or li.find('span', class_='result-price')
                link_elem = li.find('a')

                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    price = price_elem.text.strip() if price_elem else "N/A"
                    link = link_elem['href']
                    if not link.startswith('http'):
                        link = "https://binghamton.craigslist.org" + link

                    results.append({
                        'source': 'Craigslist',
                        'title': title,
                        'price': price,
                        'job_url': link, # Using job_url for consistency with jobs engine
                        'location': f'Near {zip_code}',
                        'description': 'Check listing for DSS details (Landlord, Utilities, Deposit).',
                        'company': 'Private Landlord/Agency' # Placeholder for consistency
                    })
        except Exception as e:
            print(f"Error scraping Craigslist: {e}")
        return results

def calculate_housing_score(row):
    score = 100
    price_str = str(row['price']).replace('$', '').replace(',', '')
    try:
        price = int(float(price_str))
        if price > 1200: score -= 40
        elif price > 900: score -= 20
        elif price < 700: score += 10
    except:
        pass
    
    desc = str(row['description']).lower()
    if 'dss' in desc or 'section 8' in desc: score += 20
    if 'utilities included' in desc or 'all utilities' in desc: score += 15
    
    return min(max(score, 0), 100)

def run_housing_search(args):
    print("\n" + "="*60)
    print("HUNTRESS HOUSING SEARCH ENGINE")
    print("="*60)

    zip_codes = args.zip if args.zip else ["13815"]
    searcher = HousingSearcher()
    all_results = []

    for z in zip_codes:
        results = searcher.scrape_craigslist(z)
        all_results.extend(results)
        time.sleep(1)

    if all_results:
        df = pd.DataFrame(all_results)
        df['contact_info'] = "Check listing link"
        df['score'] = df.apply(calculate_housing_score, axis=1)
        # Sort by score descending
        df = df.sort_values(by='score', ascending=False)
        return df
    return None
