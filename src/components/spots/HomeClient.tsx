"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import MapView from "@/components/map/MapView";
import SpotFilter from "@/components/spots/SpotFilter";
import NearbySpots from "@/components/spots/NearbySpots";
import { loadAllSpots } from "@/lib/storage/local";
import { isValidTag } from "@/lib/utils/tagConfig";
import type { Spot, SpotCategory } from "@/types/spot";

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
  const [allSpots, setAllSpots] = useState<Spot[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setAllSpots(loadAllSpots());
    setMounted(true);

    const onStorage = (e: StorageEvent) => {
      if (e.key === "multi-mapping:spots:v1") setAllSpots(loadAllSpots());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

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
    <>
      <SpotFilter />
      <div className="relative" style={{ height: "60vh", minHeight: "400px" }}>
        <MapView spots={filteredSpots} />
        <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur px-3 py-1.5 rounded-md shadow text-xs text-gray-700 z-10">
          {mounted ? `${filteredSpots.length} 件のスポット` : "読み込み中..."}
        </div>
      </div>
      <NearbySpots spots={allSpots} />
    </>
  );
}
