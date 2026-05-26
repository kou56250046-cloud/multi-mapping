"""
なっぷ (nap.jp) スクレイパー

BBQ場・アウトドア施設の情報を取得する。

⚠️ 重要: 実行前に必ず robots.txt を確認すること
   curl https://nap.jp/robots.txt
   Disallow ルールを厳守し、Crawl-delay を遵守する。

対象: 東京都(pref=13)・神奈川県(pref=14)のBBQ・アウトドア施設
"""

import sys
import os
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_scraper import BaseScraper
from classifier import classify_category, classify_tags
from geocoder import Geocoder
from config import OUTPUT_DIR

# なっぷの都道府県コード
PREF_MAP = {
    "tokyo": "13",
    "kanagawa": "14",
}

SOURCE_ID = "nap"
BASE_URL = "https://nap.jp"


def check_robots_txt() -> bool:
    """
    robots.txt を確認してスクレイピングが許可されているかチェックする。
    実際の実装では robotparser を使用する。
    """
    import urllib.robotparser
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{BASE_URL}/robots.txt")
    try:
        rp.read()
        # 検索一覧ページへのアクセス確認
        allowed = rp.can_fetch("*", f"{BASE_URL}/search/")
        if not allowed:
            print("⛔ robots.txt によりスクレイピングが禁止されています")
        return allowed
    except Exception as e:
        print(f"robots.txt の確認に失敗しました: {e}")
        return False


class NapScraper(BaseScraper):
    def __init__(self):
        super().__init__(delay_min=3.0, delay_max=7.0)  # なっぷは長めに待機
        self.geocoder = Geocoder()

    def scrape(self, max_pages: int = 5) -> list[dict]:
        """なっぷから東京・神奈川のBBQ・アウトドア施設を収集する"""

        # robots.txt チェック
        if not check_robots_txt():
            print("スクレイピングを中止します")
            return []

        all_spots: list[dict] = []
        for pref_name, pref_code in PREF_MAP.items():
            print(f"\n  {pref_name} のデータを取得中...")
            spots = self._scrape_prefecture(pref_name, pref_code, max_pages)
            all_spots.extend(spots)
            print(f"  {len(spots)} 件取得")

        return all_spots

    def _scrape_prefecture(self, pref_name: str, pref_code: str, max_pages: int) -> list[dict]:
        """指定都道府県のスポットを収集する"""
        spots = []

        for page in range(1, max_pages + 1):
            # なっぷの実際のURL構造に合わせて調整が必要
            url = f"{BASE_URL}/search/?pref={pref_code}&page={page}"
            try:
                soup = self.get_soup(url)
            except Exception as e:
                print(f"    ページ{page}の取得失敗: {e}")
                break

            # 施設カードを取得（実際のHTMLに合わせてセレクタを調整）
            items = soup.select(".facility-item, .spot-card, article")
            if not items:
                print(f"    ページ{page}: アイテムなし（終了）")
                break

            for item in items:
                link = item.find("a")
                if not link:
                    continue
                href = link.get("href", "")
                detail_url = href if href.startswith("http") else f"{BASE_URL}{href}"

                try:
                    spot = self._scrape_detail(detail_url, pref_name)
                    if spot:
                        spots.append(spot)
                except Exception as e:
                    print(f"    詳細取得エラー: {e}")

        return spots

    def _scrape_detail(self, url: str, pref_name: str) -> dict | None:
        """施設詳細ページから情報を取得する"""
        soup = self.get_soup(url)

        # 施設名
        name_el = soup.find("h1") or soup.find("h2")
        if not name_el:
            return None
        name = name_el.text.strip()

        # 住所
        address = None
        address_el = soup.find(class_=re.compile(r"address|addr", re.I))
        if address_el:
            address = address_el.text.strip()

        # 座標取得
        lat, lng = None, None
        if address:
            coords = self.geocoder.geocode(address)
            if coords:
                lat, lng = coords

        if lat is None or lng is None:
            return None
        if not self.geocoder.is_in_area(lat, lng):
            return None

        # 説明文
        desc_el = soup.find(class_=re.compile(r"desc|intro|about|overview", re.I))
        description = desc_el.text.strip() if desc_el else None

        # 設備・タグ情報
        facilities: list[str] = [el.text.strip() for el in soup.select(".tag, .facility, .amenity")]

        return {
            "name": name,
            "description": description,
            "category": classify_category(name, description or "", facilities),
            "latitude": lat,
            "longitude": lng,
            "source": SOURCE_ID,
            "source_url": url,
            "tags": classify_tags(name, description or "", facilities),
            "prefecture": pref_name,
        }


if __name__ == "__main__":
    import pandas as pd

    scraper = NapScraper()
    spots = scraper.scrape(max_pages=3)

    if spots:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        df = pd.DataFrame(spots)
        output_path = os.path.join(OUTPUT_DIR, "nap_spots.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n✅ {len(spots)} 件を保存: {output_path}")
    else:
        print("データが取得できませんでした")
