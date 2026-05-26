"""
scraper/app.py — スポット管理 Streamlit UI

起動方法:
  cd scraper
  pip install -r requirements.txt
  streamlit run app.py

ページ構成:
  1. 📡 スクレイパー実行  — スクレイパーをGUIで選択・実行・ログ確認
  2. ✏️ データ編集       — CSV を表形式で確認・編集・保存
  3. 🗺️ 地図プレビュー   — folium でスポットを地図表示
  4. 📦 JSON変換・ビルド — npm run generate / npm run build を実行
"""

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# ---- パス設定 ----
SCRAPER_DIR = Path(__file__).parent
ROOT_DIR = SCRAPER_DIR.parent
OUTPUT_SPOTS_CSV = SCRAPER_DIR / "output" / "spots.csv"
FINAL_CSV = ROOT_DIR / "data" / "spots.csv"
SPOTS_JSON = ROOT_DIR / "src" / "lib" / "data" / "spots.json"

# ---- カテゴリ設定（categoryConfig.ts と同期） ----
CATEGORY_CONFIG: dict[str, dict] = {
    "meditation": {"label": "瞑想・癒し",  "icon": "🧘", "color": "#a78bfa"},
    "waterside":  {"label": "川・水辺",    "icon": "🏞️", "color": "#60a5fa"},
    "hidden_gem": {"label": "穴場",        "icon": "💎", "color": "#f472b6"},
    "waterfall":  {"label": "滝",          "icon": "💦", "color": "#22d3ee"},
    "walking":    {"label": "散歩道",      "icon": "🚶", "color": "#84cc16"},
    "sports":     {"label": "スポーツ",    "icon": "⚽", "color": "#f97316"},
    "bbq":        {"label": "BBQ",         "icon": "🍖", "color": "#ef4444"},
}

SOURCE_LABELS: dict[str, str] = {
    "overpass":      "OpenStreetMap",
    "tokyo_park":    "東京都立公園",
    "kanagawa_park": "神奈川県立公園",
    "nap":           "なっぷ",
    "mlit":          "国土数値情報（非推奨）",
    "manual":        "手動入力",
}

VALID_TAGS = [
    "few_people", "bbq_ok", "toilet", "parking", "water",
    "bench", "shade", "pet_ok", "wheelchair", "night_view",
    "cherry_blossom", "autumn_leaves",
]

CSV_COLUMNS = [
    "id", "name", "description", "category",
    "latitude", "longitude", "source", "source_url", "tags", "prefecture",
]

