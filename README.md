# Sentinel Asia EOR API

Sentinel Asiaの緊急観測要請（EOR: Emergency Observation Request）情報を取得するFastAPIベースのAPIサーバーです。

## APIエンドポイント

本APIは以下のURLでホストされています：
- 本番環境: https://reder-test-o5k8.onrender.com

ローカル環境での開発時は以下のURLを使用します：
- ローカル環境: http://localhost:8000

## APIドキュメント

本APIは以下の2つのインタラクティブなドキュメントを提供しています：

### Swagger UI
- URL: `/docs`
- インタラクティブなAPIドキュメント
- APIエンドポイントのテスト実行が可能
- リクエストパラメータの詳細な説明
- レスポンスのスキーマ定義

### ReDoc
- URL: `/redoc`
- より読みやすい形式のAPIドキュメント
- エンドポイントの詳細な説明
- リクエスト/レスポンスの例
- スキーマの視覚的な表示

## サンプルノートブック

本APIの使用方法を示す2つのJupyter Notebookを提供しています：

### sample_render.ipynb
- RenderでホストされたAPIの基本的な使用方法
- 国リストの取得
- イベント情報の取得とフィルタリング
- プロダクト情報の取得
- データの可視化例

### get_kmz_files.ipynb
- KMZファイルの取得と保存に特化したサンプル
- 特定の国や期間のKMZファイルを一括取得
- ファイルの自動ダウンロードと保存
- エラーハンドリングの例

## 主な機能

- EOR（災害イベント）情報の一覧取得
- 年、国（ISO3コード）、日付範囲によるフィルタリング
- 各EORの詳細情報（requester, escalation_to_charter, glide_number, country等）の自動抽出
- 各EORのファイルリストへのリンク提供
- 利用可能な国リストの取得（アジア・中東・太平洋諸国を網羅）
- サービスのメタデータ取得

## 仕様のポイント

- **国名はEOR詳細ページの「Country」欄から取得**し、ISO3コードもそこからマッピングします。
- 災害イベントの詳細情報（requester, escalation_to_charter, glide_number等）もEOR詳細ページから自動抽出します。
- 国コードはアジア・中東・太平洋諸国を網羅しています。

## ライセンスと利用条件

取得したプロダクト（ファイル）の利用に関して、以下の条件が適用されます：

1. 取得したファイルを加工することはできません。
2. 取得したファイルを掲載するときは各ファイルのクレジットを参考に記載してください。
3. すべてのプロダクトはSentinel Asiaによって提供されており、適切なクレジット表示が必要です。

## インストール

```bash
pip install -r requirements.txt
```

## サーバー起動方法

```bash
conda activate sentinel_api
uvicorn main:app --reload
```

## APIエンドポイント

### 1. 国リスト取得
- `GET /get_countries`
- 利用可能な国名とISO3コードのリストを返します。
- **アジア・中東・太平洋諸国を網羅**

### 2. メタデータ取得
- `GET /get_metadata`
- サービスの説明、ライセンス、手法、注意点などを返します。
- 返却内容:
  - description: サービスの説明
  - licence: 利用条件とライセンス情報
  - methodology: データ収集方法
  - caveats: 注意事項

### 3. 災害イベント情報取得
- `GET /get_events`
- クエリパラメータ:
  - `countryiso3s`: カンマ区切りのISO3国コード（例: JPN,PHL,CHN,IND,IDN,IRN,ISR,SAU,SGP,FJI など）
  - `start_date`: 開始日（YYYYMMDDまたはYYYY-MM-DD）
  - `end_date`: 終了日（YYYYMMDDまたはYYYY-MM-DD）
- 返却内容:
  - name, description, disaster_type, country, country_iso3, occurrence_date, sa_activation_date, requester, escalation_to_charter, glide_number, url など
- **国名・ISO3コード・requester等はEOR詳細ページから自動抽出**

### 4. プロダクト（成果物）情報取得
- `GET /get_products?url=...`
- 指定したEOR詳細ページのURLから、成果物（例: kmzファイル等）のリストを返します。
- 返却内容:
  - date, title, download_url, view_url, file_type など

## サンプル利用例（Python/Jupyter Notebook）

```python
import requests
import pandas as pd

# APIのベースURL
BASE_URL = "https://reder-test-o5k8.onrender.com"  # 本番環境
# BASE_URL = "http://localhost:8000"  # ローカル環境

# 国リスト取得
countries = requests.get(f"{BASE_URL}/get_countries").json()
df_countries = pd.DataFrame(countries)
display(df_countries)

# 例：2024年以降の中国（CHN）のイベントを取得
events_url = f"{BASE_URL}/get_events"
params = {
    "countryiso3s": "CHN",
    "start_date": "20240101"
}
events = requests.get(events_url, params=params).json()
df_events = pd.DataFrame(events)
display(df_events[["name", "disaster_type", "occurrence_date", "country", "requester", "glide_number", "url"]])

# 1件目のイベントのProduct（成果物）一覧を取得
if len(df_events) > 0:
    products = requests.get(f"{BASE_URL}/get_products", params={"url": df_events.iloc[0]["url"]}).json()
    df_products = pd.DataFrame(products)
    display(df_products)
    # 1番目のkmzファイルをダウンロード
    kmz_row = df_products[df_products["file_type"] == "kmz"].iloc[0]
    download_url = kmz_row["download_url"]
    r = requests.get(download_url)
    with open("downloaded_product.kmz", "wb") as f:
        f.write(r.content)
```

