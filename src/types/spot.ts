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

export interface Spot {
  id: string;
  name: string;
  description: string | null;
  category: SpotCategory;
  latitude: number;
  longitude: number;
  nickname: string | null;
  created_at: string;
  updated_at: string;
  tags?: SpotTag[];
  distance_km?: number;
}

export interface SpotCreatePayload {
  name: string;
  description?: string;
  category: SpotCategory;
  latitude: number;
  longitude: number;
  nickname?: string;
  tags: SpotTag[];
  turnstileToken: string;
}
