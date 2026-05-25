"use client";

import { useEffect, useState } from "react";
import { useGeolocation } from "@/hooks/useGeolocation";
import SpotCard from "./SpotCard";
import { haversineDistance } from "@/lib/utils/geo";
import type { Spot } from "@/types/spot";

interface Props {
  spots: Spot[];
}

export default function NearbySpots({ spots }: Props) {
  const { position, loading, error, getCurrentPosition } = useGeolocation();
  const [nearby, setNearby] = useState<Spot[] | null>(null);

  useEffect(() => {
    if (!position) return;
    const ranked = spots
      .map((s) => ({
        ...s,
        distance_km: haversineDistance(position.lat, position.lng, s.latitude, s.longitude),
      }))
      .filter((s) => s.distance_km <= 20)
      .sort((a, b) => a.distance_km - b.distance_km)
      .slice(0, 10);
    setNearby(ranked);
  }, [position, spots]);

  return (
    <section className="bg-white border-t border-gray-200">
      <div className="max-w-6xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-gray-900">📍 現在地から近いスポット</h2>
          <button
            type="button"
            onClick={getCurrentPosition}
            disabled={loading}
            className="px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-md"
          >
            {loading ? "取得中..." : position ? "更新" : "近くを探す"}
          </button>
        </div>
        {error && <div className="text-sm text-red-600 mb-2">{error}</div>}
        {!position && !loading && !error && (
          <div className="text-sm text-gray-500">
            ボタンを押して位置情報を許可してください。現在地から20km以内のスポットを近い順に表示します。
          </div>
        )}
        {nearby && nearby.length === 0 && (
          <div className="text-sm text-gray-500">20km以内にスポットがありません</div>
        )}
        {nearby && nearby.length > 0 && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {nearby.map((s) => (
              <SpotCard key={s.id} spot={s} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
