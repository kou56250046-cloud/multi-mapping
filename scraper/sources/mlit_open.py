"""
国土数値情報 N13（都市公園）スクレイパー

国土交通省が提供するGMLデータから東京・神奈川の都市公園情報を取得する。
ライセンス: CC BY 4.0（出典表示が必要）
データURL: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N13.html

GML構造の注意:
  N13のGMLはバージョンによって要素名・名前空間が異なる。
  このスクレイパーはロバストに対応するため、複数の要素名・座標形式を試行する。
"""

import sys
import os
import io
import zipfile
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET
from math import fsum

sys.path.insert(0, str(Path(__file__).parent.parent))
from classifier import classify_category, classify_tags
from config import OUTPUT_DIR

# 東京都・神奈川県の都市公園データ（複数のURLを試行）
DATASET_CANDIDATES = {
    "tokyo": [
        "https://nlftp.mlit.go.jp/ksj/gml/data/N13/N13-21/N13-21_13_GML.zip",
        "https://nlftp.mlit.go.jp/ksj/gml/data/N13/N13-18/N13-18_13_GML.zip",
    ],
    "kanagawa": [
        "https://nlftp.mlit.go.jp/ksj/gml/data/N13/N13-21/N13-21_14_GML.zip",
        "https://nlftp.mlit.go.jp/ksj/gml/data/N13/N13-18/N13-18_14_GML.zip",
    ],
}

# 試行するGML名前空間（バージョンによって異なる）
POSSIBLE_NS = [
    {"ksj": "http://nlftp.mlit.go.jp/ksj/schemas/ksj-app",
     "gml": "http://www.opengis.net/gml/3.2"},
    {"ksj": "http://nlftp.mlit.go.jp/ksj/schemas/ksj-app",
     "gml": "http://www.opengis.net/gml"},
]

# 公園要素として試行するタグ名
PARK_ELEMENT_CANDIDATES = [
    "UrbanPark",
    "ParkFacility",
    "Park",
    "N13",
]

# 公園名として試行するサブ要素名
NAME_ELEMENT_CANDIDATES = [
    "parkName",
    "name",
    "施設名称",
    "N13_002",
    "N13_003",
]

# 公園種別として試行するサブ要素名
TYPE_ELEMENT_CANDIDATES = [
    "parkClassification",
    "parkType",
    "N13_001",
]


def download_gml(prefecture: str) -> tuple[bytes, str] | tuple[None, None]:
    """ZIPをダウンロードしてGMLファイルのバイト列とファイル名を返す"""
    candidates = DATASET_CANDIDATES.get(prefecture, [])

    for url in candidates:
        print(f"  試行: {url}")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NatureSpotBot/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                zip_data = resp.read()
            print(f"  ダウンロード完了: {len(zip_data):,} bytes")

            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                # GML/XMLファイルを探す
                gml_names = [
                    n for n in zf.namelist()
                    if n.endswith(".xml") or n.endswith(".gml")
                ]
                if not gml_names:
                    print(f"  GMLファイルが見つかりません（ZIP内: {zf.namelist()[:5]}）")
                    continue
                print(f"  GMLファイル: {gml_names[0]}")
                with zf.open(gml_names[0]) as f:
                    return f.read(), gml_names[0]

        except urllib.error.HTTPError as e:
            print(f"  HTTPエラー {e.code}: {url}")
            continue
        except Exception as e:
            print(f"  ダウンロード失敗: {e}")
            continue

    print(f"  ⚠️ {prefecture} のGMLを取得できませんでした（全URLを試行済み）")
    return None, None


def _polygon_centroid(coords_text: str) -> tuple[float, float] | None:
    """
    GMLのposList（空白区切り緯度経度ペア）からポリゴン重心を計算する。
    GML3では lat lng lat lng... の順。
    """
    try:
        vals = list(map(float, coords_text.strip().split()))
        if len(vals) < 4:
            return None
        # lat, lng のペアを抽出
        lats = vals[0::2]
        lngs = vals[1::2]
        # 単純な算術平均（重心の近似）
        return fsum(lats) / len(lats), fsum(lngs) / len(lngs)
    except Exception:
        return None


def _find_text(elem: ET.Element, tag_candidates: list[str], ns: dict) -> str:
    """複数の候補タグ名で要素を検索してテキストを返す"""
    for tag in tag_candidates:
        for prefix, uri in ns.items():
            el = elem.find(f"{{{uri}}}{tag}")
            if el is not None and el.text:
                return el.text.strip()
        # 名前空間なしでも試行
        el = elem.find(f".//{tag}")
        if el is not None and el.text:
            return el.text.strip()
    return ""


