"""
神奈川県立公園スクレイパー

神奈川県立公園協会 (kanagawa-park.or.jp) から公園情報を取得する。

⚠️ スクレイピング前に robots.txt を確認すること:
   curl https://www.kanagawa-park.or.jp/robots.txt
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

KANAGAWA_PARK_LIST_URL = "https://www.kanagawa-park.or.jp/parks/"
SOURCE_ID = "kanagawa_park"


class KanagawaParkScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.geocoder = Geocoder()

    def scrape(self) -> list[dict]:
        """神奈川県立公園の情報を収集する"""
        print("  神奈川県立公園リストを取得中...")

        try:
            soup = self.get_soup(KANAGAWA_PARK_LIST_URL)
        except Exception as e:
            print(f"  リスト取得失敗: {e}")
            return []

        # 公園リンクを抽出（実際のHTMLに合わせてセレクタを調整）
        park_links = soup.select("a[href*='park']")
        print(f"  {len(park_links)} 件の公園リンクを検出")

        spots = []
        seen_urls: set[str] = set()

        for link in park_links:
            href = link.get("href", "")
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)

            url = href if href.startswith("http") else f"https://www.kanagawa-park.or.jp{href}"
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

        # 公園名
        name_el = soup.find("h1") or soup.find("h2")
        if not name_el:
            return None
        name = name_el.text.strip()
        if not name:
            return None

        # 住所
        address = None
        for el in soup.select("td, dd, p"):
            text = el.text.strip()
            if re.search(r"神奈川県|〒2[0-9]{2}", text):
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
        desc_el = soup.find("p", class_=re.compile(r"desc|intro|about", re.I))
        description = desc_el.text.strip() if desc_el else None

        # 設備情報
        facilities: list[str] = [el.text.strip() for el in soup.select(".facility, .equipment")]

        return {
            "name": name,
            "description": description,
            "category": classify_category(name, description or "", facilities),
            "latitude": lat,
            "longitude": lng,
            "source": SOURCE_ID,
            "source_url": url,
            "tags": classify_tags(name, description or "", facilities),
            "prefecture": "kanagawa",
        }


if __name__ == "__main__":
    import pandas as pd

    scraper = KanagawaParkScraper()
    spots = scraper.scrape()

    if spots:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        df = pd.DataFrame(spots)
        output_path = os.path.join(OUTPUT_DIR, "kanagawa_park_spots.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n✅ {len(spots)} 保存: {output_path}")
    else:
        print("データが取得できませんでした")
