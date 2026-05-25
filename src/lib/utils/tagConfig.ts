import type { SpotTag } from "@/types/spot";

export interface TagDef {
  value: SpotTag;
  label: string;
  icon: string;
}

export const TAGS: TagDef[] = [
  { value: "few_people", label: "人少ない", icon: "🤫" },
  { value: "bbq_ok", label: "BBQ可", icon: "🔥" },
  { value: "toilet", label: "トイレあり", icon: "🚻" },
  { value: "parking", label: "駐車場あり", icon: "🅿️" },
  { value: "water", label: "水道あり", icon: "🚰" },
  { value: "bench", label: "ベンチあり", icon: "🪑" },
  { value: "shade", label: "日陰あり", icon: "🌳" },
  { value: "pet_ok", label: "ペット可", icon: "🐕" },
  { value: "wheelchair", label: "バリアフリー", icon: "♿" },
  { value: "night_view", label: "夜景", icon: "🌃" },
  { value: "cherry_blossom", label: "桜", icon: "🌸" },
  { value: "autumn_leaves", label: "紅葉", icon: "🍁" },
];

export const TAG_MAP = new Map(TAGS.map((t) => [t.value, t]));

export function getTagLabel(value: SpotTag): string {
  return TAG_MAP.get(value)?.label ?? value;
}

export function getTagIcon(value: SpotTag): string {
  return TAG_MAP.get(value)?.icon ?? "🏷️";
}

export function isValidTag(value: string): value is SpotTag {
  return TAG_MAP.has(value as SpotTag);
}
