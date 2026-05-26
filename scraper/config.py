"""
共通設定
"""

# リクエスト間隔（秒）の最小・最大
REQUEST_DELAY_MIN = 2.0
REQUEST_DELAY_MAX = 5.0

# HTTP リクエストのデフォルトヘッダー
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NatureSpotBot/1.0; "
        "+https://github.com/kou56250046-cloud/multi-mapping)"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 対象エリアの緯度・経度範囲（東京・神奈川）
AREA = {
    "lat_min": 35.0,
    "lat_max": 36.1,
    "lng_min": 138.8,
    "lng_max": 140.0,
}

# 国土地理院ジオコーディングAPI
GSI_GEOCODE_URL = "https://msearch.gsi.go.jp/address-search/AddressSearch"

# CSVの出力先ディレクトリ
OUTPUT_DIR = "output"
