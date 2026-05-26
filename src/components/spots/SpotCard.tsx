import Link from "next/link";
import CategoryBadge from "./CategoryBadge";
import { formatDate } from "@/lib/utils/formatters";
import { formatDistance } from "@/lib/utils/geo";
import { getTagIcon, getTagLabel } from "@/lib/utils/tagConfig";
import type { Spot } from "@/types/spot";

const SOURCE_LABELS: Record<string, string> = {
  nap: "なっぷ",
  tokyo_park: "東京都公園協会",
  kanagawa_park: "神奈川県公園",
  mlit: "国土数値情報",
  manual: "編集部",
};

export default function SpotCard({ spot }: { spot: Spot }) {
  return (
    <Link
      href={`/spots/${spot.id}`}
      className="block bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md hover:border-primary-300 transition-all"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-bold text-gray-900 text-base line-clamp-1">{spot.name}</h3>
        {typeof spot.distance_km === "number" && (
          <span className="text-xs text-primary-600 font-medium whitespace-nowrap">
            {formatDistance(spot.distance_km)}
          </span>
        )}
      </div>
      <div className="mb-2">
        <CategoryBadge category={spot.category} />
      </div>
      {spot.description && (
        <p className="text-sm text-gray-600 line-clamp-2 mb-2">{spot.description}</p>
      )}
      {spot.tags && spot.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {spot.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="text-xs bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded"
            >
              {getTagIcon(tag)} {getTagLabel(tag)}
            </span>
          ))}
          {spot.tags.length > 4 && (
            <span className="text-xs text-gray-500">+{spot.tags.length - 4}</span>
          )}
        </div>
      )}
      <div className="text-xs text-gray-500 flex items-center justify-between">
        <span>{SOURCE_LABELS[spot.source] ?? spot.source}</span>
        <span>{formatDate(spot.created_at)}</span>
      </div>
    </Link>
  );
}
