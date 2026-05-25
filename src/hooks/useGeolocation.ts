"use client";

import { useCallback, useState } from "react";

interface GeoState {
  lat: number;
  lng: number;
  accuracy: number;
}

interface UseGeolocationResult {
  position: GeoState | null;
  loading: boolean;
  error: string | null;
  getCurrentPosition: () => void;
}

export function useGeolocation(): UseGeolocationResult {
  const [position, setPosition] = useState<GeoState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getCurrentPosition = useCallback(() => {
    if (typeof window === "undefined" || !navigator.geolocation) {
      setError("お使いのブラウザは位置情報に対応していません");
      return;
    }
    setLoading(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPosition({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
        setLoading(false);
      },
      (err) => {
        setError(
          err.code === err.PERMISSION_DENIED
            ? "位置情報の利用が拒否されました"
            : "位置情報を取得できませんでした",
        );
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  }, []);

  return { position, loading, error, getCurrentPosition };
}
