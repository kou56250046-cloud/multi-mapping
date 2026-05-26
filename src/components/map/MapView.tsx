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

// GeoJSON FeatureCollection に変換
function spotsToGeoJSON(spots: Spot[]) {
  return {
    type: "FeatureCollection" as const,
    features: spots.map((s) => ({
      type: "Feature" as const,
      geometry: {
        type: "Point" as const,
        coordinates: [s.longitude, s.latitude] as [number, number],
      },
      properties: {
        id: s.id,
        name: s.name,
        description: s.description ?? "",
        source: s.source,
        source_url: s.source_url ?? "",
        color: getCategoryColor(s.category),
        categoryLabel: getCategoryLabel(s.category),
        categoryIcon: getCategoryIcon(s.category),
      },
    })),
  };
}

function buildPopupHtml(p: Record<string, string>): string {
  return `<div style="padding:10px;min-width:190px;font-family:sans-serif">
    <div style="font-weight:bold;font-size:14px;margin-bottom:4px;line-height:1.4">${escapeHtml(p.name)}</div>
    ${p.description ? `<div style="font-size:12px;color:#555;margin-bottom:6px;max-height:60px;overflow:hidden;line-height:1.5">${escapeHtml(p.description)}</div>` : ""}
    <div style="font-size:11px;color:#888;margin-bottom:8px">${escapeHtml(p.categoryIcon)} ${escapeHtml(p.categoryLabel)}</div>
    <a href="/spots/${escapeHtml(p.id)}" style="display:inline-block;background:#22c55e;color:#fff;padding:4px 12px;border-radius:6px;font-size:12px;text-decoration:none">詳細を見る →</a>
  </div>`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
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

  // マップ初期化
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
          // クラスター件数テキスト描画用グリフ
          glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
          sources: {
            osm: {
              type: "raster",
              tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
              tileSize: 256,
              attribution:
                '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
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

        // ---- GeoJSON ソース（クラスタリング有効） ----
        map.addSource("spots", {
          type: "geojson",
          data: spotsToGeoJSON(spots),
          cluster: true,
          clusterMaxZoom: 13,
          clusterRadius: 40,
        });

        // ① クラスター円（件数に応じて緑→黄→赤）
        map.addLayer({
          id: "clusters",
          type: "circle",
          source: "spots",
          filter: ["has", "point_count"],
          paint: {
            "circle-color": [
              "step",
              ["get", "point_count"],
              "#22c55e",
              50,
              "#f59e0b",
              200,
              "#ef4444",
            ],
            "circle-radius": [
              "step",
              ["get", "point_count"],
              22,
              50,
              30,
              200,
              40,
            ],
            "circle-stroke-width": 2,
            "circle-stroke-color": "#fff",
          },
        });

        // ② クラスター件数テキスト
        map.addLayer({
          id: "cluster-count",
          type: "symbol",
          source: "spots",
          filter: ["has", "point_count"],
          layout: {
            "text-field": "{point_count_abbreviated}",
            "text-font": ["Open Sans Bold"],
            "text-size": 13,
          },
          paint: { "text-color": "#ffffff" },
        });

        // ③ 個別スポット円（カテゴリ色）
        map.addLayer({
          id: "unclustered-point",
          type: "circle",
          source: "spots",
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-color": ["get", "color"],
            "circle-radius": 10,
            "circle-stroke-width": 2,
            "circle-stroke-color": "#fff",
          },
        });

        // ---- クリックハンドラー ----

        // クラスタークリック → ズームイン
        map.on("click", "clusters", (e) => {
          const features = map.queryRenderedFeatures(e.point, {
            layers: ["clusters"],
          });
          if (!features.length) return;
          const feat = features[0];
          const clusterId = feat.properties?.cluster_id as number;
          const src = map.getSource("spots") as unknown as {
            getClusterExpansionZoom: (
              id: number,
              cb: (err: unknown, zoom: number) => void,
            ) => void;
          };
          src.getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err) return;
            const coords = (feat.geometry as unknown as { coordinates: [number, number] })
              .coordinates;
            map.easeTo({ center: coords, zoom });
          });
        });

        // 個別スポットクリック → ポップアップ
        map.on("click", "unclustered-point", (e) => {
          if (!e.features?.length) return;
          const props = e.features[0].properties as Record<string, string>;
          new maplibre.Popup({ offset: 12, closeButton: true })
            .setLngLat(e.lngLat)
            .setHTML(buildPopupHtml(props))
            .addTo(map);
        });

        // カーソル変更
        for (const layer of ["clusters", "unclustered-point"]) {
          map.on("mouseenter", layer, () => {
            map.getCanvas().style.cursor = "pointer";
          });
          map.on("mouseleave", layer, () => {
            map.getCanvas().style.cursor = "";
          });
        }

        // ピッカーモード用クリックハンドラー
        if (onMapClick) {
          map.on("click", (ev) => {
            onMapClick(ev.lngLat.lat, ev.lngLat.lng);
          });
          map.getCanvas().style.cursor = "crosshair";
        }

        setLoaded(true);
      });
    })();

    return () => {
      cancelled = true;
      const m = mapRef.current as { remove?: () => void } | null;
      m?.remove?.();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialCenter, initialZoom, onMapClick]);

  // スポットデータ更新（props 変更時に GeoJSON を差し替え）
  useEffect(() => {
    if (!loaded || !mapRef.current) return;
    const map = mapRef.current as {
      getSource: (id: string) => { setData: (data: unknown) => void } | undefined;
    };
    map.getSource("spots")?.setData(spotsToGeoJSON(spots));
  }, [loaded, spots]);

  // ピッカーモード用マーカー
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
