"""
hidden_gem スポットを取得してdata/spots.csvに追記するスクリプト
エリアを2分割して取得することでAPI負荷を軽減
"""
import sys, os, time
import requests
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from sources.overpass import _osm_tags_to_category, _osm_tags_to_spot_tags, _get_coords, _is_in_target_area, _get_prefecture, SOURCE_ID

FINAL_CSV = ROOT_DIR / "data" / "spots.csv"
URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "multi-mapping-scraper/1.0 (educational)"}

CSV_COLUMNS = [
    "id", "name", "description", "category",
    "latitude", "longitude", "source", "source_url", "tags", "prefecture",
]

# エリアを2分割して負荷を軽減
BBOXES = [
    "35.55,138.8,36.1,140.0",  # 北部（東京北部・埼玉境界付近）
    "35.0,138.8,35.55,140.0",  # 南部（横浜・鎌倉・三浦半島）
]

def run_simple_query(bbox: str, qtype: str) -> list[dict]:
    """単一タイプのクエリを実行"""
    queries = {
        "attraction": f'[out:json][timeout:30]; node["tourism"="attraction"]["name"~"."]({bbox}); out 200;',
        "artwork":    f'[out:json][timeout:30]; node["tourism"="artwork"]["name"~"."]({bbox}); out 100;',
        "ruins":      f'[out:json][timeout:30]; node["historic"="ruins"]["name"~"."]({bbox}); out 100;',
    }
    query = queries[qtype]
    try:
        r = requests.post(URL, data={"data": query}, headers=HEADERS, timeout=45)
        if r.status_code != 200:
            print(f"  [{qtype}@{bbox[:10]}] HTTP {r.status_code}")
            return []
        elements = r.json().get("elements", [])
        print(f"  [{qtype}@{bbox[:10]}] {len(elements)} 要素")
        return elements
    except Exception as e:
        print(f"  [{qtype}@{bbox[:10]}] エラー: {e}")
        return []

def elements_to_spots(elements: list) -> list[dict]:
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
        description = tags.get("description") or tags.get("note") or None
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

def main():
    print("=== hidden_gem スポットを追加 ===")
    all_spots = []

    for bbox in BBOXES:
        for qtype in ["attraction", "artwork", "ruins"]:
            elements = run_simple_query(bbox, qtype)
            spots = elements_to_spots(elements)
            all_spots.extend(spots)
            time.sleep(2)

    print(f"\n取得合計: {len(all_spots)} 件")
    if not all_spots:
        print("⚠️ 0件。APIのレート制限の可能性があります。")
        return

    # 重複除去
    seen = set()
    unique = []
    for s in all_spots:
        key = f"{s['name']}_{s['latitude']:.3f}_{s['longitude']:.3f}"
        if key not in seen:
            seen.add(key)
            unique.append(s)
    print(f"重複除去後: {len(unique)} 件")

    # 既存CSVとの重複チェック
    existing = pd.read_csv(FINAL_CSV, dtype=str).fillna("")
    existing_keys = set(
        f"{row['name']}_{float(row['latitude']):.3f}_{float(row['longitude']):.3f}"
        for _, row in existing.iterrows()
        if row['latitude'] and row['longitude']
    )
    start_id = len(existing) + 1

    new_rows = []
    for i, spot in enumerate(unique):
        key = f"{spot['name']}_{spot['latitude']:.3f}_{spot['longitude']:.3f}"
        if key in existing_keys:
            continue
        tags = spot.get("tags", [])
        new_rows.append({
            "id": f"overpass-{str(start_id + i).zfill(5)}",
            "name": spot["name"],
            "description": spot.get("description") or "",
            "category": spot["category"],
            "latitude": spot["latitude"],
            "longitude": spot["longitude"],
            "source": spot["source"],
            "source_url": spot.get("source_url") or "",
            "tags": ";".join(tags) if isinstance(tags, list) else tags,
            "prefecture": spot.get("prefecture", "tokyo"),
        })

    if not new_rows:
        print("✅ すべて既存データに含まれていました（重複なし）")
        return

    print(f"新規追加: {len(new_rows)} 件")
    df_new = pd.DataFrame(new_rows, columns=CSV_COLUMNS)
    df_new.to_csv(FINAL_CSV, mode='a', index=False, encoding="utf-8-sig", header=False)
    print(f"💾 {FINAL_CSV} に追記完了")

    from collections import Counter
    cats = Counter(r["category"] for r in new_rows)
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}")

if __name__ == "__main__":
    main()
