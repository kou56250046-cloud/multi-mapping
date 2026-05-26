export type SpotCategory =
  | "meditation"
  | "waterside"
  | "hidden_gem"
  | "waterfall"
  | "walking"
  | "sports"
  | "bbq";

export type SpotTag =
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

/** データ提供元の識別子 */
export type SpotSource =
  | "nap"
  | "tokyo_park"
  | "kanagawa_park"
  | "mlit"
  | "manual";

export interface Spot {
  id: string;
  name: string;
  description: string | null;
  category: SpotCategory;
  latitude: number;
  longitude: number;
  /** データ提供元 */
  source: SpotSource;
  /** 元データのURL（あれば） */
  source_url: string | null;
  created_at: string;
  updated_at: string;
  tags?: SpotTag[];
  /** 現在地からの距離（計算値・任意） */
  distance_km?: number;
}