def _find_coords(elem: ET.Element, gml_uri: str) -> tuple[float, float] | None:
    """GML要素から座標を取得する（pos / posList / coordinates を試行）"""
    # gml:pos（点）
    pos = elem.find(f".//{{{gml_uri}}}pos")
    if pos is not None and pos.text:
        parts = pos.text.strip().split()
        if len(parts) >= 2:
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                pass

    # gml:posList（ポリゴン → 重心）
    poslist = elem.find(f".//{{{gml_uri}}}posList")
    if poslist is not None and poslist.text:
        result = _polygon_centroid(poslist.text)
        if result:
            return result

    # gml:coordinates（旧形式 "lng,lat lng,lat"）
    coords_el = elem.find(f".//{{{gml_uri}}}coordinates")
    if coords_el is not None and coords_el.text:
        try:
            first_pair = coords_el.text.strip().split()[0]
            lng_s, lat_s = first_pair.split(",")
            return float(lat_s), float(lng_s)
        except Exception:
            pass

    return None


def parse_gml(gml_bytes: bytes, prefecture: str) -> list[dict]:
    """GMLをパースしてスポット辞書のリストを返す"""
    try:
        tree = ET.fromstring(gml_bytes)
    except ET.ParseError as e:
        print(f"  GMLパースエラー: {e}")
        return []

    # ルート要素の名前空間を検出
    root_tag = tree.tag
    print(f"  ルート要素: {root_tag}")

    spots = []

    # 試行する名前空間と公園要素の組み合わせを探索
    for ns in POSSIBLE_NS:
        ksj_uri = ns["ksj"]
        gml_uri = ns["gml"]

        for park_tag in PARK_ELEMENT_CANDIDATES:
            parks = tree.findall(f".//{{{ksj_uri}}}{park_tag}")
            if not parks:
                # 名前空間なしでも試行
                parks = tree.findall(f".//{park_tag}")

            if parks:
                print(f"  → 要素 '{park_tag}' で {len(parks)} 件を検出（名前空間: {ksj_uri[:40]}）")

                for park in parks:
                    try:
                        # 公園名を取得
                        name = _find_text(park, NAME_ELEMENT_CANDIDATES, ns)
                        if not name:
                            # どこかにテキストがあれば使う
                            all_texts = [el.text.strip() for el in park.iter() if el.text and el.text.strip()]
                            if all_texts:
                                name = all_texts[0]
                        if not name:
                            continue

                        # 座標を取得
                        coords = _find_coords(park, gml_uri)
                        if coords is None:
                            continue
                        lat, lng = coords

                        # 座標の妥当性チェック（日本の緯度経度範囲）
                        if not (24 <= lat <= 46 and 122 <= lng <= 146):
                            # 逆順かも
                            if 24 <= lng <= 46 and 122 <= lat <= 146:
                                lat, lng = lng, lat
                            else:
                                continue

                        # 公園種別
                        park_type = _find_text(park, TYPE_ELEMENT_CANDIDATES, ns)

                        category = classify_category(name, park_type)
                        tags = classify_tags(name, park_type)

                        spots.append({
                            "name": name,
                            "description": f"都市公園（{park_type}）" if park_type else "都市公園",
                            "category": category,
                            "latitude": round(lat, 7),
                            "longitude": round(lng, 7),
                            "source": "mlit",
                            "source_url": None,
                            "tags": tags,
                            "prefecture": prefecture,
                        })
                    except Exception as e:
                        print(f"  パースエラー（スキップ）: {e}")
                        continue

                if spots:
                    break  # 成功した組み合わせが見つかったら終了

        if spots:
            break

    if not spots:
        # デバッグ情報として実際の要素名を表示
        all_tags = {el.tag for el in tree.iter()}
        print(f"  ⚠️ 公園要素が見つかりませんでした")
        print(f"  GML内の要素名（先頭20個）: {list(all_tags)[:20]}")

    return spots


def scrape_mlit(prefectures: list[str] | None = None) -> list[dict]:
    """
    国土数値情報N13から都市公園データを取得する。
    """
    if prefectures is None:
        prefectures = list(DATASET_CANDIDATES.keys())

    all_spots: list[dict] = []
    for pref in prefectures:
        print(f"\n都市公園データ取得中: {pref}")
        gml_bytes, filename = download_gml(pref)
        if gml_bytes is None:
            continue
        spots = parse_gml(gml_bytes, pref)
        print(f"  → {len(spots)} 件取得")
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
