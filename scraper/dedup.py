"""
スポットの重複排除
複数ソースから同じ施設が取得された場合に、100m以内の同名スポットを重複とみなして除去する
"""

from math import radians, cos, sin, asin, sqrt


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """2点間のハーバーサイン距離（km）を計算する"""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return R * 2 * asin(sqrt(a))


def deduplicate(
    spots: list[dict],
    distance_threshold_km: float = 0.1,
    name_match: bool = True,
) -> list[dict]:
    """
    スポットリストから重複を除去する。

    Args:
        spots: スポット辞書のリスト（source優先度順にソートしておくと良い）
        distance_threshold_km: 同一スポットとみなす距離（デフォルト100m）
        name_match: Trueの場合、名前が同じかつ距離以内のものを重複とみなす

    Returns:
        重複を除去したスポットリスト
    """
    unique: list[dict] = []

    for spot in spots:
        is_dup = False
        for existing in unique:
            dist = haversine_km(
                spot["latitude"], spot["longitude"],
                existing["latitude"], existing["longitude"],
            )
            if dist < distance_threshold_km:
                # 距離以内にある場合
                if not name_match or spot["name"] == existing["name"]:
                    is_dup = True
                    break
        if not is_dup:
            unique.append(spot)

    return unique
