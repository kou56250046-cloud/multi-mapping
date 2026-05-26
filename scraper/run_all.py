"""
全スクレイパーを実行し、統合CSVを生成するエントリポイント

使い方:
  cd scraper
  pip install -r requirements.txt
  python run_all.py                              # 全ソースを実行
  python run_all.py --sources mlit,tokyo_park   # 指定ソースのみ実行
  NAP_SCRAPING_ENABLED=true python run_all.py   # なっぷも含めて全実行

出力:
  scraper/output/spots.csv  → プロジェクトルートの data/spots.csv にコピーされる
  (その後 npm run generate でJSONに変換する)
"""

import argparse
import os
import sys
import pandas as pd
from pathlib import Path

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


def main(enabled_sources: set[str] | None = None):
    """
    Args:
        enabled_sources: 実行するソースのセット。None の場合は全ソースを実行。
                         例: {"mlit", "tokyo_park"}
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(str(ROOT_DIR / "data"), exist_ok=True)

    def should_run(source_key: str) -> bool:
        return enabled_sources is None or source_key in enabled_sources

    all_spots: list[dict] = []

    # 1. 国土数値情報 N13（最優先・法的リスクなし）
    if should_run("mlit"):
        try:
            from sources.mlit_open import scrape_mlit
            spots = run_scraper("国土数値情報 N13（都市公園）", scrape_mlit)
            all_spots.extend(spots)
        except ImportError as e:
            print(f"⚠️  mlit_open のインポートエラー: {e}")
    else:
        print("⏭️  国土数値情報 N13: スキップ")

    # 2. 東京都公園協会
    if should_run("tokyo_park"):
        try:
            from sources.tokyo_park import TokyoParkScraper
            spots = run_scraper("東京都立公園", TokyoParkScraper().scrape)
            all_spots.extend(spots)
        except ImportError as e:
            print(f"⚠️  tokyo_park のインポートエラー: {e}")
    else:
        print("⏭️  東京都立公園: スキップ")

    # 3. 神奈川県立公園
    if should_run("kanagawa_park"):
        try:
            from sources.kanagawa_park import KanagawaParkScraper
            spots = run_scraper("神奈川県立公園", KanagawaParkScraper().scrape)
            all_spots.extend(spots)
        except ImportError as e:
            print(f"⚠️  kanagawa_park のインポートエラー: {e}")
    else:
        print("⏭️  神奈川県立公園: スキップ")

    # 4. なっぷ（robots.txt確認済み かつ 選択された場合のみ）
    NAP_ENABLED = os.environ.get("NAP_SCRAPING_ENABLED", "false").lower() == "true"
    if should_run("nap") and NAP_ENABLED:
        try:
            from sources.nap import NapScraper
            spots = run_scraper("なっぷ (nap.jp)", NapScraper().scrape)
            all_spots.extend(spots)
        except ImportError as e:
            print(f"⚠️  nap のインポートエラー: {e}")
    elif should_run("nap") and not NAP_ENABLED:
        print("\nℹ️  なっぷのスクレイピングは無効です（NAP_SCRAPING_ENABLED=true が必要）")
    else:
        print("⏭️  なっぷ: スキップ")

    if not all_spots:
        print("\n⚠️  データが取得できませんでした")
        print("   各スクレイパーのエラーログを確認し、ネットワーク接続・サイト構造を確認してください")
        print("   Streamlit UI の「既存データをインポート」を使うと手動データでパイプラインを確認できます")
        # sys.exit(1) は呼ばず、空のCSVを書いて終了する
        df_empty = pd.DataFrame(columns=CSV_COLUMNS)
        df_empty.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        df_empty.to_csv(FINAL_CSV, index=False, encoding="utf-8-sig")
        print(f"💾 空のCSVを作成: {OUTPUT_CSV}")
        return

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
    parser = argparse.ArgumentParser(description="スポットスクレイパー実行ツール")
    parser.add_argument(
        "--sources",
        default=None,
        help="実行するソース（カンマ区切り）例: mlit,tokyo_park,kanagawa_park,nap",
    )
    args = parser.parse_args()

    enabled: set[str] | None = None
    if args.sources:
        enabled = {s.strip() for s in args.sources.split(",") if s.strip()}
        print(f"📋 実行対象ソース: {', '.join(sorted(enabled))}")

    main(enabled_sources=enabled)
