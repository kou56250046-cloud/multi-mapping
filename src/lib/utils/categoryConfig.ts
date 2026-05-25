import type { SpotCategory } from "@/types/spot";

export interface CategoryDef {
  value: SpotCategory;
  label: string;
  icon: string;
  color: string;
}

export const CATEGORIES: CategoryDef[] = [
  { value: "meditation", label: "瞑想・癒し", icon: "🧘", color: "#a78bfa" },
  { value: "waterside", label: "川・水辺", icon: "🏞️", color: "#60a5fa" },
  { value: "hidden_gem", label: "穴場", icon: "💎", color: "#f472b6" },
  { value: "waterfall", label: "滝", icon: "💦", color: "#22d3ee" },
  { value: "walking", label: "散歩道", icon: "🚶", color: "#84cc16" },
  { value: "sports", label: "スポーツ", icon: "⚽", color: "#f97316" },
  { value: "bbq", label: "BBQ", icon: "🍖", color: "#ef4444" },
];

export const CATEGORY_MAP = new Map(CATEGORIES.map((c) => [c.value, c]));

export function getCategoryLabel(value: SpotCategory): string {
  return CATEGORY_MAP.get(value)?.label ?? value;
}

export function getCategoryIcon(value: SpotCategory): string {
  return CATEGORY_MAP.get(value)?.icon ?? "📍";
}

export function getCategoryColor(value: SpotCategory): string {
  return CATEGORY_MAP.get(value)?.color ?? "#6b7280";
}
