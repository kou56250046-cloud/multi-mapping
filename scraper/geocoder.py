"""
住所→緯度経度変換（国土地理院ジオコーディングAPI使用）

無料・商用利用可・レート制限なし
https://msearch.gsi.go.jp/address-search/AddressSearch?q={住所}
"""

import time
import requests
from config import GSI_GEOCODE_URL, AREA


class Geocoder:
    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self._cache: dict[str, tuple[float, float] | None] = {}

    def geocode(self, address: str) -> tuple[float, float] | None:
        """
        住所を (latitude, longitude) タプルに変換する。
        変換できない場合は None を返す。
        """
        address = address.strip()
        if not address:
            return None
        if address in self._cache:
            return self._cache[address]

        time.sleep(self.delay)
        try:
            resp = requests.get(
                GSI_GEOCODE_URL,
                params={"q": address},
                timeout=10,
            )
            data = resp.json()
            if data:
                # 最初の候補を使用
                # レスポンス形式: [{"geometry": {"coordinates": [lng, lat]}, ...}]
                coords = data[0]["geometry"]["coordinates"]
                result: tuple[float, float] = (coords[1], coords[0])  # (lat, lng)
                self._cache[address] = result
                return result
        except Exception as e:
            print(f"    ジオコーディング失敗 ({address}): {e}")

        self._cache[address] = None
        return None

    def is_in_area(self, lat: float, lng: float) -> bool:
        """東京・神奈川エリア内の座標かチェックする"""
        return (
            AREA["lat_min"] <= lat <= AREA["lat_max"]
            and AREA["lng_min"] <= lng <= AREA["lng_max"]
        )
