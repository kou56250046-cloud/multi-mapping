"""
全スクレイパーを実行し、統合CSVを生成するエントリポイント

使い方:
  cd scraper
  pip install -r requirements.txt
  python run_all.py

出力:
  scraper/output/spots.csv  → プロジェクトルートの data/spots.csv にコピーされる
  (その後 npm run generate でJSONに変換する)
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from dedup import deduplicate
from config import OUTPUT_DIR

OUTPUT_CSV = os.path.join(OUTPUT_DIR, "spots.csv")
FINAL_CSV = str(ROOT_DIR / "data" / "spots.csv")

# CSV カラム定義
CSV_COLUMNS = [
    "id", "name", "description", "category",
    "latitude", "longitude", "source", "source_url", "tags", "prefecture",
]

# データソース優先度（重複排除時に先頭のソースが優先される）
SOURCE_PRIORITY = ["mlit", "tokyo_park", "kanagawa_park", "nap", "manual"]


def run_scraper(name: str, scraper_fn) -> list[dict]:
    """スクレイパーを実行してスポットリストを返す"""
    print(f"\n{'='*50}")
    print(f"📡 {name} を実行中...")
    print(f"{'='*50}")
    try:
        spots = scraper_fn()
        print(f"✅ {name}: {len(spots)} 件取得")
        return spots
    except Exception as e:
        print(f"❌ {name}: エラー発生 - {e}")
        return []


def spots_to_csv_rows(spots: list[dict]) -> list[dict]:
    """スポット辞書をCSV行フォーマットに変換する"""
    rows = []
    for i, spot in enumerate(spots):
        source = spot.get("source", "manual")
        tags = spot.get("tags", [])
        rows.append({
            "id": spot.get("id") or f"{source}-{str(i+1).zfill(4)}",
            "name": spot.get("name", ""),
            "description": spot.get("description") or "",
            "category": spot.get("category", "walking"),
            "latitude": spot.get("latitude", 0),
            "longitude": spot.get("longitude", 0),
            "source": source,
            "source_url": spot.get("source_url") or "",
            "tags": ";".join(tags) if isinstance(tags, list) else tags,
            "prefecture": spot.get("prefecture", "tokyo"),
        })
    return rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(str(ROOT_DIR / "data"), exist_ok=True)

    all_spots: list[dict] = []

    # 1. 国土数値情報 N13（最優先・法的リスクなし）
    try:
        from sources.mlit_open import scrape_mlit
        spots = run_scraper("国土数値情報 N13（都市公園）", scrape_mlit)
        all_spots.extend(spots)
    except ImportError as e:
        print(f"⚠️  mlit_open のインポートエラー: {e}")

    # 2. 東京都公園協会
    try:
        from sources.tokyo_park import TokyoParkScraper
        spots = run_scraper("東京都立公園", TokyoParkScraper().scrape)
        all_spots.extend(spots)
    except ImportError as e:
        print(f"⚠️  tokyo_park のインポートエラー: {e}")

    # 3. 神奈川県立公園
    try:
        from sources.kanagawa_park import KanagawaParkScraper
        spots = run_scraper("神奈川県立公園", KanagawaParkScraper().scrape)
        all_spots.extend(spots)
    except ImportError as e:
        print(f"⚠️  kanagawa_park のインポートエラー: {e}")

    # 4. なっぷ（robots.txt確認済みの場合のみ）
    NAP_ENABLED = os.environ.get("NAP_SCRAPING_ENABLED", "false").lower() == "true"
    if NAP_ENABLED:
        try:
            from sources.nap import NapScraper
            spots = run_scraper("なっぷ (nap.jp)", NapScraper().scrape)
            all_spots.extend(spots)
        except ImportError as e:
            print(f"⚠️  nap のインポートエラー: {e}")
    else:
        print("\nℹ️  なっぷのスクレイピングは無効です")
        print("   有効にするには: NAP_SCRAPING_ENABLED=true python run_all.py")

    if not all_spots:
        print("\n⚠️  データが取得できませんでした")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"📊 合計 {len(all_spots)} 件取得")

    # 優先度順にソート（重複排除で先頭が優先されるため）
    def sort_key(s: dict) -> int:
        src = s.get("source", "manual")
        return SOURCE_PRIORITY.index(src) if src in SOURCE_PRIORITY else len(SOURCE_PRIORITY)
    all_spots.sort(key=sort_key)

    # 重複排除
    deduped = deduplicate(all_spots, distance_threshold_km=0.1)
    print(f"🔄 重複排除後: {len(deduped)} 件（{len(all_spots) - len(deduped)} 件除去）")

    # IDを振り直す
    for i, spot in enumerate(deduped):
        if not spot.get("id"):
            spot["id"] = f"{spot.get('source', 'manual')}-{str(i+1).zfill(4)}"

    # CSV出力
    rows = spots_to_csv_rows(deduped)
    df = pd.DataFrame(rows, columns=CSV_COLUMNS)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"💾 中間CSV: {OUTPUT_CSV}")

    df.to_csv(FINAL_CSV, index=False, encoding="utf-8-sig")
    print(f"💾 最終CSV: {FINAL_CSV}")

    print(f"\n{'='*50}")
    print(f"✅ 完了! 次のステップ:")
    print(f"   cd ..")
    print(f"   npm run generate")
    print(f"   npm run build")
    print(f"{'='*50}")

    # カテゴリ別集計
    print("\n📈 カテゴリ別集計:")
    for cat, count in df["category"].value_counts().items():
        print(f"   {cat}: {count} 件")


if __name__ == "__main__":
    main()