# ---- ページ設定 ----
st.set_page_config(
    page_title="スポット管理ツール",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---- セッションステート初期化 ----
def init_session_state():
    defaults: dict = {
        "scraping_running": False,
        "scraping_done": False,
        "scraping_log": [],
        "log_queue": None,
        "page": "scraper_run",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---- CSV ロードユーティリティ ----
def load_csv() -> pd.DataFrame | None:
    """output/spots.csv を読み込む。存在しない場合は None"""
    if OUTPUT_SPOTS_CSV.exists():
        return pd.read_csv(OUTPUT_SPOTS_CSV, dtype=str).fillna("")
    return None


# ========== サイドバー ==========

def render_sidebar() -> str:
    with st.sidebar:
        st.title("🗺️ スポット管理")
        st.divider()

        page = st.radio(
            "ページを選択",
            ["scraper_run", "data_editor", "map_preview", "json_build"],
            format_func=lambda k: {
                "scraper_run":  "📡 スクレイパー実行",
                "data_editor":  "✏️ データ編集",
                "map_preview":  "🗺️ 地図プレビュー",
                "json_build":   "📦 JSON変換・ビルド",
            }[k],
            key="page",
        )

        st.divider()

        # CSVサマリー
        df = load_csv()
        if df is not None:
            st.metric("登録スポット数", len(df))
            st.caption(f"📁 {OUTPUT_SPOTS_CSV.name}")
        else:
            st.info("spots.csv が存在しません\nまずスクレイパーを実行してください")

    return page  # type: ignore[return-value]


# ========== ページ1: スクレイパー実行 ==========

def page_scraper_run():
    st.title("📡 スクレイパー実行")
    st.caption("実行するデータソースを選択してスクレイピングを開始します")

    # ---- スクレイパー選択 ----
    st.subheader("データソース選択")
    col1, col2 = st.columns(2)
    with col1:
        run_overpass = st.checkbox(
            "🗺️ OpenStreetMap (Overpass API)",
            value=True,
            help="無料・認証不要・ODbLライセンス (© OpenStreetMap contributors)。東京・神奈川の公園・滝・川・BBQスポットを取得。最優先推奨。",
        )
        run_tokyo    = st.checkbox("🌿 東京都立公園", value=True, help="tokyo-park.or.jp からスクレイピング")
    with col2:
        run_kanagawa = st.checkbox("🌿 神奈川県立公園", value=True, help="kanagawa-park.or.jp からスクレイピング")
        run_nap      = st.checkbox("🍖 なっぷ (nap.jp)", help="BBQ・アウトドア施設専門サイト。robots.txt 確認必須。")

    # なっぷ選択時の確認
    nap_confirmed = False
    if run_nap:
        st.warning(
            "**⚠️ なっぷ選択時の注意事項**\n\n"
            "スクレイピング前に必ず [robots.txt](https://nap.jp/robots.txt) を確認してください。"
            " Disallow ルールと Crawl-delay を厳守することが必要です。"
            " ユーザーレビュー・写真は著作権があるため取得しません（施設名・住所・設備情報のみ）。"
        )
        nap_confirmed = st.checkbox(
            "✅ robots.txt を確認済みです。Disallow ルールに違反していないことを確認しました。",
            key="nap_robots_confirmed",
        )
        if not nap_confirmed:
            st.error("なっぷを実行するには上記チェックが必要です")

    # 実行対象のソースリストを構築
    selected_sources = []
    if run_overpass:      selected_sources.append("overpass")
    if run_tokyo:         selected_sources.append("tokyo_park")
    if run_kanagawa:      selected_sources.append("kanagawa_park")
    if run_nap and nap_confirmed: selected_sources.append("nap")

    can_start = len(selected_sources) > 0 and not st.session_state.scraping_running

    st.divider()

    # ---- 実行ボタン ----
    col_btn, col_status = st.columns([2, 5])
    with col_btn:
        start = st.button(
            "🚀 スクレイピング開始",
            disabled=not can_start,
            type="primary",
            use_container_width=True,
        )
    with col_status:
        if st.session_state.scraping_running:
            st.info("⏳ 実行中です...")
        elif st.session_state.scraping_done:
            st.success("✅ 完了しました")
        elif not selected_sources:
            st.warning("ソースを1つ以上選択してください")

    # スクレイピング開始
    if start and can_start:
        _start_scraping(selected_sources)

    # ---- ログ表示 ----
    if st.session_state.scraping_running or st.session_state.scraping_log:
        _render_log()

    # ---- 完了サマリー ----
    if st.session_state.scraping_done:
        _render_scraping_summary()

    # ---- 既存データをインポート ----
    st.divider()
    _render_import_section()


def _render_import_section():
    """spots.json の手動データをCSVに変換してインポートするセクション"""
    with st.expander("📥 既存データをインポート（スクレイピングが失敗した場合）", expanded=False):
        st.markdown(
            "現在 `src/lib/data/spots.json` に登録済みの手動データをCSVとしてインポートします。\n"
            "スクレイパーが動作しない間も、データ編集・地図プレビュー・JSON変換を確認できます。"
        )

        if not SPOTS_JSON.exists():
            st.warning("spots.json が見つかりません")
            return

        with open(SPOTS_JSON, encoding="utf-8") as f:
            spots_data: list[dict] = json.load(f)

        st.info(f"spots.json に **{len(spots_data)} 件**のデータがあります")

        if st.button("📥 spots.json をCSVとしてインポート", type="secondary"):
            rows = []
            for i, s in enumerate(spots_data):
                tags = s.get("tags", [])
                rows.append({
                    "id": s.get("id") or f"manual-{str(i+1).zfill(4)}",
                    "name": s.get("name", ""),
                    "description": s.get("description") or "",
                    "category": s.get("category", "walking"),
                    "latitude": s.get("latitude", 0),
                    "longitude": s.get("longitude", 0),
                    "source": s.get("source", "manual"),
                    "source_url": s.get("source_url") or "",
                    "tags": ";".join(tags) if isinstance(tags, list) else (tags or ""),
                    "prefecture": s.get("prefecture", "tokyo"),
                })

            df = pd.DataFrame(rows)
            OUTPUT_SPOTS_CSV.parent.mkdir(parents=True, exist_ok=True)
            FINAL_CSV.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(OUTPUT_SPOTS_CSV, index=False, encoding="utf-8-sig")
            df.to_csv(FINAL_CSV, index=False, encoding="utf-8-sig")
            st.success(f"✅ {len(df)} 件をCSVとしてインポートしました！\n「データ編集」や「地図プレビュー」ページで確認できます。")
            st.rerun()


def _start_scraping(sources: list[str]):
    """subprocess + threading でスクレイパーを非同期起動する"""
    st.session_state.scraping_running = True
    st.session_state.scraping_done = False
    st.session_state.scraping_log = ["▶ スクレイピングを開始します..."]

    env = os.environ.copy()
    env["NAP_SCRAPING_ENABLED"] = "true" if "nap" in sources else "false"

    cmd = [
        sys.executable,
        str(SCRAPER_DIR / "run_all.py"),
        "--sources", ",".join(sources),
    ]

    log_q: queue.Queue = queue.Queue()
    st.session_state.log_queue = log_q

    def _reader(proc: subprocess.Popen):
        for line in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
            log_q.put(("log", line.rstrip()))
        proc.wait()
        log_q.put(("done", proc.returncode))

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(SCRAPER_DIR),
    )
    t = threading.Thread(target=_reader, args=(proc,), daemon=True)
    t.start()


def _render_log():
    """キューをドレインしてログを画面に表示。実行中は st.rerun() でポーリング"""
    q: queue.Queue | None = st.session_state.log_queue
    done = False

    if q is not None:
        while not q.empty():
            msg_type, content = q.get_nowait()
            if msg_type == "log":
                st.session_state.scraping_log.append(content)
            elif msg_type == "done":
                st.session_state.scraping_running = False
                st.session_state.scraping_done = True
                done = True

    log_text = "\n".join(st.session_state.scraping_log[-300:])
    st.code(log_text, language=None)

    if st.session_state.scraping_running and not done:
        time.sleep(0.3)
        st.rerun()


def _render_scraping_summary():
    """完了後のサマリー表示"""
    df = load_csv()
    if df is None or len(df) == 0:
        st.error(
            "**スポットが取得できませんでした。**\n\n"
            "考えられる原因:\n"
            "- ネットワーク接続の問題（タイムアウト等）\n"
            "- 対象サイトのHTML構造変更・URL変更\n"
            "- GMLデータの名前空間・要素名の変更\n\n"
            "上のログを確認して詳細なエラーを確認してください。\n\n"
            "**→ 下の「既存データをインポート」で手動データを読み込み、パイプラインを確認できます。**"
        )
        return

    st.divider()
    st.subheader("📊 取得結果サマリー")
    col1, col2, col3 = st.columns(3)
    col1.metric("取得スポット数", len(df))
    col2.metric("カテゴリ数", df["category"].nunique())
    col3.metric("ソース数", df["source"].nunique())

    # カテゴリ別件数グラフ
    cat_df = (
        df["category"]
        .value_counts()
        .rename_axis("category")
        .reset_index(name="件数")
    )
    cat_df["表示名"] = cat_df["category"].map(
        lambda c: f"{CATEGORY_CONFIG.get(c, {}).get('icon', '')} {CATEGORY_CONFIG.get(c, {}).get('label', c)}"
    )
    st.bar_chart(cat_df.set_index("表示名")["件数"])


# ========== ページ2: データ編集 ==========

def page_data_editor():
    st.title("✏️ データ編集")

    df_all = load_csv()
    if df_all is None:
        st.warning("output/spots.csv が存在しません。先にスクレイパーを実行してください。")
        return

    # ---- フィルター（サイドバー） ----
    with st.sidebar:
        st.subheader("🔍 フィルター")
        all_cats = sorted(df_all["category"].dropna().unique().tolist())
        sel_cats = st.multiselect(
            "カテゴリ", all_cats, default=all_cats,
            format_func=lambda c: f"{CATEGORY_CONFIG.get(c, {}).get('icon', '')} {CATEGORY_CONFIG.get(c, {}).get('label', c)}",
        )
        all_prefs = sorted(df_all["prefecture"].dropna().unique().tolist())
        sel_prefs = st.multiselect("都道府県", all_prefs, default=all_prefs)
        all_sources = sorted(df_all["source"].dropna().unique().tolist())
        sel_sources = st.multiselect(
            "ソース", all_sources, default=all_sources,
            format_func=lambda s: SOURCE_LABELS.get(s, s),
        )

    # フィルター適用
    mask = (
        df_all["category"].isin(sel_cats) &
        df_all["prefecture"].isin(sel_prefs) &
        df_all["source"].isin(sel_sources)
    )
    df_view = df_all[mask].copy()

    st.caption(f"{len(df_view)} 件 / {len(df_all)} 件を表示中")

    # ---- data_editor ----
    edited_df = st.data_editor(
        df_view,
        use_container_width=True,
        num_rows="dynamic",
        height=520,
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
            "name": st.column_config.TextColumn("名前", width="medium"),
            "description": st.column_config.TextColumn("説明", width="large"),
            "category": st.column_config.SelectboxColumn(
                "カテゴリ",
                options=list(CATEGORY_CONFIG.keys()),
                width="small",
            ),
            "latitude": st.column_config.NumberColumn("緯度", format="%.6f", width="small"),
            "longitude": st.column_config.NumberColumn("経度", format="%.6f", width="small"),
            "source": st.column_config.SelectboxColumn(
                "ソース",
                options=list(SOURCE_LABELS.keys()),
                width="small",
            ),
            "source_url": st.column_config.LinkColumn("元URL", width="medium"),
            "tags": st.column_config.TextColumn(
                "タグ（;区切り）",
                help=f"使用可能なタグ: {', '.join(VALID_TAGS)}",
                width="medium",
            ),
            "prefecture": st.column_config.SelectboxColumn(
                "都道府県",
                options=["tokyo", "kanagawa"],
                width="small",
            ),
        },
        hide_index=True,
        key="spots_editor",
    )

    # ---- 保存ボタン ----
    col1, col2 = st.columns([1, 6])
    with col1:
        save = st.button("💾 保存", type="primary", use_container_width=True)

    if save:
        _save_edited(df_all, mask, edited_df)


