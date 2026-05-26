import spotsJson from "./spots.json";
import type { Spot } from "@/types/spot";

const ALL_SPOTS: Spot[] = spotsJson as Spot[];

/** 全スポットを返す */
export function loadAllSpots(): Spot[] {
  return ALL_SPOTS;
}

/** IDでスポットを検索する */
export function loadSpotById(id: string): Spot | null {
  return ALL_SPOTS.find((s) => s.id === id) ?? null;
}
