"""
OpenStreetMap Overpass API スクレイパー

OpenStreetMapのOverpass APIから東京・神奈川の自然スポットを取得する。

利用条件:
  - 無料・認証不要
  - ODbL ライセンス（© OpenStreetMap contributors）
  - レート制限: 過度なリクエストを避けること（リクエスト間隔を設ける）

APIドキュメント: https://overpass-api.de/
"""

import sys
import os
import time
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from classifier import classify_tags
from config import OUTPUT_DIR

# 東京・神奈川エリアの境界ボックス (south, west, north, east)
BBOX = "35.0,138.8,36.1,140.0"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

SOURCE_ID = "overpass"

# OSMタグ → カテゴリのマッピング
CATEGORY_MAP = [
    # (カテゴリ, [(key, value), ...]) — 先にマッチしたものが優先
    ("waterfall",  [("natural", "waterfall"), ("waterway", "waterfall")]),
    ("bbq",        [("amenity", "bbq"), ("leisure", "firepit"),
                    ("barbecue_grill", "yes")]),
    ("waterside",  [("natural", "water"), ("waterway", "river"),
                    ("waterway", "stream"), ("natural", "coastline"),
                    ("natural", "beach"), ("leisure", "swimming_area"),
                    ("waterway", "riverbank")]),
    ("sports",     [("leisure", "sports_centre"), ("leisure", "pitch"),
                    ("leisure", "stadium"), ("leisure", "track")]),
    ("hidden_gem", [("tourism", "attraction"), ("tourism", "artwork"),
                    ("historic", "ruins"), ("historic", "archaeological_site")]),
    ("walking",    [("leisure", "park"), ("leisure", "garden"),
                    ("leisure", "nature_reserve"), ("boundary", "national_park"),
                    ("natural", "peak"), ("natural", "wood")]),
    ("meditation", [("tourism", "viewpoint"), ("historic", "monument"),
                    ("amenity", "place_of_worship")]),
]

# OSMタグ → SpotTagのマッピング
TAG_OSM_MAP = [
    ("toilet",    [("amenity", "toilets"), ("toilets", "yes")]),
    ("parking",   [("amenity", "parking"), ("parking", "yes")]),
    ("water",     [("amenity", "drinking_water"), ("drinking_water", "yes")]),
    ("bench",     [("amenity", "bench"), ("bench", "yes")]),
    ("bbq_ok",    [("amenity", "bbq"), ("barbecue_grill", "yes")]),
    ("pet_ok",    [("dog", "yes"), ("pets", "yes")]),
    ("wheelchair",[("wheelchair", "yes"), ("wheelchair", "designated")]),
    ("fee",       [("fee", "yes")]),
]

# Overpassクエリ（カテゴリ別）
QUERIES = {
    "parks_and_nature": """
[out:json][timeout:60];
(
  node["leisure"="park"]["name"~"."]{bbox};
  way["leisure"="park"]["name"~"."]{bbox};
  node["leisure"="nature_reserve"]["name"~"."]{bbox};
  way["leisure"="nature_reserve"]["name"~"."]{bbox};
  node["boundary"="national_park"]["name"~"."]{bbox};
  way["boundary"="protected_area"]["name"~"."]{bbox};
);
out center;
""",
    "waterfalls": """
[out:json][timeout:30];
(
  node["natural"="waterfall"]{bbox};
  way["natural"="waterfall"]["name"~"."]{bbox};
  node["waterway"="waterfall"]["name"~"."]{bbox};
  way["waterway"="waterfall"]["name"~"."]{bbox};
  node["name"~"滝",i]{bbox};
);
out center;
""",
    "waterside": """
[out:json][timeout:90];
(
  node["natural"="beach"]["name"~"."]{bbox};
  way["natural"="beach"]["name"~"."]{bbox};
  node["leisure"="swimming_area"]["name"~"."]{bbox};
  way["waterway"="river"]["name"~"."]{bbox};
  relation["waterway"="river"]["name"~"."]{bbox};
  node["natural"="spring"]["name"~"."]{bbox};
  way["natural"="water"]["name"~"."]{bbox};
  node["natural"="water"]["name"~"."]{bbox};
  way["waterway"="stream"]["name"~"."]{bbox};
);
out center;
""",
    "bbq": """
[out:json][timeout:60];
(
  node["amenity"="bbq"]{bbox};
  node["leisure"="firepit"]["name"~"."]{bbox};
  way["barbecue_grill"="yes"]["name"~"."]{bbox};
  node["barbecue_grill"="yes"]["name"~"."]{bbox};
  node["name"~"バーベキュー|BBQ|バーベキュ",i]{bbox};
  way["name"~"バーベキュー|BBQ|バーベキュ",i]{bbox};
);
out center;
""",
    "sports": """
[out:json][timeout:30];
(
  node["leisure"="sports_centre"]["name"~"."]{bbox};
  way["leisure"="sports_centre"]["name"~"."]{bbox};
);
out center;
""",
    "viewpoints": """
[out:json][timeout:30];
(
  node["tourism"="viewpoint"]["name"~"."]{bbox};
  node["natural"="peak"]["name"~"."]{bbox};
);
out center;
""",
    "hidden_gem": """
[out:json][timeout:60];
(
  node["tourism"="attraction"]["name"~"."]{bbox};
  way["tourism"="attraction"]["name"~"."]{bbox};
  node["tourism"="artwork"]["name"~"."]{bbox};
  way["tourism"="artwork"]["name"~"."]{bbox};
  node["historic"="ruins"]["name"~"."]{bbox};
  node["historic"="archaeological_site"]["name"~"."]{bbox};
  way["historic"="ruins"]["name"~"."]{bbox};
);
out center;
""",
}


