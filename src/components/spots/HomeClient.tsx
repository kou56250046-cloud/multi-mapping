"use client";

import { useMemo } from "react";
import { useSearchParams } from "next/navigation";
import MapView from "@/components/map/MapView";
import SpotFilter from "@/components/spots/SpotFilter";
import { loadAllSpots } from "@/lib/data/spots";
import { isValidTag } from "@/lib/utils/tagConfig";
import type { SpotCategory } from "@/types/spot";

const VALID_CATEGORIES: SpotCategory[] = [
  "meditation",
  "waterside",
  "hidden_gem",
  "waterfall",
  "walking",
  "sports",
  "bbq",
];

export default function HomeClient() {
  const searchParams = useSearchParams();

  // 静的JSONから全スポットを取得
  const allSpots = useMemo(() => loadAllSpots(), []);

  const filteredSpots = useMemo(() => {
    const categoryParam = searchParams.get("category");
    const tagParam = searchParams.get("tag");
    const keyword = searchParams.get("keyword")?.toLowerCase().trim() ?? "";

    const cats = categoryParam
      ? categoryParam.split(",").filter((c) => VALID_CATEGORIES.includes(c as SpotCategory))
      : [];
    const tags = tagParam ? tagParam.split(",").filter(isValidTag) : [];

    return allSpots.filter((s) => {
      if (cats.length > 0 && !cats.includes(s.category)) return false;
      if (tags.length > 0) {
        const spotTags = s.tags ?? [];
        if (!tags.every((t) => spotTags.includes(t))) return false;
      }
      if (keyword) {
        const hay = `${s.name} ${s.description ?? ""}`.toLowerCase();
        if (!hay.includes(keyword)) return false;
      }
      return true;
    });
  }, [allSpots, searchParams]);

  return (
    // ヘッダー高さ約57pxを除いた全高マップ
    <div className="relative overflow-hidden" style={{ height: "calc(100vh - 57px)" }}>
      {/* 全高マップ */}
      <MapView spots={filteredSpots} />

      {/* フローティングフィルターパネル（左上） */}
      <div
        className="absolute top-3 left-3 z-10 w-80"
        style={{ maxHeight: "calc(100% - 5rem)", overflowY: "auto" }}
      >
        <SpotFilter />
      </div>

      {/* スポット件数バッジ（左下） */}
      <div className="absolute bottom-8 left-3 bg-white/90 backdrop-blur-sm px-3 py-1.5 rounded-full shadow text-xs text-gray-700 z-10 pointer-events-none">
        📍 {filteredSpots.length.toLocaleString()} 件表示中
      </div>
    </div>
  );
}
