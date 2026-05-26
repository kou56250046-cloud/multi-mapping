/**
 * scripts/csv-to-json.ts
 *
 * data/spots.csv を読み込み、バリデーションして
 * src/lib/data/spots.json に出力する。
 *
 * 実行: node --experimental-strip-types scripts/csv-to-json.ts
 *
 * CSVフォーマット（ヘッダー行必須）:
 * id,name,description,category,latitude,longitude,source,source_url,tags,prefecture
 *
 * - tags: セミコロン区切り例: bbq_ok;toilet;parking
 * - prefecture: tokyo / kanagawa
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");

// ---- 型定義 ----
type SpotCategory =
  | "meditation"
  | "waterside"
  | "hidden_gem"
  | "waterfall"
  | "walking"
  | "sports"
  | "bbq";

type SpotTag =
  | "few_people"
  | "bbq_ok"
  | "toilet"
  | "parking"
  | "water"
  | "bench"
  | "shade"
  | "pet_ok"
  | "wheelchair"
  | "night_view"
  | "cherry_blossom"
  | "autumn_leaves";

type SpotSource = "nap" | "tokyo_park" | "kanagawa_park" | "mlit" | "manual";

interface Spot {
  id: string;
  name: string;
  description: string | null;
  category: SpotCategory;
  latitude: number;
  longitude: number;
  source: SpotSource;
  source_url: string | null;
  created_at: string;
  updated_at: string;
  tags?: SpotTag[];
}

// ---- バリデーション定数 ----
const VALID_CATEGORIES = new Set<SpotCategory>([
  "meditation", "waterside", "hidden_gem", "waterfall", "walking", "sports", "bbq",
]);
const VALID_TAGS = new Set<SpotTag>([
  "few_people", "bbq_ok", "toilet", "parking", "water", "bench", "shade",
  "pet_ok", "wheelchair", "night_view", "cherry_blossom", "autumn_leaves",
]);
const VALID_SOURCES = new Set<SpotSource>([
  "nap", "tokyo_park", "kanagawa_park", "mlit", "manual",
]);

/** 東京・神奈川エリアの座標範囲チェック */
function isInArea(lat: number, lng: number): boolean {
  return lat >= 35.0 && lat <= 36.1 && lng >= 138.8 && lng <= 140.0;
}

/** 簡易CSVパーサー（ダブルクォート内のカンマ対応） */
function parseCsv(content: string): Record<string, string>[] {
  const lines = content.trim().split(/\r?\n/);
  if (lines.length < 2) return [];
  const headers = lines[0].split(",").map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const values: string[] = [];
    let cur = "";
    let inQuote = false;
    for (const ch of line) {
      if (ch === '"') { inQuote = !inQuote; }
      else if (ch === "," && !inQuote) { values.push(cur.trim()); cur = ""; }
      else { cur += ch; }
    }
    values.push(cur.trim());
    return Object.fromEntries(headers.map((h, i) => [h, values[i] ?? ""]));
  });
}

/** 1行をSpotオブジェクトに変換。無効な場合はnullを返す */
function rowToSpot(row: Record<string, string>, rowNum: number): Spot | null {
  const warn = (msg: string) => console.warn(`  [行 ${rowNum}] スキップ: ${msg} (${row.name || "名前なし"})`);

  if (!row.name?.trim()) { warn("名前が空"); return null; }

  const lat = parseFloat(row.latitude);
  const lng = parseFloat(row.longitude);
  if (isNaN(lat) || isNaN(lng)) { warn(`座標が不正 (${row.latitude}, ${row.longitude})`); return null; }
  if (!isInArea(lat, lng)) { warn(`エリア外の座標 (${lat.toFixed(4)}, ${lng.toFixed(4)})`); return null; }

  if (!VALID_CATEGORIES.has(row.category as SpotCategory)) {
    warn(`カテゴリ不正 "${row.category}"`);
    return null;
  }

  const source: SpotSource = VALID_SOURCES.has(row.source as SpotSource)
    ? (row.source as SpotSource)
    : "manual";

  const tags: SpotTag[] = row.tags
    ? row.tags.split(";").map((t) => t.trim()).filter((t) => VALID_TAGS.has(t as SpotTag)) as SpotTag[]
    : [];

  const now = new Date().toISOString();
  return {
    id: row.id?.trim() || `spot-${String(rowNum).padStart(4, "0")}`,
    name: row.name.trim(),
    description: row.description?.trim() || null,
    category: row.category as SpotCategory,
    latitude: lat,
    longitude: lng,
    source,
    source_url: row.source_url?.trim() || null,
    created_at: now,
    updated_at: now,
    ...(tags.length > 0 && { tags }),
  };
}

// ---- メイン処理 ----
const csvPath = join(ROOT, "data", "spots.csv");
const outputPath = join(ROOT, "src", "lib", "data", "spots.json");

if (!existsSync(csvPath)) {
  console.log(`ℹ️  ${csvPath} が見つかりません。既存の spots.json を維持します。`);
  process.exit(0);
}

console.log(`📂 CSVを読み込み中: ${csvPath}`);
const csvContent = readFileSync(csvPath, "utf-8");
const rows = parseCsv(csvContent);
console.log(`   ${rows.length} 行を検出`);

const spots: Spot[] = [];
let skipped = 0;

for (let i = 0; i < rows.length; i++) {
  const spot = rowToSpot(rows[i], i + 2); // 行番号は2始まり（1行目はヘッダー）
  if (spot) spots.push(spot);
  else skipped++;
}

// ID重複チェック
const ids = spots.map((s) => s.id);
const duplicates = ids.filter((id, i) => ids.indexOf(id) !== i);
if (duplicates.length > 0) {
  console.error(`❌ IDが重複しています: ${duplicates.join(", ")}`);
  process.exit(1);
}

writeFileSync(outputPath, JSON.stringify(spots, null, 2) + "\n", "utf-8");

console.log(`\n✅ 変換完了`);
console.log(`   有効: ${spots.length} 件 → ${outputPath}`);
if (skipped > 0) console.log(`   スキップ: ${skipped} 件`);