def _osm_tags_to_category(tags: dict) -> str:
    """OSMタグからカテゴリを判定する"""
    for category, conditions in CATEGORY_MAP:
        for key, val in conditions:
            if tags.get(key) == val:
                return category
    # 名前・説明からも判定
    name = (tags.get("name", "") + " " + tags.get("name:ja", "") +
            " " + tags.get("description", "")).lower()
    if any(w in name for w in ["滝", "falls", "waterfall"]):
        return "waterfall"
    if any(w in name for w in ["バーベキュー", "bbq", "バーベキュ"]):
        return "bbq"
    if any(w in name for w in ["川", "河川", "river", "海", "池", "湖", "湿地"]):
        return "waterside"
    from classifier import classify_category
    return classify_category(name)


def _osm_tags_to_spot_tags(element_tags: dict, nearby_features: dict = {}) -> list[str]:
    """OSMタグからSpotTagリストを生成する"""
    spot_tags = []
    # 要素自身のタグを確認
    for tag, conditions in TAG_OSM_MAP:
        for key, val in conditions:
            if element_tags.get(key) == val:
                spot_tags.append(tag)
                break
    # 名前・説明からも補完
    name = element_tags.get("name", "") + " " + element_tags.get("description", "")
    from classifier import classify_tags as ct
    inferred = ct(name)
    for t in inferred:
        if t not in spot_tags:
            spot_tags.append(t)
    return list(set(spot_tags))


def _get_coords(element: dict) -> tuple[float, float] | None:
    """Overpass要素から座標を取得する"""
    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")
    elif element.get("type") == "way" and "center" in element:
        c = element["center"]
        return c.get("lat"), c.get("lon")
    elif element.get("type") == "relation" and "center" in element:
        c = element["center"]
        return c.get("lat"), c.get("lon")
    return None, None


def _is_in_target_area(lat: float, lon: float) -> bool:
    """東京・神奈川エリア内かチェック"""
    from config import AREA
    return (AREA["lat_min"] <= lat <= AREA["lat_max"] and
            AREA["lng_min"] <= lon <= AREA["lng_max"])


def _get_prefecture(lat: float, lon: float) -> str:
    """座標から都道府県を推定（簡易判定）"""
    # 神奈川: おおむね南部
    if lat < 35.55 and lon < 139.8:
        return "kanagawa"
    return "tokyo"


def run_query(query_name: str, query_template: str) -> list[dict]:
    """Overpass APIにクエリを実行してスポットリストを返す"""
    query = query_template.replace("{bbox}", f"({BBOX})")
    print(f"  [{query_name}] クエリ実行中...")

    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": "multi-mapping-scraper/1.0 (educational; github.com/kou56250046-cloud/multi-mapping)"},
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        print(f"  [{query_name}] タイムアウト")
        return []
    except Exception as e:
        print(f"  [{query_name}] エラー: {e}")
        return []

    elements = data.get("elements", [])
    print(f"  [{query_name}] {len(elements)} 要素を取得")

    spots = []
    for elem in elements:
        tags = elem.get("tags", {})
        name = tags.get("name") or tags.get("name:ja")
        if not name:
            continue

        lat, lon = _get_coords(elem)
        if lat is None or lon is None:
            continue
        if not _is_in_target_area(lat, lon):
            continue

        # 説明文
        description = (
            tags.get("description")
            or tags.get("note")
            or tags.get("wikipedia")
            or None
        )

        # OSM URL
        osm_type = elem.get("type", "node")
        osm_id = elem.get("id", "")
        source_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"

        category = _osm_tags_to_category(tags)
        spot_tags = _osm_tags_to_spot_tags(tags)

        spots.append({
            "name": name.strip(),
            "description": description,
            "category": category,
            "latitude": round(float(lat), 7),
            "longitude": round(float(lon), 7),
            "source": SOURCE_ID,
            "source_url": source_url,
            "tags": spot_tags,
            "prefecture": _get_prefecture(float(lat), float(lon)),
        })

    return spots


def scrape_overpass() -> list[dict]:
    """
    OpenStreetMap Overpass APIから東京・神奈川のスポットを取得する
    """
    all_spots: list[dict] = []
    seen_ids: set = set()

    for query_name, query_template in QUERIES.items():
        spots = run_query(query_name, query_template)
        new_count = 0
        for spot in spots:
            # 名前+座標の近似で重複除去
            key = f"{spot['name']}_{spot['latitude']:.3f}_{spot['longitude']:.3f}"
            if key not in seen_ids:
                seen_ids.add(key)
                all_spots.append(spot)
                new_count += 1
        print(f"  → 新規追加: {new_count} 件（累計: {len(all_spots)} 件）")
        # APIへの負荷を減らすため待機
        time.sleep(2)

    return all_spots


if __name__ == "__main__":
    import pandas as pd

    print("Overpass API スクレイパーを実行中...")
    spots = scrape_overpass()

    if spots:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        df = pd.DataFrame(spots)
        output_path = os.path.join(OUTPUT_DIR, "overpass_spots.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n完了: {len(spots)} 件を保存 -> {output_path}")
        print("\nカテゴリ別:")
        for cat, cnt in df["category"].value_counts().items():
            print(f"  {cat}: {cnt}")
    else:
        print("データが取得できませんでした")
