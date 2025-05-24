from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel
import re
from urllib.parse import urljoin
import json

app = FastAPI(
    title="Sentinel Asia EOR API",
    description="Sentinel Asiaの緊急観測要請（EOR）情報を取得するAPI",
    version="2.0.0"
)

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ISO3国コードの簡易マッピング（必要に応じて拡張）
COUNTRY_TO_ISO3 = {
    # 東アジア
    "Japan": "JPN", "China": "CHN", "South Korea": "KOR", "Korea": "KOR", "North Korea": "PRK", "Taiwan": "TWN", 
    "Mongolia": "MNG",
    # 東南アジア
    "Philippines": "PHL", "Vietnam": "VNM", "Thailand": "THA", "Myanmar": "MMR", "Cambodia": "KHM", 
    "Laos": "LAO", "Lao People's Democratic Republic (Laos)": "LAO", "Lao PDR": "LAO",
    "Malaysia": "MYS", "Singapore": "SGP", "Indonesia": "IDN", "Brunei": "BRN", "Timor-Leste": "TLS",
    # 南アジア
    "India": "IND", "Pakistan": "PAK", "Bangladesh": "BGD", "Nepal": "NPL", "Sri Lanka": "LKA", "Bhutan": "BTN", "Maldives": "MDV", 
    # 中央アジア
    "Kazakhstan": "KAZ", "Uzbekistan": "UZB", "Kyrgyzstan": "KGZ", "Kyrgyz": "KGZ", "Tajikistan": "TJK", "Turkmenistan": "TKM",
    # 西アジア（中東）
    "Afghanistan": "AFG", "Iran": "IRN", "Iraq": "IRQ", "Syria": "SYR", "Lebanon": "LBN", "Israel": "ISR", "Jordan": "JOR", "Turkey": "TUR", "Saudi Arabia": "SAU", 
    "United Arab Emirates (UAE)": "ARE", "United Arab Emirates": "ARE", "UAE": "ARE",
    "Qatar": "QAT", "Bahrain": "BHR", "Kuwait": "KWT", "Oman": "OMN", "Yemen": "YEM", "Palestine": "PSE",
    # 南コーカサス
    "Armenia": "ARM", "Azerbaijan": "AZE", "Georgia": "GEO",
    # 太平洋諸島
    "Australia": "AUS", "New Zealand": "NZL", "Papua New Guinea": "PNG", "Fiji": "FJI", 
    "Solomon Islands": "SLB", "Solomon": "SLB",
    "Vanuatu": "VUT", "Samoa": "WSM", "Tonga": "TON", "Micronesia": "FSM", "Palau": "PLW", "Marshall Islands": "MHL", "Nauru": "NRU", "Kiribati": "KIR", "Tuvalu": "TUV"
}

# --- Pydanticモデル ---
class FileItem(BaseModel):
    name: str
    description: Optional[str] = None
    url: str
    file_type: Optional[str] = None

class EventItem(BaseModel):
    name: str
    description: str
    disaster_type: str
    country: str
    country_iso3: Optional[str]
    occurrence_date: str
    sa_activation_date: Optional[str] = None
    requester: Optional[str] = None
    escalation_to_charter: Optional[str] = None
    glide_number: Optional[str] = None
    additional_metadata: Optional[Dict[str, str]] = None
    files: List[FileItem] = []
    url: Optional[str] = None

class CountryItem(BaseModel):
    name: str
    iso3: str

class MetadataItem(BaseModel):
    description: str
    licence: str
    methodology: str
    caveats: Optional[str] = None

class ProductItem(BaseModel):
    date: Optional[str] = None
    title: Optional[str] = None
    download_url: Optional[str] = None
    view_url: Optional[str] = None
    file_type: Optional[str] = None

def load_events_from_json(filename: str = "events.json") -> List[EventItem]:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            events_data = json.load(f)
            return [EventItem(**event) for event in events_data]
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Please run scraper.py first.")
        return []
    except Exception as e:
        print(f"Error loading events from JSON: {str(e)}")
        return []

def get_all_countries(events: List[EventItem]) -> List[CountryItem]:
    seen = set()
    countries = []
    for event in events:
        if event.country and event.country not in seen:
            seen.add(event.country)
            countries.append(CountryItem(name=event.country, iso3=event.country_iso3 or ""))
    return countries

def parse_products(html_content: str, base_url: str) -> List[ProductItem]:
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    for card in soup.select('div.col.card'):
        date_tag = card.find('div', class_='card-date')
        date = date_tag.text.strip() if date_tag else None
        title_tag = card.find('h3')
        title = title_tag.get_text(separator=' ', strip=True) if title_tag else None
        download_a = card.find('a', class_='btn-download-new')
        download_url = urljoin(base_url, download_a['href']) if download_a and download_a.has_attr('href') else None
        view_a = card.find('a', class_='btn-view')
        view_url = urljoin(base_url, view_a['href']) if view_a and view_a.has_attr('href') else None
        file_type = None
        if download_url:
            file_type = download_url.split('.')[-1].split('?')[0].lower()
        products.append(ProductItem(
            date=date,
            title=title,
            download_url=download_url,
            view_url=view_url,
            file_type=file_type
        ))
    return products

# --- エンドポイント ---
@app.get("/get_countries", response_model=List[CountryItem])
async def get_countries():
    try:
        events = load_events_from_json()
        return get_all_countries(events)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_metadata", response_model=MetadataItem)
async def get_metadata():
    return MetadataItem(
        description="Sentinel Asia is an international cooperation project that utilizes space technology to contribute to disaster management in the Asia-Pacific region.",
        licence="The obtained files cannot be modified. When publishing the obtained files, please include credits as referenced in each file. All products are provided by Sentinel Asia and must be attributed accordingly.",
        methodology="Automatically collected and parsed from the official website.",
        caveats="Some country names and disaster types may contain errors due to automatic extraction."
    )

@app.get("/get_events", response_model=List[EventItem])
async def get_events(
    countryiso3s: Optional[str] = Query(None, description="カンマ区切りのISO3国コード"),
    start_date: Optional[str] = Query(None, description="YYYYMMDDまたはYYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYYMMDDまたはYYYY-MM-DD")
):
    try:
        events = load_events_from_json()
        # フィルタリング
        if countryiso3s:
            iso3_list = [c.strip().upper() for c in countryiso3s.split(",")]
            events = [e for e in events if e.country_iso3 and e.country_iso3 in iso3_list]
        if start_date:
            start_date = start_date.replace("-", "")
            events = [e for e in events if e.occurrence_date.replace("-", "") >= start_date]
        if end_date:
            end_date = end_date.replace("-", "")
            events = [e for e in events if e.occurrence_date.replace("-", "") <= end_date]
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_products", response_model=List[ProductItem])
async def get_products(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        products = parse_products(response.text, url)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Sentinel Asia EOR API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 