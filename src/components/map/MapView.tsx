"use client";

import { useEffect, useRef, useState } from "react";
import type { Spot } from "@/types/spot";
import { getCategoryColor, getCategoryIcon, getCategoryLabel } from "@/lib/utils/categoryConfig";
import { TOKYO_CENTER } from "@/lib/utils/geo";

interface Props {
  spots: Spot[];
  onMapClick?: (lat: number, lng: number) => void;
  pickerMode?: boolean;
  selectedLatLng?: { lat: number; lng: number } | null;
  initialCenter?: [number, number];
  initialZoom?: number;
}

export default function MapView({
  spots,
  onMapClick,
  pickerMode = false,
  selectedLatLng = null,
  initialCenter = TOKYO_CENTER,
  initialZoom = 10,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);
  const pickerMarkerRef = useRef<unknown>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;
    let cancelled = false;

    (async () => {
      const maplibre = await import("maplibre-gl");
      if (cancelled || !containerRef.current) return;

      const map = new maplibre.Map({
        container: containerRef.current,
        style: {
          version: 8,
          sources: {
            osm: {
              type: "raster",
              tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
              tileSize: 256,
              attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
              maxzoom: 19,
            },
          },
          layers: [{ id: "osm", type: "raster", source: "osm" }],
        },
        center: initialCenter,
        zoom: initialZoom,
      });

      map.addControl(new maplibre.NavigationControl(), "top-right");
      map.addControl(
        new maplibre.GeolocateControl({
          positionOptions: { enableHighAccuracy: true },
          trackUserLocation: false,
          showAccuracyCircle: true,
        }),
        "top-right",
      );

      map.on("load", () => {
        if (cancelled) return;
        mapRef.current = map;
        setLoaded(true);

        if (onMapClick) {
          map.on("click", (e: { lngLat: { lat: number; lng: number } }) => {
            onMapClick(e.lngLat.lat, e.lngLat.lng);
          });
          map.getCanvas().style.cursor = "crosshair";
        }
      });
    })();

    return () => {
      cancelled = true;
      const m = mapRef.current as { remove?: () => void } | null;
      m?.remove?.();
      mapRef.current = null;
    };
  }, [initialCenter, initialZoom, onMapClick]);

  // スポットマーカー描画
  useEffect(() => {
    if (!loaded || !mapRef.current) return;
    const map = mapRef.current as {
      _spotMarkers?: Array<{ remove: () => void }>;
    } & Record<string, unknown>;

    // 既存マーカーをクリア
    if (map._spotMarkers) {
      map._spotMarkers.forEach((m) => m.remove());
    }
    const markers: Array<{ remove: () => void }> = [];

    (async () => {
      const maplibre = await import("maplibre-gl");
      for (const spot of spots) {
        const el = document.createElement("div");
        el.className = "spot-marker";
        el.style.cssText = `
          width: 36px; height: 36px;
          background: ${getCategoryColor(spot.category)};
          border: 3px solid white;
          border-radius: 50%;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          display: flex; align-items: center; justify-content: center;
          font-size: 18px;
          cursor: pointer;
        `;
        el.textContent = getCategoryIcon(spot.category);

        const popupHTML = `
          <div style="padding: 12px; min-width: 200px;">
            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px;">
              <span style="background: ${getCategoryColor(spot.category)}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">${getCategoryIcon(spot.category)} ${getCategoryLabel(spot.category)}</span>
            </div>
            <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">${escapeHtml(spot.name)}</div>
            ${spot.description ? `<div style="font-size: 12px; color: #555; margin-bottom: 6px; max-height: 60px; overflow: hidden;">${escapeHtml(spot.description)}</div>` : ""}
            <div style="font-size: 11px; color: #888; margin-bottom: 8px;">提供元: ${escapeHtml(spot.source)}</div>
            <a href="/spots/${spot.id}" style="display: inline-block; background: #22c55e; color: white; padding: 4px 12px; border-radius: 6px; font-size: 12px; text-decoration: none;">詳細を見る →</a>
          </div>
        `;

        const popup = new maplibre.Popup({ offset: 24, closeButton: true }).setHTML(popupHTML);

        const marker = new maplibre.Marker({ element: el })
          .setLngLat([spot.longitude, spot.latitude])
          .setPopup(popup)
          .addTo(mapRef.current as Parameters<typeof marker.addTo>[0]);

        markers.push(marker);
      }
      map._spotMarkers = markers;
    })();
  }, [loaded, spots]);

  // ピッカーモードでの選択地点表示
  useEffect(() => {
    if (!loaded || !mapRef.current || !pickerMode) return;
    (async () => {
      const maplibre = await import("maplibre-gl");
      const existing = pickerMarkerRef.current as { remove: () => void } | null;
      existing?.remove();

      if (selectedLatLng) {
        const el = document.createElement("div");
        el.style.cssText = `
          width: 40px; height: 40px;
          background: #ef4444;
          border: 4px solid white;
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        `;
        const marker = new maplibre.Marker({ element: el, anchor: "bottom" })
          .setLngLat([selectedLatLng.lng, selectedLatLng.lat])
          .addTo(mapRef.current as Parameters<typeof marker.addTo>[0]);
        pickerMarkerRef.current = marker;
      }
    })();
  }, [loaded, pickerMode, selectedLatLng]);

  return <div ref={containerRef} className="w-full h-full" />;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
