# Sentinel Asia EOR API

Sentinel Asiaの緊急観測要請（EOR: Emergency Observation Request）情報を取得するFastAPIベースのAPIサーバーです。

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

# 国リスト取得
countries = requests.get("http://localhost:8000/get_countries").json()
df_countries = pd.DataFrame(countries)
display(df_countries)

# 例：2024年以降の中国（CHN）のイベントを取得
events_url = "http://localhost:8000/get_events"
params = {
    "countryiso3s": "CHN",
    "start_date": "20240101"
}
events = requests.get(events_url, params=params).json()
df_events = pd.DataFrame(events)
display(df_events[["name", "disaster_type", "occurrence_date", "country", "requester", "glide_number", "url"]])

# 1件目のイベントのProduct（成果物）一覧を取得
if len(df_events) > 0:
    products = requests.get("http://localhost:8000/get_products", params={"url": df_events.iloc[0]["url"]}).json()
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

ご質問・要望はIssueまたはPull Requestでお知らせください。