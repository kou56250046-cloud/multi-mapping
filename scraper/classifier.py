"""
スポット名・説明・設備情報からカテゴリとタグを自動判定する
"""

from typing import Literal

SpotCategory = Literal[
    "meditation", "waterside", "hidden_gem", "waterfall", "walking", "sports", "bbq"
]
SpotTag = Literal[
    "few_people", "bbq_ok", "toilet", "parking", "water", "bench", "shade",
    "pet_ok", "wheelchair", "night_view", "cherry_blossom", "autumn_leaves",
]

# カテゴリ判定キーワード（上位が優先される）
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("bbq",        ["バーベキュー", "BBQ", "bbq", "炭火", "バーベキュー場"]),
    ("waterfall",  ["滝", "たき", "瀑布", "落差"]),
    ("waterside",  ["川", "河川", "水辺", "池", "湖", "沼", "渓谷", "沢", "海", "水遊び", "磯"]),
    ("sports",     ["スポーツ", "野球", "サッカー", "テニス", "運動", "球技", "陸上", "プール"]),
    ("walking",    ["散歩", "ハイキング", "トレッキング", "登山", "遊歩道", "ウォーキング", "山"]),
    ("meditation", ["瞑想", "静寂", "癒し", "禅", "坐禅", "静か"]),
    ("hidden_gem", ["穴場", "秘境", "知る人ぞ知る", "隠れ"]),
]

# タグ判定キーワード
TAG_RULES: list[tuple[str, list[str]]] = [
    ("bbq_ok",         ["バーベキュー可", "BBQ可", "BBQ場", "バーベキュー場", "バーベキューエリア", "炉"]),
    ("toilet",         ["トイレ", "公衆トイレ", "便所", "WC", "多目的トイレ"]),
    ("parking",        ["駐車場", "パーキング", "駐車", "P有", "無料駐車", "有料駐車"]),
    ("water",          ["水道", "流し台", "給水", "水場", "手洗い場"]),
    ("bench",          ["ベンチ", "休憩所", "東屋", "あずまや", "休憩スペース"]),
    ("shade",          ["日陰", "木陰", "緑陰", "林", "森", "木々"]),
    ("pet_ok",         ["ペット可", "犬可", "ペットOK", "愛犬", "犬同伴", "ペット歓迎"]),
    ("wheelchair",     ["バリアフリー", "車椅子", "スロープ", "多目的", "UD"]),
    ("night_view",     ["夜景", "ライトアップ", "イルミネーション"]),
    ("cherry_blossom", ["桜", "お花見", "ソメイヨシノ", "花見"]),
    ("autumn_leaves",  ["紅葉", "もみじ", "紅葉狩り", "秋の葉"]),
    ("few_people",     ["静か", "人が少", "混雑なし", "穴場", "のんびり", "人少"]),
]


def classify_category(
    name: str,
    description: str = "",
    facility_tags: list[str] | None = None,
) -> str:
    """スポット名・説明・設備タグからカテゴリを判定する。デフォルトは 'walking'"""
    text = f"{name} {description} {' '.join(facility_tags or [])}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            return category
    return "walking"


def classify_tags(
    name: str,
    description: str = "",
    facilities: list[str] | None = None,
) -> list[str]:
    """スポット名・説明・設備情報からタグリストを判定する"""
    text = f"{name} {description} {' '.join(facilities or [])}".lower()
    return [tag for tag, keywords in TAG_RULES if any(kw in text for kw in keywords)]
