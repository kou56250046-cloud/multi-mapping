"use client";

import { useEffect, useState } from "react";
import MapView from "@/components/map/MapView";
import { useGeolocation } from "@/hooks/useGeolocation";
import { isInTokyoKanagawaArea } from "@/lib/utils/geo";

interface Props {
  onChange: (lat: number, lng: number) => void;
  value: { lat: number; lng: number } | null;
}

export default function LocationPicker({ onChange, value }: Props) {
  const [outsideArea, setOutsideArea] = useState(false);
  const { position, loading, error, getCurrentPosition } = useGeolocation();

  const handleMapClick = (lat: number, lng: number) => {
    setOutsideArea(!isInTokyoKanagawaArea(lat, lng));
    onChange(lat, lng);
  };

  const handleUseGps = () => {
    getCurrentPosition();
  };

  useEffect(() => {
    if (position && !value) {
      onChange(position.lat, position.lng);
      setOutsideArea(!isInTokyoKanagawaArea(position.lat, position.lng));
    }
  }, [position, value, onChange]);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={handleUseGps}
          disabled={loading}
          className="px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-md"
        >
          {loading ? "取得中..." : "📍 現在地を使う"}
        </button>
        {value && (
          <span className="text-xs text-gray-600 font-mono">
            緯度: {value.lat.toFixed(6)} / 経度: {value.lng.toFixed(6)}
          </span>
        )}
      </div>
      {error && <div className="text-xs text-red-600">{error}</div>}
      {outsideArea && value && (
        <div className="text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 px-2 py-1 rounded">
          ⚠️ 東京・神奈川エリア外の位置です（投稿は可能です）
        </div>
      )}
      <div className="text-xs text-gray-600">
        地図をクリックして位置を選択してください
      </div>
      <div className="w-full h-[400px] rounded-md overflow-hidden border border-gray-300">
        <MapView
          spots={[]}
          onMapClick={handleMapClick}
          pickerMode
          selectedLatLng={value}
        />
      </div>
    </div>
  );
}
