from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
import re
from urllib.parse import urljoin
from typing import List, Dict, Optional
from main import COUNTRY_TO_ISO3, EventItem, FileItem

def parse_events(html_content: str) -> List[EventItem]:
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    for year_tag in soup.find_all('a', attrs={'name': True}):
        year = year_tag['name']
        span = year_tag.find_next('span', class_='acd-content')
        if not span:
            continue
        ul = span.find('ul')
        if not ul:
            continue
        for li in ul.find_all('li'):
            a = li.find('a')
            if not a:
                continue
            text = a.text.strip()
            match = re.match(r'(\d{4}-\d{2}-\d{2}):\s*(.+?)\s+on\s+(.+)', text)
            if match:
                date, title, date_str = match.groups()
                disaster_type_match = re.match(r'([A-Za-z ]+) in ', title)
                disaster_type = disaster_type_match.group(1).strip() if disaster_type_match else "Unknown"
                url = "https://sentinel-asia.org/EO/" + a['href']

                # 詳細ページから追加情報を取得
                requester = None
                escalation_to_charter = None
                glide_number = None
                country = None
                files = []
                try:
                    detail_res = requests.get(url, timeout=10)
                    detail_res.raise_for_status()
                    detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                    report_ul = detail_soup.find('ul', class_='report-data')
                    if report_ul:
                        for li2 in report_ul.find_all('li'):
                            title_span = li2.find('span', class_='data-title')
                            value_span = li2.find('span', class_='data-value')
                            if not title_span or not value_span:
                                continue
                            title_text = title_span.get_text(strip=True)
                            value_text = value_span.get_text(strip=True)
                            if 'Country' in title_text:
                                country = value_text
                            elif 'Requester' in title_text:
                                requester = value_text
                            elif 'Escalation to the International Charter' in title_text:
                                escalation_to_charter = value_text
                            elif 'GLIDE Number' in title_text:
                                a_tag = value_span.find('a')
                                if a_tag:
                                    glide_number = a_tag.get_text(strip=True)
                                else:
                                    glide_number = value_text

                    # Productセクションからファイル情報を取得
                    product_section = detail_soup.find('h2', string='Product')
                    if product_section:
                        for card in product_section.find_all_next('div', class_='card'):
                            file_name = None
                            file_url = None
                            file_type = None
                            
                            # ファイル名を取得
                            h3 = card.find('h3')
                            if h3:
                                file_name = h3.get_text(strip=True)
                            
                            # ダウンロードリンクを取得
                            download_link = card.find('a', class_='btn-download-new')
                            if download_link and 'href' in download_link.attrs:
                                file_url = urljoin(url, download_link['href'])
                                file_type = file_url.split('.')[-1].lower()
                            
                            if file_name and file_url:
                                files.append(FileItem(
                                    name=file_name,
                                    url=file_url,
                                    file_type=file_type
                                ))

                except Exception as e:
                    print(f"Error fetching details for {url}: {str(e)}")

                iso3 = COUNTRY_TO_ISO3.get(country, None)

                events.append(EventItem(
                    name=title,
                    description=text,
                    disaster_type=disaster_type,
                    country=country,
                    country_iso3=iso3,
                    occurrence_date=date,
                    sa_activation_date=date,
                    requester=requester,
                    escalation_to_charter=escalation_to_charter,
                    glide_number=glide_number,
                    additional_metadata=None,
                    files=files,
                    url=url
                ))
    return events

def save_events_to_json(events: List[EventItem], filename: str = "events.json"):
    events_dict = [event.dict() for event in events]
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(events_dict, f, ensure_ascii=False, indent=2)

def main():
    try:
        print("Fetching events from Sentinel Asia...")
        response = requests.get("https://sentinel-asia.org/EO/EmergencyObservation.html")
        response.raise_for_status()
        events = parse_events(response.text)
        print(f"Found {len(events)} events")
        
        print("Saving events to JSON file...")
        save_events_to_json(events)
        print("Done!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 