## 注意事項
- 本APIはSentinel Asia公式サイトのHTML構造に依存しているため、サイト構造の変更により動作しなくなる場合があります。
- 国名や災害タイプの自動抽出は完全ではない場合があります。
- 取得したプロダクトの利用には、上記のライセンスと利用条件が適用されます。

---

# Sentinel Asia EOR API (English)

A FastAPI-based API server for retrieving Sentinel Asia Emergency Observation Request (EOR) information.

## API Endpoints

The API is hosted at the following URLs:
- Production: https://reder-test-o5k8.onrender.com

For local development, use:
- Local: http://localhost:8000

## API Documentation

The API provides two interactive documentation interfaces:

### Swagger UI
- URL: `/docs`
- Interactive API documentation
- Test API endpoints directly
- Detailed request parameter descriptions
- Response schema definitions

### ReDoc
- URL: `/redoc`
- More readable API documentation format
- Detailed endpoint descriptions
- Request/response examples
- Visual schema representation

## Sample Notebooks

Two Jupyter Notebooks are provided to demonstrate the API usage:

### sample_render.ipynb
- Basic usage of the API hosted on Render
- Retrieving country list
- Getting and filtering event information
- Retrieving product information
- Data visualization examples

### get_kmz_files.ipynb
- Sample focused on KMZ file retrieval and saving
- Batch retrieval of KMZ files for specific countries or periods
- Automatic file download and saving
- Error handling examples

## Main Features

- Retrieve EOR (disaster event) information
- Filter by year, country (ISO3 code), and date range
- Automatic extraction of detailed EOR information (requester, escalation_to_charter, glide_number, country, etc.)
- Links to file lists for each EOR
- Available country list retrieval (covering Asia, Middle East, and Pacific countries)
- Service metadata retrieval

## Key Specifications

- **Country names are extracted from the "Country" field** in the EOR detail page, and ISO3 codes are mapped accordingly.
- Disaster event details (requester, escalation_to_charter, glide_number, etc.) are automatically extracted from the EOR detail page.
- Country codes cover all Asian, Middle Eastern, and Pacific countries.

## License and Terms of Use

The following conditions apply to the use of obtained products (files):

1. Obtained files cannot be modified.
2. When publishing obtained files, please include credits as referenced in each file.
3. All products are provided by Sentinel Asia and must be properly attributed.

## Installation

```bash
pip install -r requirements.txt
```

## Server Startup

```bash
conda activate sentinel_api
uvicorn main:app --reload
```

## API Endpoints

### 1. Country List Retrieval
- `GET /get_countries`
- Returns a list of available country names and ISO3 codes.
- **Covers Asian, Middle Eastern, and Pacific countries**

### 2. Metadata Retrieval
- `GET /get_metadata`
- Returns service description, license, methodology, and caveats.
- Response content:
  - description: Service description
  - licence: Terms of use and license information
  - methodology: Data collection method
  - caveats: Notes and limitations

### 3. Disaster Event Information Retrieval
- `GET /get_events`
- Query parameters:
  - `countryiso3s`: Comma-separated ISO3 country codes (e.g., JPN,PHL,CHN,IND,IDN,IRN,ISR,SAU,SGP,FJI)
  - `start_date`: Start date (YYYYMMDD or YYYY-MM-DD)
  - `end_date`: End date (YYYYMMDD or YYYY-MM-DD)
- Response content:
  - name, description, disaster_type, country, country_iso3, occurrence_date, sa_activation_date, requester, escalation_to_charter, glide_number, url, etc.
- **Country names, ISO3 codes, and requester information are automatically extracted from the EOR detail page**

### 4. Product Information Retrieval
- `GET /get_products?url=...`
- Returns a list of products (e.g., kmz files) from the specified EOR detail page URL.
- Response content:
  - date, title, download_url, view_url, file_type, etc.

## Usage Example (Python/Jupyter Notebook)

```python
import requests
import pandas as pd

# API base URL
BASE_URL = "https://reder-test-o5k8.onrender.com"  # Production
# BASE_URL = "http://localhost:8000"  # Local

# Get country list
countries = requests.get(f"{BASE_URL}/get_countries").json()
df_countries = pd.DataFrame(countries)
display(df_countries)

# Example: Get events in China (CHN) since 2024
events_url = f"{BASE_URL}/get_events"
params = {
    "countryiso3s": "CHN",
    "start_date": "20240101"
}
events = requests.get(events_url, params=params).json()
df_events = pd.DataFrame(events)
display(df_events[["name", "disaster_type", "occurrence_date", "country", "requester", "glide_number", "url"]])

# Get product list for the first event
if len(df_events) > 0:
    products = requests.get(f"{BASE_URL}/get_products", params={"url": df_events.iloc[0]["url"]}).json()
    df_products = pd.DataFrame(products)
    display(df_products)
    # Download the first kmz file
    kmz_row = df_products[df_products["file_type"] == "kmz"].iloc[0]
    download_url = kmz_row["download_url"]
    r = requests.get(download_url)
    with open("downloaded_product.kmz", "wb") as f:
        f.write(r.content)
```

## Notes
- This API depends on the HTML structure of the Sentinel Asia official website, so it may stop working if the site structure changes.
- Automatic extraction of country names and disaster types may not be perfect.
- The above license and terms of use apply to the use of obtained products.

---

ご質問・要望はIssueまたはPull Requestでお知らせください。
Questions and requests can be submitted via Issues or Pull Requests.