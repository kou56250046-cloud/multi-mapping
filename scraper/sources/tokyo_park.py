"""
東京都立公園スクレイパー

東京都公園協会 (tokyo-park.or.jp) から都立公園の情報を取得する。
また東京都オープンデータカタログも確認する。

⚠️ スクレイピング前に robots.txt を確認すること:
   curl https://www.tokyo-park.or.jp/robots.txt
"""

import sys
import os
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_scraper import BaseScraper
from geocoder import Geocoder
from classifier import classify_category, classify_tags
from config import OUTPUT_DIR

TOKYO_PARK_LIST_URL = "https://www.tokyo-park.or.jp/park/index.html"
SOURCE_ID = "tokyo_park"


class TokyoParkScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.geocoder = Geocoder()

    def scrape(self) -> list[dict]:
        """東京都公園協会サイトから都立公園の情報を収集する"""
        print("  東京都立公園リストを取得中...")

        try:
            soup = self.get_soup(TOKYO_PARK_LIST_URL)
        except Exception as e:
            print(f"  リスト取得失敗: {e}")
            return []

        # 公園リンクを抽出（実際のHTMLに合わせてセレクタを調整）
        park_links = soup.select("a[href*='/park/']")
        print(f"  {len(park_links)} 件の公園リンクを検出")

        spots = []
        for link in park_links[:50]:  # 初回は50件に制限
            href = link.get("href", "")
            if not href or href == "/park/index.html":
                continue

            url = href if href.startswith("http") else f"https://www.tokyo-park.or.jp{href}"
            try:
                spot = self._scrape_detail(url)
                if spot:
                    spots.append(spot)
            except Exception as e:
                print(f"    詳細取得エラー ({url}): {e}")

        return spots

    def _scrape_detail(self, url: str) -> dict | None:
        """公園詳細ページから情報を取得する"""
        soup = self.get_soup(url)

        # 公園名（実際のHTMLに合わせて調整）
        name_el = soup.find("h1") or soup.find("h2")
        if not name_el:
            return None
        name = name_el.text.strip()
        if not name:
            return None

        # 住所を探す（tableやdlタグ内にある場合が多い）
        address = None
        for el in soup.select("td, dd, span"):
            text = el.text.strip()
            if re.search(r"東京都|〒1[0-9]{2}", text):
                address = text
                break

        # 座標取得
        lat, lng = None, None
        if address:
            coords = self.geocoder.geocode(address)
            if coords:
                lat, lng = coords

        if lat is None or lng is None:
            print(f"    座標取得失敗（スキップ）: {name}")
            return None

        if not self.geocoder.is_in_area(lat, lng):
            return None

        # 説明文
        desc_el = soup.find("p", class_=re.compile(r"desc|intro|overview", re.I))
        description = desc_el.text.strip() if desc_el else None

        # 設備情報
        facilities: list[str] = [el.text.strip() for el in soup.select(".facility, .equipment, .amenity")]

        return {
            "name": name,
            "description": description,
            "category": classify_category(name, description or "", facilities),
            "latitude": lat,
            "longitude": lng,
            "source": SOURCE_ID,
            "source_url": url,
            "tags": classify_tags(name, description or "", facilities),
            "prefecture": "tokyo",
        }


if __name__ == "__main__":
    import pandas as pd

    scraper = TokyoParkScraper()
    spots = scraper.scrape()

    if spots:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        df = pd.DataFrame(spots)
        output_path = os.path.join(OUTPUT_DIR, "tokyo_park_spots.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n✅ {len(spots)} 件を保存: {output_path}")
    else:
        print("データが取得できませんでした")
