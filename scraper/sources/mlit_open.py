"""
国土数値情報 N13（都市公園）スクレイパー

国土交通省が提供するGMLデータから東京・神奈川の都市公園情報を取得する。
ライセンス: CC BY 4.0（出典表示が必要）
データURL: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N13.html
"""

import sys
import os
import io
import zipfile
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent.parent))
from classifier import classify_category, classify_tags
from config import OUTPUT_DIR

# 東京都・神奈川県の都市公園データ
DATASETS = {
    "tokyo": "https://nlftp.mlit.go.jp/ksj/gml/data/N13/N13-21/N13-21_13_GML.zip",
    "kanagawa": "https://nlftp.mlit.go.jp/ksj/gml/data/N13/N13-21/N13-21_14_GML.zip",
}

# GML名前空間
NS = {
    "ksj": "http://nlftp.mlit.go.jp/ksj/schemas/ksj-app",
    "gml": "http://www.opengis.net/gml/3.2",
    "xlink": "http://www.w3.org/1999/xlink",
}


def download_gml(prefecture: str) -> bytes | None:
    """ZIPをダウンロードしてGMLファイルのバイト列を返す"""
    url = DATASETS.get(prefecture)
    if not url:
        print(f"未対応の都道府県: {prefecture}")
        return None

    print(f"  ダウンロード中: {url}")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            zip_data = resp.read()
    except Exception as e:
        print(f"  ダウンロード失敗: {e}")
        return None

    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        # GMLファイルを探す
        gml_names = [n for n in zf.namelist() if n.endswith(".xml") or n.endswith(".gml")]
        if not gml_names:
            print("  GMLファイルが見つかりません")
            return None
        # 最初のGMLファイルを使用
        with zf.open(gml_names[0]) as f:
            return f.read()


def parse_gml(gml_bytes: bytes, prefecture: str) -> list[dict]:
    """GMLをパースしてスポット辞書のリストを返す"""
    tree = ET.fromstring(gml_bytes)
    spots = []

    # N13のGML構造: <ksj:UrbanPark> 要素を探す
    parks = tree.findall(".//ksj:UrbanPark", NS)
    print(f"  {len(parks)} 件の公園を検出")

    for park in parks:
        try:
            name_el = park.find(".//ksj:parkName", NS)
            name = name_el.text.strip() if name_el is not None and name_el.text else None
            if not name:
                continue

            # 座標（ポリゴンの重心または代表点）を取得
            pos_el = park.find(".//gml:pos", NS)
            coords_el = park.find(".//gml:posList", NS)

            lat, lng = None, None
            if pos_el is not None and pos_el.text:
                parts = pos_el.text.strip().split()
                if len(parts) >= 2:
                    lat, lng = float(parts[0]), float(parts[1])
            elif coords_el is not None and coords_el.text:
                # ポリゴンの最初の座標を使用（後で重心計算に変えても良い）
                parts = coords_el.text.strip().split()
                if len(parts) >= 2:
                    lat, lng = float(parts[0]), float(parts[1])

            if lat is None or lng is None:
                continue

            # 公園種別を取得
            type_el = park.find(".//ksj:parkClassification", NS)
            park_type = type_el.text.strip() if type_el is not None and type_el.text else ""

            category = classify_category(name, park_type)
            tags = classify_tags(name, park_type)

            spots.append({
                "name": name,
                "description": f"都市公園（{park_type}）" if park_type else "都市公園",
                "category": category,
                "latitude": lat,
                "longitude": lng,
                "source": "mlit",
                "source_url": None,
                "tags": tags,
                "prefecture": prefecture,
            })
        except Exception as e:
            print(f"  パースエラー（スキップ）: {e}")
            continue

    return spots


def scrape_mlit(prefectures: list[str] | None = None) -> list[dict]:
    """
    国土数値情報N13から都市公園データを取得する。

    Args:
        prefectures: 対象都道府県リスト。Noneの場合は全対象（東京・神奈川）

    Returns:
        スポット辞書のリスト
    """
    if prefectures is None:
        prefectures = list(DATASETS.keys())

    all_spots: list[dict] = []
    for pref in prefectures:
        print(f"\n都市公園データ取得中: {pref}")
        gml_bytes = download_gml(pref)
        if gml_bytes is None:
            continue
        spots = parse_gml(gml_bytes, pref)
        print(f"  取得: {len(spots)} 件")
        all_spots.extend(spots)

    return all_spots


if __name__ == "__main__":
    import pandas as pd

    spots = scrape_mlit()
    if spots:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        df = pd.DataFrame(spots)
        output_path = os.path.join(OUTPUT_DIR, "mlit_spots.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n✅ {len(spots)} 件を保存: {output_path}")
    else:
        print("データが取得できませんでした")