def _save_edited(df_all: pd.DataFrame, mask: pd.Series, edited_df: pd.DataFrame):
    """フィルター対象外の行を保持しつつ編集済み行と結合して保存する"""
    df_others = df_all[~mask].copy()
    df_final = pd.concat([df_others, edited_df], ignore_index=True)

    # カラム順を保証
    for col in CSV_COLUMNS:
        if col not in df_final.columns:
            df_final[col] = ""
    df_final = df_final[CSV_COLUMNS]

    # 保存
    OUTPUT_SPOTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    FINAL_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(OUTPUT_SPOTS_CSV, index=False, encoding="utf-8-sig")
    df_final.to_csv(FINAL_CSV, index=False, encoding="utf-8-sig")

    st.success(f"✅ {len(df_final)} 件を保存しました（output/spots.csv と data/spots.csv）")
    st.info("💡 次は「JSON変換・ビルド」ページで `npm run generate` を実行してください")


# ========== ページ3: 地図プレビュー ==========

def page_map_preview():
    st.title("🗺️ 地図プレビュー")

    df_all = load_csv()
    if df_all is None:
        st.warning("output/spots.csv が存在しません。先にスクレイパーを実行してください。")
        return

    # 座標を数値変換・無効行を除外
    df = df_all.copy()
    df["latitude"]  = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]

    if df.empty:
        st.warning("有効な座標データがありません")
        return

    # ---- フィルター（サイドバー） ----
    with st.sidebar:
        st.subheader("🔍 地図フィルター")
        show_cats = st.multiselect(
            "カテゴリ",
            list(CATEGORY_CONFIG.keys()),
            default=list(CATEGORY_CONFIG.keys()),
            format_func=lambda c: f"{CATEGORY_CONFIG[c]['icon']} {CATEGORY_CONFIG[c]['label']}",
        )
    df_map = df[df["category"].isin(show_cats)]

    # ---- カテゴリ別メトリクス ----
    cols = st.columns(len(CATEGORY_CONFIG))
    for i, (cat_key, cat_info) in enumerate(CATEGORY_CONFIG.items()):
        count = int((df["category"] == cat_key).sum())
        cols[i].metric(
            f"{cat_info['icon']} {cat_info['label']}",
            count,
        )
    st.divider()

    # ---- folium 地図生成 ----
    center_lat = float(df_map["latitude"].mean())
    center_lng = float(df_map["longitude"].mean())

    fmap = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=10,
        tiles="OpenStreetMap",
    )

    for _, row in df_map.iterrows():
        cat = str(row.get("category", "walking"))
        cat_info = CATEGORY_CONFIG.get(cat, {"color": "#6b7280", "label": cat, "icon": "📍"})

        # タグ整形
        tags_raw = str(row.get("tags", ""))
        tags_html = ""
        if tags_raw:
            tags_html = "<br>🏷️ " + " / ".join(t.strip() for t in tags_raw.split(";") if t.strip())

        popup_html = f"""
        <div style="min-width:180px; font-family:sans-serif">
            <b style="font-size:14px">{row['name']}</b><br>
            <span style="color:{cat_info['color']}">{cat_info['icon']} {cat_info['label']}</span>
            {tags_html}
        </div>
        """

        folium.CircleMarker(
            location=[float(row["latitude"]), float(row["longitude"])],
            radius=8,
            color=cat_info["color"],
            fill=True,
            fill_color=cat_info["color"],
            fill_opacity=0.85,
            weight=2,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=row["name"],
        ).add_to(fmap)

    # 凡例
    legend_items = "".join(
        f'<div style="margin:3px 0">'
        f'<span style="background:{info["color"]};width:13px;height:13px;'
        f'display:inline-block;border-radius:50%;margin-right:6px;vertical-align:middle"></span>'
        f'{info["icon"]} {info["label"]}'
        f'</div>'
        for info in CATEGORY_CONFIG.values()
    )
    legend_html = f"""
    <div style="position:fixed;bottom:36px;left:36px;background:rgba(255,255,255,0.95);
                padding:12px 16px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.25);
                z-index:9999;font-size:13px;line-height:1.6">
        <b>凡例</b><br>{legend_items}
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))

    # ---- 地図表示 ----
    map_data = st_folium(
        fmap,
        use_container_width=True,
        height=580,
        returned_objects=["last_object_clicked_tooltip"],
    )

    # クリックされたスポットの詳細表示
    clicked_name = map_data.get("last_object_clicked_tooltip") if map_data else None
    if clicked_name:
        found = df_map[df_map["name"] == clicked_name]
        if not found.empty:
            row = found.iloc[0]
            with st.expander(f"📍 {row['name']}", expanded=True):
                c1, c2 = st.columns(2)
                c1.write(f"**カテゴリ:** {CATEGORY_CONFIG.get(row['category'], {}).get('label', row['category'])}")
                c2.write(f"**提供元:** {SOURCE_LABELS.get(row['source'], row['source'])}")
                if row.get("description"):
                    st.write(f"**説明:** {row['description']}")
                if row.get("tags"):
                    st.write(f"**タグ:** {row['tags']}")
                if row.get("source_url"):
                    st.write(f"[元ページを見る →]({row['source_url']})")


# ========== ページ4: JSON変換・ビルド ==========

def page_json_build():
    st.title("📦 JSON変換・ビルド")

    # ---- セクション1: JSON変換 ----
    st.subheader("1. JSON変換（npm run generate）")
    st.caption("`data/spots.csv` を読み込み、バリデーションして `src/lib/data/spots.json` に変換します")

    if FINAL_CSV.exists():
        df_csv = pd.read_csv(FINAL_CSV)
        st.info(f"📄 data/spots.csv: **{len(df_csv)} 件**")
    else:
        st.warning("data/spots.csv が存在しません。先にデータ編集ページで保存してください。")

    generate_btn = st.button("⚙️ JSON変換を実行", type="primary", disabled=not FINAL_CSV.exists())

    if generate_btn:
        with st.spinner("npm run generate を実行中..."):
            result = subprocess.run(
                ["npm", "run", "generate"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(ROOT_DIR),
            )

        log_text = (result.stdout + result.stderr).strip()
        st.code(log_text, language=None)

        if result.returncode == 0:
            st.success("✅ JSON変換が完了しました")
        else:
            st.error(f"❌ エラーが発生しました（終了コード: {result.returncode}）")

    # ---- セクション2: JSONプレビュー ----
    if SPOTS_JSON.exists():
        st.divider()
        st.subheader("2. 変換済み JSON プレビュー")

        with open(SPOTS_JSON, encoding="utf-8") as f:
            spots_data: list[dict] = json.load(f)

        # 統計
        col1, col2 = st.columns(2)
        col1.metric("有効スポット数", len(spots_data))
        if FINAL_CSV.exists():
            df_csv2 = pd.read_csv(FINAL_CSV)
            col2.metric("スキップ件数（概算）", len(df_csv2) - len(spots_data))

        # カテゴリ別集計
        from collections import Counter
        cat_count = Counter(s.get("category", "unknown") for s in spots_data)
        cat_df = pd.DataFrame(
            [{"カテゴリ": CATEGORY_CONFIG.get(c, {}).get("label", c), "件数": n}
             for c, n in cat_count.most_common()],
        )
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

        # 先頭5件プレビュー
        with st.expander("先頭 5 件を表示"):
            st.json(spots_data[:5])

    # ---- セクション3: Next.jsビルド ----
    st.divider()
    st.subheader("3. Next.js ビルド（任意）")
    st.caption("`npm run build` を実行して本番用ファイルを生成します。数分かかる場合があります。")

    build_btn = st.button(
        "🏗️ npm run build を実行",
        disabled=not SPOTS_JSON.exists(),
        help="JSON変換が完了してから実行してください",
    )

    if build_btn:
        build_log_area = st.empty()
        with st.spinner("npm run build を実行中（しばらくお待ちください）..."):
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(ROOT_DIR),
            )
        build_log_area.code((result.stdout + result.stderr).strip(), language=None)
        if result.returncode == 0:
            st.success("✅ ビルドが完了しました")
        else:
            st.error(f"❌ ビルドエラー（終了コード: {result.returncode}）")


# ========== メイン ==========

def main():
    init_session_state()
    page = render_sidebar()

    if page == "scraper_run":
        page_scraper_run()
    elif page == "data_editor":
        page_data_editor()
    elif page == "map_preview":
        page_map_preview()
    elif page == "json_build":
        page_json_build()


if __name__ == "__main__":
    main()
