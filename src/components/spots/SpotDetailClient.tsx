"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import CategoryBadge from "./CategoryBadge";
import { loadSpotById, deleteSpot, isUserCreatedSpot } from "@/lib/storage/local";
import { displayNickname, formatDate } from "@/lib/utils/formatters";
import { getTagIcon, getTagLabel } from "@/lib/utils/tagConfig";
import type { Spot } from "@/types/spot";

export default function SpotDetailClient({ id }: { id: string }) {
  const router = useRouter();
  const [spot, setSpot] = useState<Spot | null | undefined>(undefined);
  const [canDelete, setCanDelete] = useState(false);

  useEffect(() => {
    setSpot(loadSpotById(id));
    setCanDelete(isUserCreatedSpot(id));
  }, [id]);

  const onDelete = () => {
    if (!confirm("このスポットを削除しますか？")) return;
    if (deleteSpot(id)) {
      router.push("/");
      router.refresh();
    }
  };

  if (spot === undefined) {
    return <div className="p-8 text-center text-gray-500">読み込み中...</div>;
  }

  if (spot === null) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
        <div className="text-6xl mb-4">🗺️</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">スポットが見つかりません</h1>
        <p className="text-gray-600 mb-6">
          お探しのスポットは削除されたか、URLが間違っている可能性があります。
        </p>
        <Link
          href="/"
          className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-md font-medium"
        >
          マップに戻る
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
        <div className="flex items-center justify-between">
          <Link href="/" className="inline-block text-sm text-gray-600 hover:text-primary-600">
            ← マップに戻る
          </Link>
          {canDelete && (
            <button
              type="button"
              onClick={onDelete}
              className="text-sm text-red-600 hover:text-red-700"
            >
              削除
            </button>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <div className="mb-2">
            <CategoryBadge category={spot.category} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-3">{spot.name}</h1>
          {spot.description && (
            <p className="text-gray-700 whitespace-pre-wrap break-words mb-4">{spot.description}</p>
          )}

          {spot.tags && spot.tags.length > 0 && (
            <div className="mb-4">
              <div className="text-xs font-bold text-gray-500 mb-1.5">特徴</div>
              <div className="flex flex-wrap gap-1.5">
                {spot.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full"
                  >
                    {getTagIcon(tag)} {getTagLabel(tag)}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 text-sm border-t border-gray-100 pt-3">
            <div>
              <div className="text-xs text-gray-500">投稿者</div>
              <div className="font-medium">{displayNickname(spot.nickname)}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">投稿日</div>
              <div className="font-medium">{formatDate(spot.created_at)}</div>
            </div>
            <div className="col-span-2">
              <div className="text-xs text-gray-500">位置</div>
              <div className="font-mono text-xs">
                {spot.latitude.toFixed(6)}, {spot.longitude.toFixed(6)}
              </div>
              <a
                href={`https://www.openstreetmap.org/?mlat=${spot.latitude}&mlon=${spot.longitude}#map=16/${spot.latitude}/${spot.longitude}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:underline"
              >
                OpenStreetMapで開く →
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
